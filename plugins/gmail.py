"""Enviar correos mediante Gmail."""

import os
import smtplib
from email.mime.text import MIMEText


def register(assistant):
    def enviar(text):
        resto = text.replace("envia correo a", "", 1).strip()
        if " " not in resto:
            assistant._say("Formato: envia correo a correo@dominio.com mensaje")
            return
        destino, mensaje = resto.split(" ", 1)
        user = os.getenv("GMAIL_USER")
        password = os.getenv("GMAIL_PASS")
        if not user or not password:
            assistant._say("Faltan credenciales de Gmail.")
            return
        try:
            msg = MIMEText(mensaje)
            msg["Subject"] = "Mensaje de Nexus"
            msg["From"] = user
            msg["To"] = destino
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(user, password)
                server.send_message(msg)
            assistant._say("Correo enviado.")
        except Exception:
            assistant._say("Error al enviar el correo.")
    assistant.register_command(
        "envia correo a",
        enviar,
        match_type="startswith",
    )
