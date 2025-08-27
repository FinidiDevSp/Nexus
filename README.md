# Nexus

Asistente de voz controlado por palabra clave u atajo de teclado.

## Configuración

El archivo `config.json` en la raíz del proyecto define los ajustes básicos:

```json
{
  "palabra_clave": "nexus",
  "hotkey": "ctrl+shift+space"
}
```

- `palabra_clave`: palabra necesaria para activar el asistente mediante voz.
- `hotkey`: combinación de teclas para activar el asistente manualmente.

## Plugins

Los comandos del asistente se cargan desde módulos ubicados en el directorio
`plugins/`. Cada archivo debe tener un nombre en *snake_case* y definir una
función `register(assistant)` que recibe la instancia de `NexusAssistant` y
añade los comandos mediante `assistant.register_command`.

Ejemplo mínimo:

```python
# plugins/saludos.py
def register(assistant):
    assistant.register_command(
        "di hola",
        lambda text: assistant._say("¡Hola!"),
    )
```

Los módulos se importan automáticamente al iniciar el programa.
