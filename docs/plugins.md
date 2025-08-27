# Plugin Development

Nexus ships with a lightweight plugin architecture that allows optional
features to be added without modifying the core application.

## Directory layout

```
nexus/
  plugins/
    base.py        # abstract Plugin API
    hello_plugin.py  # example implementation
config/
  plugins.yaml     # plugin configuration
```

## Creating a plugin

1. **Subclass** `nexus.plugins.base.Plugin` and implement all lifecycle hooks:
   `load`, `unload`, and `execute`.
2. **Register** an instance with
   `nexus.plugins.register_plugin` when the module is imported.
3. Optionally accept configuration parameters in `load`.

Example implementation:

```python
# nexus/plugins/hello_plugin.py
from . import register_plugin
from .base import Plugin

class HelloPlugin(Plugin):
    def __init__(self) -> None:
        self._greeting = "Hello"
        self._loaded = False

    def load(self, greeting: str = "Hello") -> None:
        self._greeting = greeting
        self._loaded = True

    def unload(self) -> None:
        self._loaded = False

    def execute(self, name: str = "World") -> str:
        return f"{self._greeting}, {name}!"

register_plugin("hello_plugin", HelloPlugin())
```

## Configuration

Plugins are enabled and customized via `config/plugins.yaml`:

```yaml
plugins:
  hello_plugin:
    enabled: true
    greeting: "Howdy"
```

Only plugins with `enabled: true` are loaded. Additional keys are passed as
arguments to the plugin's `load` method.

## Testing your plugin

1. Update `config/plugins.yaml` with your plugin settings.
2. Run the application to verify it loads:

```bash
python -m nexus.app
```

3. Write unit tests that import your plugin and exercise its behavior, then run:

```bash
pytest
```

This ensures your plugin integrates correctly with the Nexus plugin system.
