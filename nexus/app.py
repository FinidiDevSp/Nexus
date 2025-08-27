"""Main application logic for the Nexus package."""

from .plugins import load_plugins, iter_plugins


def main() -> None:
    """Entry point for running the Nexus application."""
    load_plugins()
    for name, capability in iter_plugins():
        print(f"Loaded plugin {name}: {capability}")


if __name__ == "__main__":
    main()
