from __future__ import annotations

import logging
from typing import Any

from . import register_plugin
from .base import Plugin

_LOGGER = logging.getLogger(__name__)


class HelloPlugin(Plugin):
    """A minimal plugin showcasing the required hooks."""

    def __init__(self) -> None:
        self._greeting: str = "Hello"
        self._loaded: bool = False

    def load(self, greeting: str = "Hello") -> None:
        """Initialize the plugin with an optional greeting."""
        self._greeting = greeting
        self._loaded = True
        _LOGGER.info("HelloPlugin loaded with greeting %s", self._greeting)

    def unload(self) -> None:
        """Clean up plugin resources."""
        self._loaded = False
        _LOGGER.info("HelloPlugin unloaded")

    def execute(self, name: str = "World", **_: Any) -> str:
        """Return a friendly greeting."""
        if not self._loaded:
            raise RuntimeError("HelloPlugin must be loaded before execution")
        message = f"{self._greeting}, {name}!"
        _LOGGER.debug("HelloPlugin executed for %s", name)
        return message


register_plugin("hello_plugin", HelloPlugin())
