"""CosmicWebGraph – network construction and emergence metrics."""

from __future__ import annotations

import networkx as nx
import numpy as np
import pandas as pd


def build_cosmic_web(
    nodes: int = 50, edges: int = 100, seed: int | None = None
) -> nx.Graph:
    """Build a cosmic web graph (nodes = gates/moments, edges = relations).

    Uses a scale-free topology (Barabási–Albert) to model the power-law
    degree distribution observed in large-scale cosmic structures.

    Args:
        nodes: Number of nodes (entropy gates / cosmic moments).
        edges: Minimum number of edges. Controls BA attachment parameter.
        seed: Random seed for reproducibility.

    Returns:
        Undirected NetworkX graph with ``emergence`` node attribute.
    """
    rng = np.random.default_rng(seed)
    # BA model parameter m: edges added per new node; must satisfy 1 <= m < n
    m = max(1, min(edges // nodes, nodes - 1))
    nx_seed = seed if seed is not None else int(rng.integers(0, 2**31))
    G = nx.barabasi_albert_graph(n=nodes, m=m, seed=nx_seed)

    for node in G.nodes:
        G.nodes[node]["emergence"] = float(rng.uniform(0.1, 1.0))
        G.nodes[node]["label"] = f"node-{node}"

    return G


def emergence_metrics(G: nx.Graph) -> pd.DataFrame:
    """Calculate cosmic emergence metrics for each node.

    Args:
        G: Cosmic web graph produced by :func:`build_cosmic_web`.

    Returns:
        DataFrame with columns: node, degree, centrality, emergence.
    """
    degrees = dict(G.degree())
    centralities = nx.betweenness_centrality(G)
    emergence = nx.get_node_attributes(G, "emergence")
    return pd.DataFrame(
        {
            "node": list(degrees.keys()),
            "degree": list(degrees.values()),
            "centrality": [centralities[n] for n in degrees],
            "emergence": [emergence[n] for n in degrees],
        }
    )


def simulate_emergence(
    G: nx.Graph, steps: int = 10, alpha: float = 0.1, seed: int | None = None
) -> list[dict]:
    """Simulate emergent propagation across the cosmic web.

    At each step, each node's emergence value is updated as a weighted
    average of its neighbours' values plus a small noise term.

    Args:
        G: Cosmic web graph.
        steps: Number of simulation steps.
        alpha: Diffusion coefficient (0 < alpha < 1).
        seed: Random seed for reproducibility.

    Returns:
        List of dicts mapping node → emergence value per step.
    """
    rng = np.random.default_rng(seed)
    # Precompute neighbour lists once — graph is static across steps
    neighbours = {n: list(G.neighbors(n)) for n in G.nodes}
    history: list[dict] = []
    current = {n: G.nodes[n]["emergence"] for n in G.nodes}

    for _ in range(steps):
        next_vals: dict[int, float] = {}
        for node in G.nodes:
            nbs = neighbours[node]
            if nbs:
                neighbour_mean = float(np.mean([current[nb] for nb in nbs]))
                noise = float(rng.normal(0, 0.01))
                val = (1 - alpha) * current[node] + alpha * neighbour_mean + noise
                next_vals[node] = float(np.clip(val, 0.0, 1.0))
            else:
                next_vals[node] = current[node]
        current = next_vals
        history.append(dict(current))

    return history
