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
        lambda text: (assistant._say("Apagando el ordenador."), assistant._shutdown()),
    )
    assistant.register_command(
        "salir",
        lambda text: (
            assistant._say("Hasta luego."),
            assistant._save_memory(),
            assistant._save_notes(),
            sys.exit(0),
        ),
    )
    assistant.register_command(
        "modo apagado",
        lambda text: (setattr(assistant, "active", False), assistant._say("Modo apagado.")),
    )
    assistant.register_command(
        "modo encendido",
        lambda text: (setattr(assistant, "active", True), assistant._say("Modo encendido.")),
    )
