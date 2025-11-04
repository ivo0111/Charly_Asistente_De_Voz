from fastmcp import FastMCP
import uvicorn
import datetime
import subprocess
import webbrowser
import wikipedia
import requests

# Crear servidor MCP
mcp = FastMCP("LocalTools")

@mcp.tool()
def prueba(number: float) -> float:
    """Devuelve el resultado de aplicar la función Maurística al número dado"""
    return number / 2 + 10

@mcp.tool()
def hora_actual() -> str:
    """Devuelve la hora y fecha actual en formato legible"""
    ahora = datetime.datetime.now()
    return ahora.strftime("Son las %H:%M del %d de %B de %Y.")

@mcp.tool()
def abrir_programa(nombre: str) -> str:
    """
    Abre un programa o sitio web en Windows.
    Ejemplo: abrir_programa('notepad') o abrir_programa('https://google.com')
    """
    try:
        # Si parece una URL, abrimos el navegador
        if nombre.startswith("http://") or nombre.startswith("https://"):
            webbrowser.open(nombre)
            return f"Abriendo el sitio web: {nombre}"

        # Diccionario de programas conocidos
        programas = {
            "notepad": "notepad.exe",
            "bloc de notas": "notepad.exe",
            "calculadora": "calc.exe",
            "explorador": "explorer.exe",
            "spotify": "spotify.exe",
            "cmd": "cmd.exe",
            "terminal": "wt.exe",
            "navegador": "start microsoft-edge:",
        }

        # Buscar el programa
        if nombre.lower() in programas:
            subprocess.Popen(programas[nombre.lower()], shell=True)
            return f"Ejecutando {nombre}..."
        else:
            subprocess.Popen(nombre, shell=True)
            return f"Intentando abrir {nombre}..."
    except Exception as e:
        return f"⚠️ No pude abrir {nombre}: {e}"

@mcp.tool()
def buscar_wikipedia(consulta: str, oraciones: int = 2) -> str:
    """Busca un resumen en Wikipedia en español"""
    wikipedia.set_lang("es")
    try:
        resumen = wikipedia.summary(consulta, sentences=oraciones)
        return resumen
    except wikipedia.exceptions.DisambiguationError as e:
        return f"La búsqueda es ambigua. Algunos resultados posibles son: {', '.join(e.options[:5])}"
    except wikipedia.exceptions.PageError:
        return "No encontré resultados para esa búsqueda."
    except Exception as e:
        return f"Error al buscar en Wikipedia: {e}"

@mcp.tool()
def obtener_clima(ciudad: str) -> dict:
    """Obtiene el clima actual y un breve pronóstico de la ciudad indicada"""
    try:
        url = f"https://wttr.in/{ciudad}?format=j1"
        response = requests.get(url, timeout=10)
        data = response.json()

        # Datos actuales
        actual = data["current_condition"][0]
        area = data["nearest_area"][0]["areaName"][0]["value"]
        pais = data["nearest_area"][0]["country"][0]["value"]

        resumen = {
            "ubicacion": f"{area}, {pais}",
            "temperatura_actual_C": actual["temp_C"],
            "sensacion_termica_C": actual["FeelsLikeC"],
            "descripcion": actual["weatherDesc"][0]["value"],
            "humedad_%": actual["humidity"],
            "viento_kmph": actual["windspeedKmph"],
            "direccion_viento": actual["winddir16Point"],
            "presion_hPa": actual["pressure"],
            "visibilidad_km": actual["visibility"],
        }

        # Pronóstico del día actual
        hoy = data["weather"][0]
        resumen["pronostico_hoy"] = {
            "max_temp_C": hoy["maxtempC"],
            "min_temp_C": hoy["mintempC"],
            "uvIndex": hoy["uvIndex"],
            "salida_sol": hoy["astronomy"][0]["sunrise"],
            "puesta_sol": hoy["astronomy"][0]["sunset"],
        }

        return resumen

    except Exception as e:
        return {"error": f"No se pudo obtener el clima: {e}"}

# Configurar la ruta del endpoint MCP
mcp.settings.streamable_http_path = "/mcp"
mcp_app = mcp.streamable_http_app()

if __name__ == "__main__":
    print("🌐 Servidor MCP iniciado en http://localhost:8000/mcp")
    uvicorn.run(mcp_app, host="0.0.0.0", port=8000)