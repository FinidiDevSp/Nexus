# Nexus

Asistente de voz controlado por palabra clave u atajo de teclado.

## Configuración

El archivo `config.json` en la raíz del proyecto define los ajustes básicos:

```json
{
  "palabra_clave": "nexus",
  "hotkey": "ctrl+shift+space",
  "reconocimiento_facial": false,
  "modo_silencio": false,
  "tema": "auto",
  "avatar_usuario": "",
  "avatar_asistente": "",
  "escenarios": {
    "modo de trabajo": [
      "code",
      "notepad",
      "chrome https://www.google.com https://www.notion.so"
    ]
  },
  "openai_api_key": "",
  "openweather_api_key": "",
  "notion_token": "",
  "notion_database_id": "",
  "google_calendar_token": "",
  "google_calendar_id": "",
  "gmail_user": "",
  "gmail_pass": ""
}
```

- `palabra_clave`: palabra necesaria para activar el asistente mediante voz.
- `hotkey`: combinación de teclas para activar el asistente manualmente.
- `reconocimiento_facial`: si está activo, se pedirá confirmación antes de iniciar.
- `modo_silencio`: inicia sin salida de voz.
- `tema`: modo de color de la interfaz (`claro`, `oscuro` o `auto` para alternar según la hora).
- `avatar_usuario`: imagen utilizada para los mensajes del usuario.
- `avatar_asistente`: imagen mostrada en las respuestas del asistente.
- `escenarios`: conjuntos de programas que pueden abrirse con el comando "abre <nombre>".
- `openai_api_key`: clave para usar la API de OpenAI.
- `openweather_api_key`: clave para consultar el clima.
- `notion_token` y `notion_database_id`: credenciales para Notion.
- `google_calendar_token` y `google_calendar_id`: credenciales para Google Calendar.
- `gmail_user` y `gmail_pass`: credenciales de Gmail.

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
        lambda text: assistant.speak("¡Hola!"),
    )
```

Los módulos se importan automáticamente al iniciar el programa.

## Integraciones y comandos

- **Escenarios**: define conjuntos de programas en `config.json` y actívalos con `abre <escenario>`.
- **Hibernación**: di `hiberna` para suspender el equipo.
- **Modo silencio**: `modo silencio` desactiva la voz y `modo voz` la reactiva.
- **Notion**: `crea nota <texto>` crea una nota en Notion (requiere `notion_token` y `notion_database_id` en `config.json`).
- **Google Calendar**: `reuniones de hoy` muestra los eventos del día (requiere `google_calendar_token` y opcional `google_calendar_id` en `config.json`).
- **Gmail**: `envia correo a <email> <mensaje>` envía un correo mediante Gmail (requiere `gmail_user` y `gmail_pass` en `config.json`).

## Distribución en Windows

Para generar un ejecutable de Windows se incluye el script `build_windows.bat`. Requiere tener Python y [PyInstaller](https://pyinstaller.org/) instalados.

```bat
build_windows.bat
```

El comando compila `gui/app.py` en modo gráfico (sin consola) e incorpora el icono definido en `gui/icon.ico`. El ejecutable resultante se encuentra en `dist/Nexus/Nexus.exe`.

Para distribuir la aplicación copia la carpeta `dist/Nexus` a otro equipo y ejecuta `Nexus.exe`.