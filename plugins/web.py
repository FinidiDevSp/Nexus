"""Comandos relacionados con navegación web."""

def register(assistant):
    assistant.register_command(
        "busca en google",
        lambda text: assistant._google_search(text.replace("busca en google", "", 1).strip()),
        match_type="startswith",
    )
    assistant.register_command(
        "youtube",
        lambda text: assistant._open_youtube(),
    )
    assistant.register_command(
        "spotify",
        lambda text: assistant._open_spotify(),
    )
