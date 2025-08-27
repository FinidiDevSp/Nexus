"""Enviar correos mediante Gmail."""

import os
import smtplib
from email.mime.text import MIMEText


def register(assistant):
    def enviar(text):
        resto = text.replace("envia correo a", "", 1).strip()
        if " " not in resto:
            assistant.speak("Formato: envia correo a correo@dominio.com mensaje")
            return
        destino, mensaje = resto.split(" ", 1)
        user = assistant.config.get("gmail_user") or os.getenv("GMAIL_USER")
        password = assistant.config.get("gmail_pass") or os.getenv("GMAIL_PASS")
        if not user or not password:
            assistant.speak("Faltan credenciales de Gmail.")
            return
        try:
            msg = MIMEText(mensaje)
            msg["Subject"] = "Mensaje de Nexus"
            msg["From"] = user
            msg["To"] = destino
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(user, password)
                server.send_message(msg)
            assistant.speak("Correo enviado.")
        except Exception:
            assistant.speak("Error al enviar el correo.")
    assistant.register_command(
        "envia correo a",
        enviar,
        match_type="startswith",
    )
