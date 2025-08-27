"""Consulta básica de eventos en Google Calendar."""

import os
from datetime import datetime, timedelta, timezone
import requests

GOOGLE_API = "https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"

def register(assistant):
    def reuniones(text):
        token = assistant.config.get("google_calendar_token") or os.getenv("GOOGLE_CALENDAR_TOKEN")
        calendar_id = (
            assistant.config.get("google_calendar_id")
            or os.getenv("GOOGLE_CALENDAR_ID")
            or "primary"
        )
        if not token:
            assistant.speak("No hay token de Google Calendar.")
            return
        now = datetime.now(timezone.utc)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        params = {
            "timeMin": start.isoformat(),
            "timeMax": end.isoformat(),
            "singleEvents": "true",
            "orderBy": "startTime",
        }
        headers = {"Authorization": f"Bearer {token}"}
        try:
            resp = requests.get(
                GOOGLE_API.format(calendar_id=calendar_id),
                params=params,
                headers=headers,
                timeout=10,
            )
            if resp.status_code != 200:
                assistant.speak("No se pudo obtener el calendario.")
                return
            eventos = resp.json().get("items", [])
            if not eventos:
                assistant.speak("No hay reuniones hoy.")
                return
            for ev in eventos:
                inicio = ev.get("start", {}).get("dateTime") or ev.get("start", {}).get("date")
                resumen = ev.get("summary", "Sin título")
                assistant.speak(f"{resumen} a las {inicio}")
        except Exception:
            assistant.speak("Error al contactar con Google Calendar.")
    assistant.register_command("reuniones de hoy", reuniones)
