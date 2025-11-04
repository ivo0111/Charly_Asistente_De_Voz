import subprocess, requests, json
from TTS.api import TTS
import os

OLLAMA_URL = "http://localhost:11434/api/generate"
WHISPER_PATH = r"C:\Users\ivogi\Escritorio\Proyectos\Asistente de voz\Charly2.0\whisper.cpp\build\bin\Release\whisper-cli.exe"  # ruta al ejecutable de whisper.cpp
WHISPER_MODEL = r"C:\Users\ivogi\Escritorio\Proyectos\Asistente de voz\Charly2.0\whisper.cpp\models\ggml-small.bin"  # ruta al modelo de whisper.cpp
TTS_MODEL = "coqui/xtts-v2"

tts = TTS(model_name=TTS_MODEL, gpu=False)

def transcribir(audio_path):
    cmd = [WHISPER_PATH, "-m", WHISPER_MODEL, "-f", audio_path, "-otxt"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip()

def generar_respuesta(prompt):
    payload = {"model": "llama3", "prompt": prompt}
    r = requests.post(OLLAMA_URL, json=payload, stream=True)
    respuesta = ""
    for line in r.iter_lines():
        if line:
            j = json.loads(line)
            if "response" in j:
                respuesta += j["response"]
    return respuesta.strip()

def hablar(texto, salida="respuesta.wav"):
    tts.tts_to_file(text=texto, speaker="Craig Gutsy", language="es" ,file_path=salida)
    os.startfile(salida)

if __name__ == "__main__":
    audio_in = "ejemplo.wav"  # Ruta al archivo de audio de entrada (hasta que tenga audio en vivo)
    texto = transcribir(audio_in)
    print("Usuario:", texto)
    respuesta = generar_respuesta(texto)
    print("Asistente:", respuesta)
    hablar(respuesta)
