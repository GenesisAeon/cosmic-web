"""Tests for cosmic_web.core."""

import networkx as nx
import pytest

from cosmic_web.core import build_cosmic_web, emergence_metrics, simulate_emergence


def test_build_cosmic_web_node_count():
    G = build_cosmic_web(nodes=20, seed=0)
    assert len(G.nodes) == 20


def test_build_cosmic_web_is_undirected():
    G = build_cosmic_web(nodes=10, seed=0)
    assert isinstance(G, nx.Graph)
    assert not isinstance(G, nx.DiGraph)


def test_build_cosmic_web_emergence_attribute():
    G = build_cosmic_web(nodes=10, seed=0)
    for node in G.nodes:
        assert "emergence" in G.nodes[node]
        val = G.nodes[node]["emergence"]
        assert 0.0 <= val <= 1.0


def test_build_cosmic_web_label_attribute():
    G = build_cosmic_web(nodes=5, seed=0)
    for node in G.nodes:
        assert "label" in G.nodes[node]
        assert G.nodes[node]["label"].startswith("node-")


def test_build_cosmic_web_reproducible():
    G1 = build_cosmic_web(nodes=15, seed=7)
    G2 = build_cosmic_web(nodes=15, seed=7)
    assert G1.number_of_nodes() == G2.number_of_nodes()
    assert G1.number_of_edges() == G2.number_of_edges()


def test_emergence_metrics_shape():
    G = build_cosmic_web(nodes=20, seed=0)
    metrics = emergence_metrics(G)
    assert len(metrics) == 20
    assert set(metrics.columns) == {"node", "degree", "centrality", "emergence"}


def test_emergence_metrics_values_in_range():
    G = build_cosmic_web(nodes=15, seed=1)
    metrics = emergence_metrics(G)
    assert (metrics["emergence"] >= 0.0).all()
    assert (metrics["emergence"] <= 1.0).all()
    assert (metrics["degree"] >= 0).all()
    assert (metrics["centrality"] >= 0.0).all()


def test_simulate_emergence_step_count():
    G = build_cosmic_web(nodes=10, seed=0)
    history = simulate_emergence(G, steps=5)
    assert len(history) == 5


def test_simulate_emergence_node_values_in_range():
    G = build_cosmic_web(nodes=10, seed=0)
    history = simulate_emergence(G, steps=3)
    for step in history:
        for val in step.values():
            assert 0.0 <= val <= 1.0


def test_simulate_emergence_all_nodes_present():
    G = build_cosmic_web(nodes=10, seed=0)
    history = simulate_emergence(G, steps=2)
    for step in history:
        assert set(step.keys()) == set(G.nodes)
