"""Plugin system for the Nexus application."""

from importlib import import_module
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

try:  # pragma: no cover - optional dependency
    import yaml
except Exception:  # pragma: no cover - defensive
    yaml = None

from .base import Plugin

__all__ = [
    "register_plugin",
    "load_plugins",
    "iter_plugins",
    "Plugin",
]

_LOGGER = logging.getLogger(__name__)
_REGISTRY: Dict[str, Plugin] = {}


def _read_config() -> Dict[str, Dict[str, Any]]:
    """Read plugin configuration from ``config/plugins.yaml``.

    Returns an empty mapping if the configuration file is missing, malformed
    or cannot be parsed. Each key is the plugin module name relative to
    ``nexus.plugins`` and maps to a dictionary of options. The ``enabled``
    option defaults to ``True`` if not provided.
    """
    config_path = Path(__file__).resolve().parents[2] / "config" / "plugins.yaml"
    if yaml is None:
        _LOGGER.warning("PyYAML not installed; skipping plugin configuration")
        return {}
    if not config_path.exists():
        _LOGGER.info("Plugin configuration %s not found; loading no plugins", config_path)
        return {}
    try:
        with config_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except Exception as exc:  # pragma: no cover - defensive
        _LOGGER.error("Failed to read plugin config %s: %s", config_path, exc)
        return {}
    if not isinstance(data, dict):
        _LOGGER.error("Plugin config %s is malformed: expected a mapping", config_path)
        return {}
    plugins = data.get("plugins", {})
    if not isinstance(plugins, dict):
        _LOGGER.error("'plugins' section in %s is malformed", config_path)
        return {}
    return plugins


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
    """Load and initialize enabled plugins based on configuration.

    Only plugins listed in ``config/plugins.yaml`` with ``enabled: true`` are
    imported. After a plugin module registers itself via :func:`register_plugin`,
    its :meth:`~Plugin.load` method is invoked with any additional settings
    supplied in the configuration. Import errors or failures during
    initialization are logged but do not stop the application.
    """
    config = _read_config()
    for name, opts in config.items():
        if not isinstance(opts, dict):
            _LOGGER.warning("Ignoring malformed configuration for plugin %s", name)
            continue
        if not opts.get("enabled", True):
            continue
        module_name = f"{__name__}.{name}"
        try:
            import_module(module_name)
        except Exception as exc:  # pragma: no cover - defensive
            _LOGGER.error("Failed to import plugin %s: %s", module_name, exc)
            continue
        plugin = _REGISTRY.get(name)
        if plugin is None:
            _LOGGER.warning("Plugin %s did not register itself", name)
            continue
        params = {k: v for k, v in opts.items() if k != "enabled"}
        try:
            plugin.load(**params)
        except TypeError:
            try:
                plugin.load()
            except Exception as exc:  # pragma: no cover - defensive
                _LOGGER.error("Failed to initialize plugin %s: %s", name, exc)
        except Exception as exc:  # pragma: no cover - defensive
            _LOGGER.error("Failed to initialize plugin %s: %s", name, exc)
