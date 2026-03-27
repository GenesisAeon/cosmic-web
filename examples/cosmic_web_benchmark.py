"""
cosmic_web_benchmark.py
=======================

Compares the GenesisAeon CosmicWebSimulator power spectrum against a
synthetic GADGET-4 / IllustrisTNG reference dataset.

Usage
-----
    python examples/cosmic_web_benchmark.py

The script expects ``data/gadget_power_spectrum.txt`` relative to the
repository root (generated automatically during the build or available
in the repository).
"""

import numpy as np
import matplotlib.pyplot as plt
from genesis_os import universums_sim  # CosmicWeb simulator

# Reproducible run
np.random.seed(42)

# ── Simulation ────────────────────────────────────────────────────────────────
print("Initialising CosmicWebSimulator …")
sim = universums_sim.CosmicWebSimulator(N=10000, box_size=100.0)
print(f"  {sim}")
print(f"  Running {500} leapfrog steps …")
sim.run(steps=500)
print("  Done.")

# ── Reference data ────────────────────────────────────────────────────────────
gadget_power = np.loadtxt("data/gadget_power_spectrum.txt")

# ── Power spectra ─────────────────────────────────────────────────────────────
t = np.linspace(0, 10, 500)           # k-axis in h/Mpc
power_genesis = sim.get_power_spectrum()  # shape (500,)

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 6))
ax.loglog(t, power_genesis, label="GenesisAeon CosmicWeb", color="purple", lw=2)
ax.loglog(t, gadget_power[:500], label="GADGET-4 / IllustrisTNG (ref)", color="teal", ls="--")
ax.set_title("CosmicWebSimulator vs. GADGET-4 / IllustrisTNG-Skalierung")
ax.set_xlabel("k  [h/Mpc]")
ax.set_ylabel("P(k)  [(Mpc/h)³]")
ax.legend()
ax.grid(True, which="both", alpha=0.4)
plt.tight_layout()
plt.savefig("examples/power_spectrum_benchmark.png", dpi=150)
plt.show()

# ── Resonanz-Metric ───────────────────────────────────────────────────────────
deviation = np.mean(np.abs(power_genesis - gadget_power[:500]))
print(f"✅ Resonanz-Metric (Power-Spectrum-Abweichung): {deviation:.4f}")
