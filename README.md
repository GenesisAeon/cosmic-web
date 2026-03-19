# cosmic-web

**The cosmic web** – relational network of entropy gates, cosmic moments, mandala nodes and
emergence visualization for the GenesisAeon stack.

[![CI](https://github.com/GenesisAeon/cosmic-web/actions/workflows/ci.yml/badge.svg)](https://github.com/GenesisAeon/cosmic-web/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/cosmic-web)](https://pypi.org/project/cosmic-web/)

---

## Install

```bash
pip install cosmic-web
# or
uv tool install cosmic-web

# With full GenesisAeon stack bindings
pip install "cosmic-web[stack]"
```

## Quick start

```bash
# Render emergence metrics for a 50-node cosmic web
cweb render --nodes 50 --edges 100

# Simulate emergent propagation (5 steps, 30 nodes)
cweb simulate --nodes 30 --steps 5

# Launch interactive Plotly/Dash dashboard
cweb dashboard --port 8050
```

## Python API

```python
from cosmic_web import build_cosmic_web, emergence_metrics
from cosmic_web.core import simulate_emergence

G = build_cosmic_web(nodes=50, edges=100, seed=42)
metrics = emergence_metrics(G)
print(metrics.head())

history = simulate_emergence(G, steps=10)
```

## Architecture

```
cosmic-web/
├── src/cosmic_web/
│   ├── core.py                  # CosmicWebGraph + emergence simulation
│   ├── app.py                   # Plotly/Dash interactive dashboard
│   ├── cli.py                   # CLI: cweb render | simulate | dashboard
│   └── entropy_table_bridge.py  # Optional bridge to entropy-table [stack]
├── domains.yaml                 # Domain topology registry
└── tests/
    ├── test_core.py
    └── test_cli.py
```

## Stack bindings (`[stack]`)

| Layer | Binding |
|-------|---------|
| `mirror-machine` | Phase-transitions as nodes |
| `climate-dashboard` | UI integration |
| `sonification` | Audio from edges |
| `mandala-visualizer` | Fractal node rendering |
| `entropy-table` | Domain registry |
| `fieldtheory` | Unified field topology |

## CLI reference

| Command | Description |
|---------|-------------|
| `cweb render` | Print emergence metrics table |
| `cweb simulate` | Run emergence diffusion simulation |
| `cweb dashboard` | Launch interactive web dashboard |
| `cweb version` | Show version |

---

**DOI** (after Zenodo release): 10.5281/zenodo.XXXXXXX

Built with [NetworkX](https://networkx.org/) · [Plotly](https://plotly.com/) ·
[Dash](https://dash.plotly.com/) · [Typer](https://typer.tiangolo.com/) · [Rich](https://rich.readthedocs.io/)
