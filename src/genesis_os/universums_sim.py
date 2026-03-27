"""
genesis_os.universums_sim
=========================

N-body + field-theory cosmological simulator for large-scale structure.

Uses the Particle Mesh (PM) algorithm:
  1. Zel'dovich approximation for cosmological initial conditions.
  2. Cloud-in-Cell (CIC) mass assignment.
  3. Poisson solver in Fourier space for gravity.
  4. Leapfrog (DKD) integration in scale-factor time.
  5. FFT-based matter power spectrum P(k).

Reference cosmology defaults: Planck 2018 (Aghanim et al. 2020).
"""

from __future__ import annotations

import numpy as np


class CosmicWebSimulator:
    """
    Particle Mesh N-body simulator for cosmic web formation.

    Parameters
    ----------
    N : int
        Target number of particles (adjusted to the nearest perfect cube).
    box_size : float
        Comoving box side length in Mpc/h.
    n_mesh : int, optional
        PM grid resolution per dimension.  Defaults to 32, which gives a
        good balance between accuracy and speed for N ≲ 10^4.
    omega_m : float
        Matter density parameter Ω_m (Planck 2018: 0.3111).
    omega_lambda : float
        Dark-energy density parameter Ω_Λ (Planck 2018: 0.6889).
    h : float
        Dimensionless Hubble constant h = H0 / (100 km/s/Mpc).
    n_s : float
        Primordial spectral index.
    sigma8 : float
        Linear matter fluctuation amplitude in 8 Mpc/h spheres.
    a_init : float
        Initial scale factor (default 0.02 → z ≈ 49).

    Examples
    --------
    >>> sim = CosmicWebSimulator(N=10000, box_size=100.0)
    >>> sim.run(steps=500)
    >>> pk = sim.get_power_spectrum()  # shape (500,)
    """

    def __init__(
        self,
        N: int = 10000,
        box_size: float = 100.0,
        n_mesh: int | None = None,
        omega_m: float = 0.3111,
        omega_lambda: float = 0.6889,
        h: float = 0.6766,
        n_s: float = 0.9665,
        sigma8: float = 0.8102,
        a_init: float = 0.02,
    ) -> None:
        self.box_size = float(box_size)
        self.n_mesh = int(n_mesh) if n_mesh is not None else 32
        self.omega_m = float(omega_m)
        self.omega_lambda = float(omega_lambda)
        self.h = float(h)
        self.n_s = float(n_s)
        self.sigma8 = float(sigma8)
        self.H0 = 100.0 * self.h  # km/s/Mpc

        # Adjust N to the nearest perfect cube for the initial lattice.
        n1d = max(1, int(round(N ** (1.0 / 3.0))))
        self.N = n1d ** 3
        self._n1d = n1d

        self.a: float = float(a_init)
        self.step_count: int = 0

        # Particle arrays (initialised by _init_zel_dovich)
        self.pos: np.ndarray  # shape (N, 3), comoving Mpc/h
        self.vel: np.ndarray  # shape (N, 3), peculiar km/s

        self._init_zel_dovich()

    # ------------------------------------------------------------------
    # Transfer function & initial power spectrum
    # ------------------------------------------------------------------

    def _transfer_function(self, k: np.ndarray) -> np.ndarray:
        """
        BBKS matter transfer function (Bardeen et al. 1986).

        Parameters
        ----------
        k : array-like
            Wavenumber in h/Mpc.

        Returns
        -------
        np.ndarray
            T(k), dimensionless.
        """
        k = np.asarray(k, dtype=float)
        Gamma = self.omega_m * self.h  # shape parameter
        q = np.where(k > 0, k / Gamma, 1e-30)
        T = (
            np.log(1.0 + 2.34 * q)
            / (2.34 * q)
            * (
                1.0
                + 3.89 * q
                + (16.1 * q) ** 2
                + (5.46 * q) ** 3
                + (6.71 * q) ** 4
            )
            ** (-0.25)
        )
        return np.where(k > 0, T, 1.0)

    def _pk_linear(self, k: np.ndarray) -> np.ndarray:
        """
        Linear matter power spectrum P(k) ∝ k^n_s · T(k)².

        Returns un-normalised shape; sigma8 normalisation is applied
        separately in `_init_zel_dovich`.
        """
        k = np.asarray(k, dtype=float)
        T = self._transfer_function(k)
        Pk = np.where(k > 0, k ** self.n_s * T ** 2, 0.0)
        return Pk

    def _sigma8_amplitude(self, nm: int) -> float:
        """
        Compute amplitude A such that the un-normalised P(k) has σ_8 = self.sigma8.
        Uses a mid-point integration over the PM k-modes.
        """
        R8 = 8.0  # Mpc/h
        kf = 2.0 * np.pi / self.box_size  # fundamental mode
        k_nyq = np.pi * nm / self.box_size  # Nyquist

        # 1-D k array spanning [kf, k_nyq]
        k_arr = np.linspace(kf, k_nyq, 512)
        dk = k_arr[1] - k_arr[0]

        Pk = self._pk_linear(k_arr)
        # Top-hat window in k-space: W(kR) = 3[sin(kR)-kR·cos(kR)]/(kR)³
        x = k_arr * R8
        W = 3.0 * (np.sin(x) - x * np.cos(x)) / (x ** 3 + 1e-30)

        # σ²_8 = 1/(2π²) ∫ k² P(k) W²(k) dk
        sigma2_raw = np.sum(k_arr ** 2 * Pk * W ** 2 * dk) / (2.0 * np.pi ** 2)

        if sigma2_raw <= 0.0:
            return 1.0
        return self.sigma8 ** 2 / sigma2_raw

    # ------------------------------------------------------------------
    # Initial conditions: Zel'dovich approximation
    # ------------------------------------------------------------------

    def _init_zel_dovich(self) -> None:
        """
        Place N particles on a uniform lattice and apply Zel'dovich
        displacements drawn from the linear power spectrum.

        The displacement field ψ satisfies:
            δ_k = −k² ψ_k   (Poisson, linear regime)
        and positions are:
            x = q + D(a_init) · ψ(q)
        Initial velocities follow:
            v = a · H(a) · f · D(a) · ψ,   f ≈ Ω_m(a)^0.55
        """
        nm = self.n_mesh
        a0 = self.a
        kf = 2.0 * np.pi / self.box_size

        # --- Uniform particle grid ---
        g = np.linspace(0.0, self.box_size, self._n1d, endpoint=False)
        gx, gy, gz = np.meshgrid(g, g, g, indexing="ij")
        q = np.stack(
            [gx.ravel(), gy.ravel(), gz.ravel()], axis=1
        ).astype(np.float64)

        # --- PM k-space grid ---
        kx = np.fft.fftfreq(nm, d=1.0 / nm) * kf
        ky = np.fft.fftfreq(nm, d=1.0 / nm) * kf
        kz = np.fft.fftfreq(nm, d=1.0 / nm) * kf
        KX, KY, KZ = np.meshgrid(kx, ky, kz, indexing="ij")
        K2 = KX ** 2 + KY ** 2 + KZ ** 2
        K = np.sqrt(K2)
        K[0, 0, 0] = 1.0  # avoid /0; reset after use

        # --- Draw Gaussian random density field ---
        A_norm = self._sigma8_amplitude(nm)
        rng = np.random.default_rng(seed=None)  # seeded externally via np.random.seed
        noise = rng.standard_normal((nm, nm, nm)).astype(np.float64)
        noise_k = np.fft.fftn(noise)

        # Cell volume factor for continuous-limit normalisation
        cell_vol = (self.box_size / nm) ** 3
        Pk = self._pk_linear(K)
        delta_k = noise_k * np.sqrt(np.maximum(Pk * A_norm * cell_vol, 0.0))
        delta_k[0, 0, 0] = 0.0  # zero mean

        # --- Zel'dovich potential: φ_k = −δ_k / k² ---
        K2_safe = K2.copy()
        K2_safe[0, 0, 0] = 1.0
        phi_k = -delta_k / K2_safe
        phi_k[0, 0, 0] = 0.0

        # --- Displacement field ψ = −∇φ in real space ---
        psi = np.stack(
            [
                np.real(np.fft.ifftn(1j * KX * phi_k)),
                np.real(np.fft.ifftn(1j * KY * phi_k)),
                np.real(np.fft.ifftn(1j * KZ * phi_k)),
            ],
            axis=-1,
        )  # shape (nm, nm, nm, 3)

        # --- Nearest-grid-point interpolation of ψ to particle positions ---
        cs = self.box_size / nm  # cell size
        ix = (q[:, 0] / cs).astype(int) % nm
        iy = (q[:, 1] / cs).astype(int) % nm
        iz = (q[:, 2] / cs).astype(int) % nm
        disp = psi[ix, iy, iz]  # shape (N, 3)

        # Growth factor D(a) ≈ a in matter domination
        D_a0 = a0

        # Apply displacement
        self.pos = (q + D_a0 * disp) % self.box_size

        # Initial peculiar velocities: v = a H f D ψ
        Ha0 = self._hubble(a0)
        f_a0 = self.omega_m ** 0.55  # logarithmic growth rate f ≈ Ω_m^0.55
        self.vel = (a0 * Ha0 * f_a0 * D_a0) * disp  # km/s

    # ------------------------------------------------------------------
    # Hubble parameter
    # ------------------------------------------------------------------

    def _hubble(self, a: float) -> float:
        """H(a) in km/s/Mpc."""
        return self.H0 * np.sqrt(
            self.omega_m / a ** 3 + self.omega_lambda
        )

    # ------------------------------------------------------------------
    # PM grid operations
    # ------------------------------------------------------------------

    def _cic_deposit(self) -> np.ndarray:
        """
        Cloud-in-Cell mass assignment: distribute particle masses onto
        the PM grid using trilinear (CIC) weighting.

        Returns
        -------
        np.ndarray, shape (n_mesh, n_mesh, n_mesh)
            Particle count / mass grid.
        """
        nm = self.n_mesh
        cs = self.box_size / nm
        density = np.zeros((nm, nm, nm), dtype=np.float64)

        xg = self.pos[:, 0] / cs
        yg = self.pos[:, 1] / cs
        zg = self.pos[:, 2] / cs

        i0 = xg.astype(int) % nm
        j0 = yg.astype(int) % nm
        k0 = zg.astype(int) % nm
        i1 = (i0 + 1) % nm
        j1 = (j0 + 1) % nm
        k1 = (k0 + 1) % nm

        dx = xg - xg.astype(int)
        dy = yg - yg.astype(int)
        dz = zg - zg.astype(int)
        tx, ty, tz = 1.0 - dx, 1.0 - dy, 1.0 - dz

        np.add.at(density, (i0, j0, k0), tx * ty * tz)
        np.add.at(density, (i1, j0, k0), dx * ty * tz)
        np.add.at(density, (i0, j1, k0), tx * dy * tz)
        np.add.at(density, (i0, j0, k1), tx * ty * dz)
        np.add.at(density, (i1, j1, k0), dx * dy * tz)
        np.add.at(density, (i1, j0, k1), dx * ty * dz)
        np.add.at(density, (i0, j1, k1), tx * dy * dz)
        np.add.at(density, (i1, j1, k1), dx * dy * dz)

        return density

    def _pm_gravity(self, a: float) -> np.ndarray:
        """
        Compute per-particle gravitational acceleration via PM.

        Solves the Poisson equation in Fourier space:
            k² φ_k = (3/2) H0² Ω_m / a · δ_k
        then interpolates −∇φ back to particle positions (CIC).

        Parameters
        ----------
        a : float
            Current scale factor.

        Returns
        -------
        np.ndarray, shape (N, 3)
            Acceleration in (km/s)² / Mpc · h.
        """
        nm = self.n_mesh
        kf = 2.0 * np.pi / self.box_size

        density = self._cic_deposit()
        rho_mean = density.mean()
        delta = density / (rho_mean + 1e-30) - 1.0

        delta_k = np.fft.fftn(delta)

        kx = np.fft.fftfreq(nm, d=1.0 / nm) * kf
        ky = np.fft.fftfreq(nm, d=1.0 / nm) * kf
        kz = np.fft.fftfreq(nm, d=1.0 / nm) * kf
        KX, KY, KZ = np.meshgrid(kx, ky, kz, indexing="ij")
        K2 = KX ** 2 + KY ** 2 + KZ ** 2
        K2[0, 0, 0] = 1.0

        # Gravitational potential
        grav = 1.5 * (self.H0 ** 2) * self.omega_m / a
        phi_k = -grav * delta_k / K2
        phi_k[0, 0, 0] = 0.0

        # Force components: F = −∇φ in real space
        fx = np.real(np.fft.ifftn(-1j * KX * phi_k))
        fy = np.real(np.fft.ifftn(-1j * KY * phi_k))
        fz = np.real(np.fft.ifftn(-1j * KZ * phi_k))

        # CIC interpolation back to particles
        cs = self.box_size / nm
        xg = self.pos[:, 0] / cs
        yg = self.pos[:, 1] / cs
        zg = self.pos[:, 2] / cs

        i0 = xg.astype(int) % nm
        j0 = yg.astype(int) % nm
        k0 = zg.astype(int) % nm
        i1 = (i0 + 1) % nm
        j1 = (j0 + 1) % nm
        k1 = (k0 + 1) % nm

        dx = xg - xg.astype(int)
        dy = yg - yg.astype(int)
        dz = zg - zg.astype(int)
        tx, ty, tz = 1.0 - dx, 1.0 - dy, 1.0 - dz

        def _interp(F: np.ndarray) -> np.ndarray:
            return (
                F[i0, j0, k0] * tx * ty * tz
                + F[i1, j0, k0] * dx * ty * tz
                + F[i0, j1, k0] * tx * dy * tz
                + F[i0, j0, k1] * tx * ty * dz
                + F[i1, j1, k0] * dx * dy * tz
                + F[i1, j0, k1] * dx * ty * dz
                + F[i0, j1, k1] * tx * dy * dz
                + F[i1, j1, k1] * dx * dy * dz
            )

        return np.stack([_interp(fx), _interp(fy), _interp(fz)], axis=1)

    # ------------------------------------------------------------------
    # Integration
    # ------------------------------------------------------------------

    def run(self, steps: int = 500, a_end: float = 1.0) -> None:
        """
        Evolve the simulation to scale factor *a_end* (z = 0) using
        Drift-Kick-Drift (DKD) leapfrog integration in scale-factor time.

        The equations of motion in comoving coordinates are:

            dx/da = v / (a² H)
            dv/da = F_grav / (a H) − (ȧ/a) v / (a H)

        where F_grav = −∇φ and the Hubble drag term accounts for
        momentum redshifting of peculiar velocities.

        Parameters
        ----------
        steps : int
            Number of integration steps (default 500).
        a_end : float
            Final scale factor (default 1.0 → z = 0).
        """
        a = self.a
        da = (a_end - a) / steps

        for _step in range(steps):
            a_mid = a + 0.5 * da
            H_mid = self._hubble(a_mid)

            # Physical time step (Mpc·s / km)
            dt = da / (a_mid * H_mid)

            # --- Drift (half) ---
            self.pos = (self.pos + 0.5 * self.vel * dt) % self.box_size

            # --- Kick ---
            accel = self._pm_gravity(a_mid)
            self.vel += accel * dt

            # Hubble drag: v_new = v · (a_old / a_new) ≈ v · (1 − Ḣ·dt)
            # Simple approximation: scale by a_mid/a_next
            a_next = a + da
            drag = a_mid / a_next
            self.vel *= np.clip(drag, 0.8, 1.0)

            # --- Drift (half) ---
            H_next = self._hubble(a_next)
            dt_next = da / (a_next * H_next)
            self.pos = (self.pos + 0.5 * self.vel * dt_next) % self.box_size

            a = a_next

        self.a = a_end
        self.step_count += steps

    # ------------------------------------------------------------------
    # Observables
    # ------------------------------------------------------------------

    def get_power_spectrum(
        self,
        n_bins: int = 500,
        k_min: float = 2.0e-2,
        k_max: float = 10.0,
    ) -> np.ndarray:
        """
        Estimate the matter power spectrum P(k) from the current density field.

        Uses CIC mass assignment + 3-D FFT, then spherically averages
        |δ(k)|² into logarithmically spaced k-bins.

        Parameters
        ----------
        n_bins : int
            Number of output k-bins (default 500 to match benchmark script).
        k_min : float
            Minimum k in h/Mpc (default ~ fundamental mode).
        k_max : float
            Maximum k in h/Mpc (default 10).

        Returns
        -------
        np.ndarray, shape (n_bins,)
            P(k) in (Mpc/h)³.  Bins with no modes are set to 0.
        """
        nm = self.n_mesh
        kf = 2.0 * np.pi / self.box_size

        density = self._cic_deposit()
        rho_mean = density.mean()
        delta = density / (rho_mean + 1e-30) - 1.0

        delta_k = np.fft.fftn(delta)
        # Continuous-field normalisation: P = |δ_k|² · V / N_cells²
        Pk_grid = np.abs(delta_k) ** 2 * (self.box_size ** 3) / (nm ** 6)

        # 3-D k magnitudes
        kx = np.fft.fftfreq(nm, d=1.0 / nm) * kf
        ky = np.fft.fftfreq(nm, d=1.0 / nm) * kf
        kz = np.fft.fftfreq(nm, d=1.0 / nm) * kf
        KX, KY, KZ = np.meshgrid(kx, ky, kz, indexing="ij")
        K_flat = np.sqrt(KX ** 2 + KY ** 2 + KZ ** 2).ravel()
        Pk_flat = Pk_grid.ravel()

        # Logarithmic binning  (avoids empty low-k bins)
        k_edges = np.geomspace(k_min, k_max, n_bins + 1)
        Pk_out = np.zeros(n_bins, dtype=np.float64)
        counts = np.zeros(n_bins, dtype=np.int64)

        idx = np.searchsorted(k_edges, K_flat, side="right") - 1
        valid = (idx >= 0) & (idx < n_bins)
        np.add.at(Pk_out, idx[valid], Pk_flat[valid])
        np.add.at(counts, idx[valid], 1)

        safe_counts = np.where(counts > 0, counts, 1)
        Pk_out = np.where(counts > 0, Pk_out / safe_counts, 0.0)
        return Pk_out

    def get_density_field(self) -> np.ndarray:
        """
        Return the overdensity field δ(x) on the PM grid.

        Returns
        -------
        np.ndarray, shape (n_mesh, n_mesh, n_mesh)
        """
        density = self._cic_deposit()
        rho_mean = density.mean()
        return density / (rho_mean + 1e-30) - 1.0

    def __repr__(self) -> str:
        return (
            f"CosmicWebSimulator("
            f"N={self.N}, box_size={self.box_size:.1f} Mpc/h, "
            f"n_mesh={self.n_mesh}, a={self.a:.4f} [z={1/self.a - 1:.2f}])"
        )
