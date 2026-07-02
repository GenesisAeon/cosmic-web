"""cosmic-web – entropy gates, cosmic moments and emergence visualization."""

__version__ = "1.0.1"

from .core import build_cosmic_web, emergence_metrics
from .universums_sim import CosmicWebSimulator

__all__ = [
    "CosmicWebSimulator",
    "build_cosmic_web",
    "emergence_metrics",
    "__version__",
]
