import sounddevice as sd
import numpy as np
import torch
from TTS.api import TTS
from faster_whisper import WhisperModel
import subprocess, requests, json, re
import os
import speech_recognition as sr
import pyttsx3

# --- CONFIGURACIÓN ---
LANG = "es"
DEVICE = "cpu"  # usar "cuda" para GPU (todavía no lo veo bien)
SAMPLE_RATE = 16000
TTS_MODEL = "tts_models/es/css10/vits"
OLLAMA_URL = "http://localhost:11434/api/generate"  # api generar respuesta (IA)
WAKE_WORD = ["charly", "charlie", "Charly", "Charlie"]  # palabras clave para activar
EXTRA_CONTEXT = (
    "Eres un asistente de voz llamado Charly. Responde de manera concisa, resumida y amigable. "
    "Las respuestas deben ser en español. Si no sabes la respuesta, di que no lo sabes."
    "No inventes información. "
    "Si el usuario hace una petición que necesite un comando externo, escribelo entre etiquetas <cmd></cmd>."
    "Tenés que adaptar los comandos a un windows 11. "
    "Para ello, usa el siguiente formato: <cmd>comando_a_ejecutar</cmd>. Por ejemplo, si el usuario te pide abrir el bloc de notas, debes responder: <cmd>start notepad</cmd>."
    "El nombre de usuario es:"
    f"os.getlogin()"
)

# --- INICIALIZACIÓN ---
tts = TTS(model_name=TTS_MODEL, gpu=False)
stt = WhisperModel("small", device=DEVICE)
listener = sr.Recognizer()
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)

def listen():
    rec = ""
    try:
        with sr.Microphone() as source:
            print("🎤 Escuchando...")
            listener.adjust_for_ambient_noise(source)
            pc = listener.listen(source, timeout=5)
            rec = listener.recognize_google(pc, language='es-ES')
            rec = rec.lower().strip()
    except sr.UnknownValueError:
        print("No entendí lo que dijiste")
    except sr.RequestError:
        print("Error de conexión a Google")
    except Exception as e:
        print(f"Error: {e}")
    return rec

def responder(prompt):
    payload = {"model": "llama3", "prompt": EXTRA_CONTEXT+"/n"+"El usuario dice:"+prompt}
    r = requests.post(OLLAMA_URL, json=payload, stream=True)
    respuesta = ""
    for line in r.iter_lines():
        if line:
            j = json.loads(line)
            if "response" in j:
                respuesta += j["response"]
    return respuesta.strip()

def hablar(texto):
    print("🗣️ Respondiendo...")
    wav = tts.tts(text=texto)
    audio = np.array(wav, dtype=np.float32)
    sd.play(audio, samplerate=tts.synthesizer.output_sample_rate)
    sd.wait() # Espera a que termine de reproducir

def extraer_comando(respuesta):
    # Extrae el comando entre las etiquetas <cmd></cmd>
    match = re.search(r"<cmd>(.*?)</cmd>", respuesta, re.IGNORECASE | re.DOTALL) # DOTALL para multilinea
    return match.group(1).strip() if match else None

def ejecutar_comando(cmd):
    try:
        subprocess.Popen(cmd, shell=True)
    except Exception as e:
        print(f"Error al ejecutar comando: {e}")
        hablar("Hubo un error al ejecutar el comando.")

# --- BUCLE PRINCIPAL ---
print("Asistente Charly iniciado. Decí 'Charly' para activarlo, o 'salir' para cerrar.\n")

while True:
    texto = listen()

    if not texto:
        continue

    if any(palabra in texto for palabra in ["salir", "terminar", "adiós"]):
        print("Hasta luego!")
        break

    # Si detecta la palabra clave, escucha el siguiente comando
    if any(p in texto for p in WAKE_WORD):
        hablar("Sí, decime.")
        comando = listen()
        print(f"Procesando: {comando}")
        respuesta = responder(comando)
        print(f"Respuesta IA: {respuesta}")

        # Buscar si hay comando dentro de la respuesta
        cmd = extraer_comando(respuesta)
        if cmd:
            # Preguntar confirmación
            hablar(f"¿Querés que ejecute el comando: {cmd}?")
            confirmacion = listen()
            if any(c in confirmacion for c in ["sí", "claro", "dale", "por favor", "ok"]):
                hablar("Perfecto, ejecutando.")
                ejecutar_comando(cmd)
            else:
                hablar("De acuerdo, cancelado.")
        else:
            # Si no hay comando, solo hablar la respuesta
            respuesta_limpia = re.sub(r"<cmd>.*?</cmd>", "", respuesta, flags=re.DOTALL)
            hablar(respuesta_limpia)
    else:
        print("(sin palabra clave, ignorando...)")
