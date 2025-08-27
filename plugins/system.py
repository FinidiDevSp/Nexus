"""Comandos relacionados con el sistema."""

import sys

def register(assistant):
    assistant.register_command(
        "sube el volumen",
        lambda text: assistant._adjust_volume(True),
    )
    assistant.register_command(
        "baja el volumen",
        lambda text: assistant._adjust_volume(False),
    )
    assistant.register_command(
        "apaga la pantalla",
        lambda text: assistant._turn_off_screen(),
    )
    assistant.register_command(
        "apaga las pantallas",
        lambda text: assistant._turn_off_screen(),
    )
    assistant.register_command(
        "apaga",
        lambda text: (assistant.speak("Apagando el ordenador."), assistant._shutdown()),
    )
    assistant.register_command(
        "hiberna",
        lambda text: (assistant.speak("Hibernando el ordenador."), assistant._hibernate()),
    )
    assistant.register_command(
        "salir",
        lambda text: (
            assistant.speak("Hasta luego."),
            assistant._save_memory(),
            assistant._save_notes(),
            sys.exit(0),
        ),
    )
    assistant.register_command(
        "modo apagado",
        lambda text: (setattr(assistant, "active", False), assistant.speak("Modo apagado.")),
    )
    assistant.register_command(
        "modo encendido",
        lambda text: (setattr(assistant, "active", True), assistant.speak("Modo encendido.")),
    )
    assistant.register_command(
        "modo silencio",
        lambda text: (assistant.speak("Modo silencio activado."), setattr(assistant, "silence", True)),
    )
    assistant.register_command(
        "modo voz",
        lambda text: (setattr(assistant, "silence", False), assistant.speak("Modo voz activado.")),
    )
