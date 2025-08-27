"""Gestión de notas."""

def register(assistant):
    assistant.register_command(
        "anota",
        lambda text: assistant._add_note(text.replace("anota", "", 1).strip()),
        match_type="startswith",
    )
    assistant.register_command(
        "lista notas",
        lambda text: assistant._list_notes(),
    )

    def _remove(text):
        resto = text.replace("borra nota", "", 1).strip()
        if resto.isdigit():
            assistant._remove_note(int(resto) - 1)
        else:
            assistant._say("Indica el número de la nota a borrar.")
    assistant.register_command(
        "borra nota",
        _remove,
        match_type="startswith",
    )
