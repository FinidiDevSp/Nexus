import speech_recognition as sr
import os
import platform

PALABRA_CLAVE = "nexus"

def escuchar_comando():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Escuchando...")
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)
    try:
        comando = r.recognize_google(audio, language="es-ES")
        print(f"Dijiste: {comando}")
        return comando.lower()
    except sr.UnknownValueError:
        print("No entendí lo que dijiste")
    except sr.RequestError:
        print("Error con el servicio de reconocimiento de voz")
    return ""

def apagar_pc():
    sistema = platform.system()
    if sistema == "Windows":
        os.system("shutdown /s /t 1")
    elif sistema == "Linux" or sistema == "Darwin":
        os.system("shutdown now")

if __name__ == "__main__":
    while True:
        comando = escuchar_comando()
        if PALABRA_CLAVE in comando:
            print("Palabra clave detectada. Esperando instrucción...")
            comando = escuchar_comando()
            if "apaga" in comando or "apagar" in comando:
                print("Apagando el ordenador...")
                apagar_pc()
                break
