import sounddevice as sd
import numpy as np
from TTS.api import TTS
import speech_recognition as sr
import requests
import json
import asyncio
import time
from fastmcp import Client

# === CONFIGURACIÓN ===
LANG = "es"
SAMPLE_RATE = 16000
TTS_MODEL = "tts_models/es/css10/vits"
OLLAMA_URL = "http://localhost:11434/api/generate"
MCP_URL = "http://localhost:8000/mcp"
WAKE_WORD = ["charly", "charlie"]
MODEL = "llama3"

EXTRA_CONTEXT = """
Eres un asistente de voz llamado Charly. Responde SOLO en español, de forma natural y breve.
Tienes acceso a herramientas a través de un servidor MCP.
Cuando necesites usar una herramienta, responde exactamente así:

<mcp>{"tool": "nombre_herramienta", "args": {"parametro": "valor"}}</mcp>

Las herramientas disponibles son:
1 hora_actual() -> str: no debés pasar argumentos.
2 abrir_programa(nombre: str) -> str: Abre un programa o sitio web usando la url completa(ej: "https://youtube.com").
3 buscar_wikipedia(consulta: str, oraciones: int = 2)
4 obtener_clima(ciudad: str)

Después de que el sistema ejecute la herramienta, usa el resultado para continuar la conversación.
No inventes datos. Si hay un error, dilo amablemente.
Reescribe los números o signos (1,°, etc.), como palabras (uno, grado, etc.) en tus respuestas.

Ejemplo:
Usuario: ¿Cuál es la temperatura en Madrid?
Charly: <mcp>{"tool": "obtener_clima", "args": {"ciudad": "Madrid"}}</mcp>
server: (ejecuta la herramienta y obtiene un json con el resultado)
Charly: La temperatura en Madrid es 22°C.
"""

# === INICIALIZACIÓN ===
tts = TTS(model_name=TTS_MODEL, gpu=False)
listener = sr.Recognizer()

# === FUNCIONES AUXILIARES ===
def escuchar():
    """Escucha una frase por micrófono y la convierte en texto"""
    rec = ""
    try:
        with sr.Microphone() as source:
            print("🎤 Escuchando...")
            listener.adjust_for_ambient_noise(source)
            listener.pause_threshold = 0.8
            audio = listener.listen(source, timeout=10)
            rec = listener.recognize_google(audio, language="es-ES").lower().strip()
    except sr.UnknownValueError:
        print("🤔 No entendí lo que dijiste.")
    except Exception as e:
        print(f"⚠️ Error: {e}")
    return rec

def hablar(texto):
    """Convierte texto en voz y lo reproduce"""
    print("🗣️ Charly:", texto)
    texto = normalizar_texto(texto)
    wav = tts.tts(text=texto)
    audio = np.array(wav, dtype=np.float32)
    sd.play(audio, samplerate=tts.synthesizer.output_sample_rate)
    sd.wait()
    sd.stop()
    del wav, audio

def normalizar_texto(texto):
    reemplazos = {
        "°": " grados ",
        "%": " por ciento ",
        "km/h": " kilómetros por hora ",
        "m/s": " metros por segundo ",
        "1":"uno","2": "dos", "3": "tres", "4": "cuatro","5": "cinco",
        "6": "seis", "7": "siete", "8": "ocho", "9": "nueve", "0": "cero",
    }
    for k, v in reemplazos.items():
        texto = texto.replace(k, v)
    return texto

def limpiar_json_mcp(texto: str) -> dict:
    """Limpia y valida el bloque JSON dentro de etiquetas <mcp>"""
    texto = texto.strip().replace(">", "")

    try:
        data = json.loads(texto)
        return data
    except json.JSONDecodeError as e:
        print("⚠️ Error limpiando JSON MCP:", e, "| Texto:", texto)
        return {}


# === CLIENTE MCP ===

async def ejecutar_herramienta_mcp_async(tool_name: str, args: dict):
    """Llama a una herramienta MCP remota"""
    try:
        async with Client(MCP_URL) as client:
            result = await client.call_tool(tool_name, args)
            if hasattr(result, "content") and len(result.content) > 0:
                first = result.content[0]
                if hasattr(first, "text"):
                    return first.text
            return str(result)
    except Exception as e:
        return f"⚠️ Error al llamar a MCP: {e}"

def ejecutar_herramienta_mcp(tool_name: str, args: dict):
    """Versión síncrona para el asistente principal"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(ejecutar_herramienta_mcp_async(tool_name, args))
    finally:
        loop.close()

# === INTERACCIÓN CON OLLAMA ===

def generar_respuesta(prompt, contexto_extra=""):
    """Genera una respuesta del modelo Ollama"""
    payload = {
        "model": MODEL,
        "prompt": EXTRA_CONTEXT + "\n" + contexto_extra + "\nUsuario: " + prompt,
        "options": {
            "temperature": 0.4,
        },
        "stream": False
    }
    r = requests.post(OLLAMA_URL, json=payload)
    if r.status_code != 200:
        return f"Error: {r.text}"
    data = r.json()
    return data.get("response", "").strip()


# === PROCESADOR DE RESPUESTAS ===

def procesar_respuesta(texto_usuario):
    """Maneja respuestas que puedan incluir herramientas MCP"""
    respuesta = generar_respuesta(texto_usuario)
    print(f"🤖 Respuesta IA: {respuesta}")

    # Si hay una llamada a MCP en el texto
    if "<mcp>" in respuesta and "</mcp>" in respuesta:
        try:
            mcp_json = respuesta.split("<mcp>")[1].split("</mcp>")[0]
            mcp_data = json.loads(mcp_json)
            tool = mcp_data["tool"]
            args = mcp_data["args"]

            print(f"🔧 Llamando a herramienta MCP: {tool}({args})")
            resultado = ejecutar_herramienta_mcp(tool, args)
            print(f"📦 Resultado herramienta: {resultado}")

            # Enviar el resultado de vuelta a la IA
            contexto_extra = (
                f"El resultado de la herramienta {tool} fue: {resultado}. "
                f"Responde al usuario basándote en este resultado."
            )
            respuesta_final = generar_respuesta(texto_usuario, contexto_extra)
            return respuesta_final

        except Exception as e:
            return f"⚠️ Error procesando herramienta MCP: {e}"

    return respuesta


# === BUCLE PRINCIPAL ===

print("🤖 Asistente de voz 'Charly' iniciado. Decí 'Charly' para activarlo. Di 'salir' para terminar.\n")

while True:
    texto = escuchar()
    if not texto:
        continue

    if any(palabra in texto for palabra in ["salir", "adiós", "terminar"]):
        hablar("Hasta luego!")
        break

    if any(w in texto for w in WAKE_WORD):
        hablar("Sí, decime.")
        comando = escuchar()
        print(f"🧠 Procesando: {comando}")
        respuesta = procesar_respuesta(comando)
        hablar(respuesta)
    else:
        print("(sin palabra clave, ignorando...)")

    time.sleep(0.2)  # Pequeña pausa antes de la siguiente iteración
