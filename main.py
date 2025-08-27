import importlib
import json
import os
import platform
import sys
import webbrowser
from pathlib import Path
from urllib.parse import quote_plus

import keyboard
import openai
import pkgutil
import pyttsx3
import requests
import speech_recognition as sr
import threading
import time
from datetime import datetime

CONFIG_FILE = "config.json"
MEMORY_FILE = "memory.json"
NOTES_FILE = "notes.json"


class NexusAssistant:
    """Asistente de voz básico con activación por palabra clave u atajo."""

    def __init__(self) -> None:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        self.config = cfg
        self.keyword = cfg.get("palabra_clave", "nexus")
        self.hotkey = cfg.get("hotkey", "ctrl+shift+space")
        self.require_face = cfg.get("reconocimiento_facial", False)
        self.silence = cfg.get("modo_silencio", False)
        self.recognizer = sr.Recognizer()
        self.tts = pyttsx3.init()
        self.active = True
        self.memory = self._load_memory()
        self.timers = []
        self.notes = self._load_notes()
        self.commands = {}
        self._load_plugins()

    def register_command(self, trigger: str, handler, match_type: str = "in") -> None:
        """Registra un comando en el asistente."""
        self.commands[trigger] = (handler, match_type)

    def _load_plugins(self) -> None:
        """Importa automáticamente los módulos del directorio de plugins."""
        plugins_path = Path(__file__).parent / "plugins"
        if not plugins_path.exists():
            return
        for module_info in pkgutil.iter_modules([str(plugins_path)]):
            module = importlib.import_module(f"plugins.{module_info.name}")
            if hasattr(module, "register"):
                module.register(self)

    # Utilidades -----------------------------------------------------------------
    def _say(self, text: str) -> None:
        print(f"Nexus: {text}")
        if not getattr(self, "silence", False):
            self.tts.say(text)
            self.tts.runAndWait()

    def _load_memory(self) -> list:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save_memory(self) -> None:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, ensure_ascii=False, indent=2)

    def _load_notes(self) -> list:
        if os.path.exists(NOTES_FILE):
            with open(NOTES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save_notes(self) -> None:
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            json.dump(self.notes, f, ensure_ascii=False, indent=2)

    # Acciones -------------------------------------------------------------------
    def _chatgpt(self, text: str) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self._say("No hay clave de API configurada.")
            return
        openai.api_key = api_key
        self.memory.append({"role": "user", "content": text})
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo", messages=self.memory
            )
            reply = response.choices[0].message["content"]
            self._say(reply)
            self.memory.append({"role": "assistant", "content": reply})
        except Exception:
            self._say("Error al contactar con GPT.")

    def _google_search(self, query: str) -> None:
        webbrowser.open(f"https://www.google.com/search?q={quote_plus(query)}")
        self._say("Buscando en Google.")

    def _open_youtube(self) -> None:
        webbrowser.open("https://www.youtube.com")
        self._say("Abriendo YouTube.")

    def _open_spotify(self) -> None:
        webbrowser.open("https://open.spotify.com")
        self._say("Abriendo Spotify.")

    def _adjust_volume(self, up: bool = True) -> None:
        sistema = platform.system()
        if sistema == "Windows":
            os.system(f"nircmd.exe changesysvolume {'5000' if up else '-5000'}")
        elif sistema == "Linux":
            os.system(f"amixer -D pulse sset Master {'5%+' if up else '5%-'}")
        elif sistema == "Darwin":
            delta = "+ 5" if up else "- 5"
            os.system(
                f"osascript -e 'set volume output volume ((output volume of (get volume settings)) {delta})'"
            )

    def _tell_time(self) -> None:
        now = datetime.now()
        fecha = now.strftime("%d/%m/%Y")
        hora = now.strftime("%H:%M")
        self._say(f"Hoy es {fecha} y son las {hora}.")

    def _manage_files(self, text: str) -> None:
        if "crea archivo" in text:
            nombre = text.split("crea archivo", 1)[1].strip()
            open(nombre, "w").close()
            self._say(f"Archivo {nombre} creado.")
        elif "borra archivo" in text:
            nombre = text.split("borra archivo", 1)[1].strip()
            try:
                os.remove(nombre)
                self._say(f"Archivo {nombre} borrado.")
            except FileNotFoundError:
                self._say("Archivo no encontrado.")

    def _add_note(self, note: str) -> None:
        if note:
            self.notes.append(note)
            self._say("Nota guardada.")
        else:
            self._say("No se proporcionó el contenido de la nota.")

    def _list_notes(self) -> None:
        if not self.notes:
            self._say("No hay notas guardadas.")
            return
        for idx, note in enumerate(self.notes, start=1):
            self._say(f"Nota {idx}: {note}")

    def _remove_note(self, index: int) -> None:
        if 0 <= index < len(self.notes):
            nota = self.notes.pop(index)
            self._say(f"Nota '{nota}' borrada.")
        else:
            self._say("Número de nota inválido.")

    def _get_weather(self, ciudad: str) -> None:
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            self._say("No hay clave de API de OpenWeather configurada.")
            return
        try:
            resp = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"q": ciudad, "appid": api_key, "lang": "es", "units": "metric"},
                timeout=10,
            )
            if resp.status_code != 200:
                self._say("No se pudo obtener el clima.")
                return
            data = resp.json()
            desc = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            self._say(f"El clima en {ciudad} es {desc} con {temp}°C.")
        except Exception:
            self._say("Error al consultar el clima.")

    def _turn_off_screen(self) -> None:
        sistema = platform.system()
        if sistema == "Windows":
            os.system("nircmd.exe monitor off")
        elif sistema == "Linux":
            os.system("xset dpms force off")
        elif sistema == "Darwin":
            os.system("pmset displaysleepnow")

    def _hibernate(self) -> None:
        sistema = platform.system()
        if sistema == "Windows":
            os.system("shutdown /h")
        elif sistema == "Linux":
            os.system("systemctl hibernate")
        elif sistema == "Darwin":
            os.system("pmset sleepnow")

    def _confirm_face(self) -> bool:
        self._say("Confirmación de rostro requerida.")
        resp = input("¿Rostro reconocido? (si/no): ").strip().lower()
        return resp == "si"

    def _shutdown(self) -> None:
        sistema = platform.system()
        if sistema == "Windows":
            os.system("shutdown /s /t 1")
        elif sistema in ("Linux", "Darwin"):
            os.system("shutdown now")

    def _set_timer(self, segundos: int) -> None:
        def tarea() -> None:
            time.sleep(segundos)
            self._say("Temporizador finalizado.")
            try:
                self.timers.remove(threading.current_thread())
            except ValueError:
                pass

        hilo = threading.Thread(target=tarea, daemon=True)
        self.timers.append(hilo)
        hilo.start()

    # Lógica principal ------------------------------------------------------------
    def _process(self, text: str) -> None:
        for trigger, (action, mode) in self.commands.items():
            if mode == "startswith" and text.startswith(trigger):
                action(text)
                return
            if mode == "in" and trigger in text:
                action(text)
                return
        self._chatgpt(text)

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    from gui.app import ChatWindow

    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())

