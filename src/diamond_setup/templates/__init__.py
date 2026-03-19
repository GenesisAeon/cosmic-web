"""Template registry — add a new module here to register a new template."""

from .genesis import TEMPLATE as GENESIS_TEMPLATE
from .minimal import TEMPLATE as MINIMAL_TEMPLATE

REGISTRY: dict[str, dict] = {
    "minimal": MINIMAL_TEMPLATE,
    "genesis": GENESIS_TEMPLATE,
}

__all__ = ["REGISTRY"]
