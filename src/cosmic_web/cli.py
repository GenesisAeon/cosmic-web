"""Cosmic-Web CLI – relational emergence network."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .core import build_cosmic_web, emergence_metrics, simulate_emergence

app = typer.Typer(
    name="cweb",
    help="Cosmic-Web CLI – explore relational emergence networks.",
    add_completion=True,
    rich_markup_mode="rich",
)
console = Console()


@app.command()
def render(
    nodes: int = typer.Option(50, help="Number of nodes (entropy gates / cosmic moments)"),
    edges: int = typer.Option(100, help="Target number of edges (relations)"),
    seed: int = typer.Option(42, help="Random seed for reproducibility"),
) -> None:
    """Render cosmic web graph metrics to the terminal."""
    console.print(
        Panel(
            f"[bold cyan]Building cosmic web[/bold cyan] — "
            f"nodes=[magenta]{nodes}[/magenta] edges≈[magenta]{edges}[/magenta]",
            expand=False,
        )
    )
    G = build_cosmic_web(nodes=nodes, edges=edges, seed=seed)
    metrics = emergence_metrics(G)

    table = Table(title="Cosmic Web – Emergence Metrics", show_lines=True)
    table.add_column("Node", style="cyan", justify="right")
    table.add_column("Degree", justify="right")
    table.add_column("Centrality", justify="right")
    table.add_column("Emergence", justify="right")

    for _, row in metrics.head(20).iterrows():
        table.add_row(
            str(int(row["node"])),
            str(int(row["degree"])),
            f"{row['centrality']:.4f}",
            f"{row['emergence']:.4f}",
        )

    console.print(table)
    console.print(
        f"\n[bold green]Graph summary:[/bold green] "
        f"{G.number_of_nodes()} nodes, {G.number_of_edges()} edges | "
        f"avg emergence = [yellow]{metrics['emergence'].mean():.3f}[/yellow]"
    )


@app.command()
def simulate(
    nodes: int = typer.Option(30, help="Number of nodes"),
    steps: int = typer.Option(5, help="Simulation steps"),
    seed: int = typer.Option(42, help="Random seed"),
) -> None:
    """Simulate emergent propagation across the cosmic web."""
    G = build_cosmic_web(nodes=nodes, seed=seed)
    history = simulate_emergence(G, steps=steps)
    console.print(f"[bold cyan]Simulated {steps} steps on {nodes} nodes[/bold cyan]")
    for i, step in enumerate(history):
        avg = sum(step.values()) / len(step)
        console.print(f"  step {i + 1:>2}: avg emergence = [yellow]{avg:.4f}[/yellow]")


@app.command()
def dashboard(
    nodes: int = typer.Option(50, help="Number of nodes"),
    edges: int = typer.Option(100, help="Target number of edges"),
    port: int = typer.Option(8050, help="Port for the Dash server"),
    debug: bool = typer.Option(False, help="Run in debug mode"),
) -> None:
    """Launch interactive cosmic web dashboard in the browser."""
    from .app import create_cosmic_web_dashboard

    console.print(
        Panel(
            f"[bold cyan]Cosmic Web Dashboard[/bold cyan] starting on "
            f"[link=http://127.0.0.1:{port}]http://127.0.0.1:{port}[/link]",
            expand=False,
        )
    )
    dash_app = create_cosmic_web_dashboard(nodes=nodes, edges=edges)
    dash_app.run(debug=debug, port=port)


@app.command()
def version() -> None:
    """Show cosmic-web version."""
    console.print(f"cosmic-web [bold]{__version__}[/bold]")


if __name__ == "__main__":
    app()
