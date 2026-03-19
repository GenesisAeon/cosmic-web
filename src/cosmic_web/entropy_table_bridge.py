"""Bridge between cosmic-web and the entropy-table stack layer.

The ``entropy-table`` package is an optional [stack] dependency.
Import errors are handled gracefully so the rest of cosmic-web works
without it installed.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import networkx as nx


class CosmicWebBridge:
    """Connect cosmic-web graph data to the entropy-table domain registry.

    Requires the ``entropy-table`` package (install with
    ``pip install cosmic-web[stack]``).

    Example::

        bridge = CosmicWebBridge()
        bridge.add_node("entropy-gate-1", 0.87)
        bridge.export("domains.yaml")
    """

    def __init__(self, domain: str = "cosmic-web") -> None:
        try:
            from entropy_table import EntropyTable  # type: ignore[import-not-found]

            self.table = EntropyTable(domain=domain)
        except ImportError as exc:
            raise ImportError(
                "entropy-table is required for CosmicWebBridge. "
                "Install it with: pip install cosmic-web[stack]"
            ) from exc

    def add_node(self, key: str, value: float) -> None:
        """Register a cosmic node relation in the entropy table.

        Args:
            key: Node identifier (e.g. ``"entropy-gate-1"``).
            value: Emergence value (0.0–1.0).
        """
        self.table.add_relation(key, value)

    def add_graph(self, G: nx.Graph) -> None:  # type: ignore[name-defined]
        """Bulk-register all nodes from a cosmic web graph.

        Args:
            G: Graph produced by :func:`cosmic_web.core.build_cosmic_web`.
        """
        for node in G.nodes:
            self.add_node(str(node), float(G.nodes[node].get("emergence", 0.0)))

    def export(self, filepath: Path | str = "domains.yaml") -> Path:
        """Export the entropy table to a YAML file.

        Args:
            filepath: Destination path (default: ``domains.yaml``).

        Returns:
            Resolved :class:`pathlib.Path` of the written file.
        """
        self.table.export(filepath)
        return Path(filepath).resolve()
