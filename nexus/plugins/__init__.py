"""Plugin system for the Nexus application."""

from importlib import import_module
import logging
import pkgutil
from typing import Dict, Iterable, Tuple

from .base import Plugin

__all__ = [
    "register_plugin",
    "load_plugins",
    "iter_plugins",
    "Plugin",
]

_LOGGER = logging.getLogger(__name__)
_REGISTRY: Dict[str, Plugin] = {}


def register_plugin(name: str, capability: Plugin) -> None:
    """Register a plugin instance under the given name.

    Raises:
        TypeError: If ``capability`` is not an instance of :class:`Plugin`.
    """
    if not isinstance(capability, Plugin):
        raise TypeError(f"Plugin {name!r} must subclass Plugin")
    _REGISTRY[name] = capability


def iter_plugins() -> Iterable[Tuple[str, Plugin]]:
    """Yield the registered plugin name and instance."""
    return _REGISTRY.items()


def load_plugins() -> None:
    """Import all plugin modules in this package.

    Any module inside ``nexus.plugins`` is treated as a plugin. Upon import,
    it is expected to call :func:`register_plugin` with an instance of
    :class:`Plugin`. Import errors or attempts to register non-conforming
    objects are logged but do not stop the application.
    """
    for module_info in pkgutil.iter_modules(__path__, prefix=__name__ + "."):
        try:
            import_module(module_info.name)
        except Exception as exc:  # pragma: no cover - defensive
            _LOGGER.error("Failed to load plugin %s: %s", module_info.name, exc)
