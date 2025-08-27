"""Integración básica con Notion para crear notas."""

import os
import requests

NOTION_API = "https://api.notion.com/v1/pages"
NOTION_VERSION = "2022-06-28"

def register(assistant):
    def crear_nota(text):
        contenido = text.replace("crea nota", "", 1).strip()
        token = assistant.config.get("notion_token") or os.getenv("NOTION_TOKEN")
        database_id = assistant.config.get("notion_database_id") or os.getenv("NOTION_DATABASE_ID")
        if not contenido:
            assistant.speak("No se proporcionó el contenido de la nota.")
            return
        if not token or not database_id:
            assistant.speak("Faltan credenciales de Notion.")
            return
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        }
        data = {
            "parent": {"database_id": database_id},
            "properties": {
                "title": {"title": [{"text": {"content": contenido}}]}
            },
        }
        try:
            resp = requests.post(NOTION_API, headers=headers, json=data, timeout=10)
            if resp.status_code == 200:
                assistant.speak("Nota creada en Notion.")
            else:
                assistant.speak("Error al crear la nota en Notion.")
        except Exception:
            assistant.speak("Error al contactar con Notion.")
    assistant.register_command(
        "crea nota",
        crear_nota,
        match_type="startswith",
    )
