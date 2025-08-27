import json
import os
import platform
import sys
import webbrowser
from urllib.parse import quote_plus

import keyboard
import openai
import pyttsx3
import requests
import speech_recognition as sr

CONFIG_FILE = "config.json"
MEMORY_FILE = "memory.json"


class NexusAssistant:
    """Asistente de voz básico con activación por palabra clave u atajo."""

    def __init__(self) -> None:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        self.keyword = cfg.get("palabra_clave", "nexus")
        self.hotkey = cfg.get("hotkey", "ctrl+shift+space")
        self.recognizer = sr.Recognizer()
        self.tts = pyttsx3.init()
        self.active = True
        self.memory = self._load_memory()

    # Utilidades -----------------------------------------------------------------
    def _say(self, text: str) -> None:
        print(f"Nexus: {text}")
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

    def _listen(self) -> str:
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source)
            audio = self.recognizer.listen(source)
        try:
            comando = self.recognizer.recognize_google(audio, language="es-ES").lower()
            print(f"Escuchado: {comando}")
            return comando
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            self._say("Error con el servicio de reconocimiento de voz.")
            return ""

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

    def _shutdown(self) -> None:
        sistema = platform.system()
        if sistema == "Windows":
            os.system("shutdown /s /t 1")
        elif sistema in ("Linux", "Darwin"):
            os.system("shutdown now")

    # Lógica principal ------------------------------------------------------------
    def _process(self, text: str) -> None:
        if text.startswith("busca en google"):
            self._google_search(text.replace("busca en google", "", 1))
        elif "youtube" in text:
            self._open_youtube()
        elif "spotify" in text:
            self._open_spotify()
        elif "sube el volumen" in text:
            self._adjust_volume(True)
        elif "baja el volumen" in text:
            self._adjust_volume(False)
        elif "apaga la pantalla" in text or "apaga las pantallas" in text:
            self._turn_off_screen()
        elif "apaga" in text and "pantalla" not in text:
            self._say("Apagando el ordenador.")
            self._shutdown()
        elif "salir" in text:
            self._say("Hasta luego.")
            self._save_memory()
            sys.exit(0)
        elif "modo apagado" in text:
            self.active = False
            self._say("Modo apagado.")
        elif "modo encendido" in text:
            self.active = True
            self._say("Modo encendido.")
        elif "crea archivo" in text or "borra archivo" in text:
            self._manage_files(text)
        elif "clima en" in text or "tiempo en" in text:
            if "clima en" in text:
                ciudad = text.split("clima en", 1)[1].strip()
            else:
                ciudad = text.split("tiempo en", 1)[1].strip()
            if ciudad:
                self._get_weather(ciudad)
            else:
                self._say("No se reconoció la ciudad.")
        else:
            self._chatgpt(text)

    def run(self) -> None:
        self._say("Nexus iniciado.")
        while True:
            if not self.active:
                keyboard.wait(self.hotkey)
                self.active = True
            if keyboard.is_pressed(self.hotkey):
                comando = self._listen()
                self._process(comando)
                continue
            comando = self._listen()
            if self.keyword in comando:
                comando = comando.replace(self.keyword, "", 1).strip()
                if not comando:
                    comando = self._listen()
                self._process(comando)


if __name__ == "__main__":
    asistente = NexusAssistant()
    try:
        asistente.run()
    finally:
        asistente._save_memory()

