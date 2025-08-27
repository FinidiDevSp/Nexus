"""Plugin system for the Nexus application."""

from importlib import import_module
import logging
import pkgutil
from typing import Any, Dict, Iterable, Tuple

__all__ = [
    "register_plugin",
    "load_plugins",
    "iter_plugins",
]

_LOGGER = logging.getLogger(__name__)
_REGISTRY: Dict[str, Any] = {}


def register_plugin(name: str, capability: Any) -> None:
    """Register a plugin capability under the given name."""
    _REGISTRY[name] = capability


def iter_plugins() -> Iterable[Tuple[str, Any]]:
    """Yield the registered plugin name and capability."""
    return _REGISTRY.items()


def load_plugins() -> None:
    """Import all plugin modules in this package.

    Any module inside ``nexus.plugins`` is treated as a plugin. Upon import,
    it is expected to call :func:`register_plugin` to declare its capabilities.
    Import errors or runtime errors during plugin import are logged but do not
    stop the application.
    """
    for module_info in pkgutil.iter_modules(__path__, prefix=__name__ + "."):
        try:
            import_module(module_info.name)
        except Exception as exc:  # pragma: no cover - defensive
            _LOGGER.error("Failed to load plugin %s: %s", module_info.name, exc)
