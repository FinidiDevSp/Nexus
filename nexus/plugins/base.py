from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Plugin(ABC):
    """Abstract base class for all Nexus plugins.

    Plugins must implement the lifecycle hooks :meth:`load`, :meth:`unload`
    and :meth:`execute`.
    """

    @abstractmethod
    def load(self) -> None:
        """Perform any setup required before the plugin can be used.

        Returns:
            None

        Raises:
            RuntimeError: If the plugin cannot be initialized.
        """

    @abstractmethod
    def unload(self) -> None:
        """Release any resources held by the plugin.

        Returns:
            None

        Raises:
            RuntimeError: If cleanup fails.
        """

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Run the plugin's main action.

        Args:
            *args: Positional arguments passed to the plugin.
            **kwargs: Keyword arguments passed to the plugin.

        Returns:
            Any: The plugin-specific result of the execution.

        Raises:
            Exception: Implementations may raise any exception to signal
                execution failure.
        """
