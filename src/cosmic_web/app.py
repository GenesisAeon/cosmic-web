"""Plotly/Dash interactive cosmic web dashboard."""

from __future__ import annotations

import networkx as nx
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html

from .core import build_cosmic_web, emergence_metrics


def _build_network_figure(G: nx.Graph) -> go.Figure:
    """Create a Plotly network figure from a cosmic web graph."""
    pos = nx.spring_layout(G, seed=42)

    edge_x: list[float | None] = []
    edge_y: list[float | None] = []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=0.5, color="#555"),
        hoverinfo="none",
        mode="lines",
    )

    node_x = [pos[n][0] for n in G.nodes()]
    node_y = [pos[n][1] for n in G.nodes()]
    emergence_vals = [G.nodes[n]["emergence"] for n in G.nodes()]
    node_text = [f"Node {n}<br>emergence={G.nodes[n]['emergence']:.3f}" for n in G.nodes()]

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        hoverinfo="text",
        text=node_text,
        marker=dict(
            size=8,
            color=emergence_vals,
            colorscale="Viridis",
            showscale=True,
            colorbar=dict(title="Emergence"),
        ),
    )

    return go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title="Cosmic Web – Emergence Network",
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            paper_bgcolor="#0a0a1a",
            plot_bgcolor="#0a0a1a",
            font=dict(color="#e0e0ff"),
        ),
    )


def create_cosmic_web_dashboard(nodes: int = 50, edges: int = 100) -> Dash:
    """Create and return the Dash application for the cosmic web dashboard.

    Args:
        nodes: Number of graph nodes.
        edges: Target number of graph edges.

    Returns:
        Configured :class:`dash.Dash` application (not yet running).
    """
    app = Dash(__name__, title="Cosmic Web")

    G = build_cosmic_web(nodes=nodes, edges=edges, seed=42)
    metrics = emergence_metrics(G)
    net_fig = _build_network_figure(G)

    bar_fig = px.bar(
        metrics,
        x="node",
        y="emergence",
        color="centrality",
        color_continuous_scale="Plasma",
        title="Node Emergence & Centrality",
        template="plotly_dark",
    )

    scatter_fig = px.scatter(
        metrics,
        x="degree",
        y="emergence",
        size="centrality",
        color="centrality",
        hover_data=["node"],
        title="Degree vs Emergence",
        template="plotly_dark",
    )

    app.layout = html.Div(
        style={"backgroundColor": "#0a0a1a", "color": "#e0e0ff", "fontFamily": "monospace"},
        children=[
            html.H1(
                "🌌 Cosmic Web – Emergence Network",
                style={"textAlign": "center", "padding": "20px"},
            ),
            html.Div(
                [
                    html.P(
                        f"Nodes: {G.number_of_nodes()} | Edges: {G.number_of_edges()} | "
                        f"Avg Emergence: {metrics['emergence'].mean():.3f}",
                        style={"textAlign": "center", "color": "#88aaff"},
                    )
                ]
            ),
            dcc.Graph(figure=net_fig, style={"height": "500px"}),
            html.Div(
                [
                    html.Div(
                        dcc.Graph(figure=bar_fig),
                        style={"width": "50%", "display": "inline-block"},
                    ),
                    html.Div(
                        dcc.Graph(figure=scatter_fig),
                        style={"width": "50%", "display": "inline-block"},
                    ),
                ]
            ),
        ],
    )

    return app
