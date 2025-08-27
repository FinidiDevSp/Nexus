"""Comandos misceláneos como tiempo, clima y archivos."""

def register(assistant):
    for frase in [
        "qué hora es",
        "que hora es",
        "qué día es",
        "que dia es",
    ]:
        assistant.register_command(frase, lambda text, _f=assistant._tell_time: _f())

    for frase in ["crea archivo", "borra archivo"]:
        assistant.register_command(frase, lambda text: assistant._manage_files(text))

    def weather(text):
        if "clima en" in text:
            ciudad = text.split("clima en", 1)[1].strip()
        else:
            ciudad = text.split("tiempo en", 1)[1].strip()
        if ciudad:
            assistant._get_weather(ciudad)
        else:
            assistant._say("No se reconoció la ciudad.")

    assistant.register_command("clima en", weather, match_type="startswith")
    assistant.register_command("tiempo en", weather, match_type="startswith")

    def timer(text):
        try:
            minutos = int(text.split("temporizador de", 1)[1].split("minuto")[0].strip())
            assistant._say(f"Temporizador de {minutos} minutos iniciado.")
            assistant._set_timer(minutos * 60)
        except ValueError:
            assistant._say("No se reconoció la duración del temporizador.")

    assistant.register_command("temporizador de", timer, match_type="startswith")
