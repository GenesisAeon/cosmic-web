"""Tests for genesis_os.universums_sim.CosmicWebSimulator."""

import numpy as np
import pytest

from genesis_os.universums_sim import CosmicWebSimulator


@pytest.fixture(scope="module")
def sim_small():
    """Tiny simulator fixture: 8 particles, 10 steps (fast)."""
    np.random.seed(42)
    sim = CosmicWebSimulator(N=8, box_size=50.0, n_mesh=16)
    sim.run(steps=10)
    return sim


def test_particle_count_adjusted_to_cube():
    """N is rounded to the nearest perfect cube."""
    sim = CosmicWebSimulator(N=10000, box_size=100.0)
    # cbrt(10000) ≈ 21.54 → n1d=22 → N=22³=10648 OR n1d=21 → 9261
    n1d = round(10000 ** (1 / 3))
    assert sim.N == n1d ** 3


def test_positions_within_box(sim_small):
    assert sim_small.pos.shape == (sim_small.N, 3)
    assert np.all(sim_small.pos >= 0.0)
    assert np.all(sim_small.pos < sim_small.box_size)


def test_velocities_shape(sim_small):
    assert sim_small.vel.shape == (sim_small.N, 3)


def test_scale_factor_after_run():
    np.random.seed(0)
    sim = CosmicWebSimulator(N=8, box_size=50.0, n_mesh=8)
    sim.run(steps=5, a_end=1.0)
    assert abs(sim.a - 1.0) < 1e-10


def test_repr_contains_key_info():
    sim = CosmicWebSimulator(N=8, box_size=50.0, n_mesh=8)
    r = repr(sim)
    assert "CosmicWebSimulator" in r
    assert "50.0" in r


def test_get_power_spectrum_shape(sim_small):
    pk = sim_small.get_power_spectrum()
    assert pk.shape == (500,)


def test_get_power_spectrum_custom_bins(sim_small):
    pk = sim_small.get_power_spectrum(n_bins=100, k_min=0.1, k_max=5.0)
    assert pk.shape == (100,)


def test_get_power_spectrum_non_negative(sim_small):
    pk = sim_small.get_power_spectrum()
    assert np.all(pk >= 0.0)


def test_density_field_shape(sim_small):
    delta = sim_small.get_density_field()
    nm = sim_small.n_mesh
    assert delta.shape == (nm, nm, nm)


def test_density_field_zero_mean(sim_small):
    delta = sim_small.get_density_field()
    # Mean of δ = ρ/ρ̄ − 1 should be ≈ 0
    assert abs(delta.mean()) < 0.1


def test_transfer_function_unity_at_zero():
    """T(k→0) → 1 (Harrison–Zel'dovich plateau)."""
    sim = CosmicWebSimulator(N=8, box_size=50.0)
    T = sim._transfer_function(np.array([1e-6]))
    assert abs(T[0] - 1.0) < 0.01


def test_transfer_function_decreasing():
    """T(k) should decrease with k (suppression at small scales)."""
    sim = CosmicWebSimulator(N=8, box_size=50.0)
    k = np.array([0.001, 0.01, 0.1, 1.0, 10.0])
    T = sim._transfer_function(k)
    assert np.all(np.diff(T) <= 0)


def test_hubble_at_a1():
    """H(a=1) = H0 √(Ω_m + Ω_Λ) ≈ H0 for flat universe."""
    sim = CosmicWebSimulator(N=8, box_size=50.0)
    H1 = sim._hubble(1.0)
    H_expected = sim.H0 * (sim.omega_m + sim.omega_lambda) ** 0.5
    assert abs(H1 - H_expected) / H_expected < 1e-6


def test_cic_deposit_total_mass(sim_small):
    """CIC deposit should conserve total particle count."""
    density = sim_small._cic_deposit()
    assert abs(density.sum() - sim_small.N) < 1e-6 * sim_small.N
