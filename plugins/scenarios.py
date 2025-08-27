"""Apertura de escenarios configurables."""

import subprocess


def register(assistant):
    escenarios = assistant.config.get("escenarios", {})
    for nombre, comandos in escenarios.items():
        def _make_handler(cmds, nombre=nombre):
            def handler(text):
                for cmd in cmds:
                    try:
                        subprocess.Popen(cmd, shell=True)
                    except Exception:
                        pass
                assistant._say(f"Escenario {nombre} abierto.")
            return handler
        assistant.register_command(
            f"abre {nombre}",
            _make_handler(comandos),
            match_type="startswith",
        )
