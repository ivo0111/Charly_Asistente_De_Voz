# Charly — Asistente de voz local

## Descripción

**Charly** es un asistente de voz local e inteligente que escucha, entiende, razona con herramientas y responde por voz.

### Arquitectura principal
-  **Entrada de voz → STT** (Whisper, Faster-Whisper o SpeechRecognition)
-  **LLM local** vía [Ollama](https://ollama.com) (modelos como `llama3`, `qwen`, etc.)
-  **Herramientas externas** mediante [FastMCP](https://github.com/modelcontextprotocol/fastmcp)
-  **Respuesta hablada → TTS** con [Coqui TTS](https://github.com/coqui-ai/TTS)

El asistente puede ejecutar acciones locales, consultar APIs, obtener clima, abrir programas, entre muchas otras cosas — sin depender de la nube ni de sistemas con créditos limitados.

---

## Tecnologías utilizadas

| Componente | Tecnología |
|-------------|-------------|
| Reconocimiento de voz (STT) | `speech_recognition`, `faster-whisper` |
| Modelo de lenguaje | Ollama (Llama3, Qwen, etc.) |
| Síntesis de voz (TTS) | Coqui TTS |
| Ejecución de herramientas | FastMCP |
| Comunicación HTTP | `requests`, `uvicorn` |
| Audio | `sounddevice`, `numpy` |
| Clima | API pública [wttr.in](https://wttr.in) |
| Otros | `wikipedia`, `datetime`, `subprocess`, `webbrowser` |

---

## Estructura del proyecto
├── assistant_charly.py # Asistente principal (voz, IA, TTS, STT, MCP)

├── mcp_server.py # Servidor MCP con herramientas locales

├── requirements.txt # Dependencias de Python

└── README.md # Este archivo

## Diseño del sistema

Charly sigue una arquitectura modular:
```scss
[Micrófono] → STT → LLM (Ollama) → MCP Tools → LLM → TTS → [Altavoz]
```

- STT: convierte voz a texto.
- LLM: analiza y genera plan de acción (prompt → herramienta → resultado).
- MCP: ejecuta funciones reales del sistema.
- TTS: genera voz natural con Coqui.
- Output: respuesta hablada en tiempo real.

---

## Requisitos previos (Windows 11)

1. **Python 3.10+** instalado (y agregado a PATH)
2. **Ollama** instalado y corriendo → [https://ollama.com](https://ollama.com)
3. **Micrófono funcional** con permisos en Windows

---

## Instalación

### Clonar el repositorio
```powershell
git clone https://github.com/ivo0111/Charly_Asistente_De_Voz.git
cd charly
```
### Crear entorno virtual
```powershell
python -m venv venv
.\venv\Scripts\activate
python -m pip install --upgrade pip
```

### Instalar dependencias
```powershell
pip install -r requirements.txt
```
Si usás GPU, instalá la versión adecuada de torch y torchaudio desde https://pytorch.org.

## Instalación y configuración del modelo local (Ollama)

### Instalar Ollama
Descargá e instalá Ollama desde su sitio oficial:
[https://ollama.com/download](https://ollama.com/download)

Una vez instalado, abrí una terminal (PowerShell o CMD) y verificá que funcione correctamente:

```bash
ollama run llama3
```

Si Ollama está instalado correctamente, verás algo como:

> Hello!

Presioná Ctrl + C para salir.

### Descargar el modelo que vas a usar

Podés usar cualquiera de los siguientes modelos locales, según tus recursos:

| Modelo	| Tamaño aprox.	| Comando para descargar |
|------------|---------------|------------------------|
| Llama 3 (recomendado) |	4.7 GB | ollama pull llama3 |
| Qwen 2.5 (3B)	| 2.9 GB	| ollama pull qwen2.5:3b |
| Mistral	| 4.1 GB	| ollama pull mistral |
| Gemma 2 (2B)	| 2.6 GB	| ollama pull gemma2:2b |

### Verificar los modelos instalados

Usá este comando para listar los modelos descargados:

```bash
ollama list
```

Ejemplo de salida:

```makefile
NAME        ID        SIZE      MODIFIED
llama3      9f6b1...  4.7 GB    2 days ago
qwen2.5:3b  12ac3...  2.9 GB    1 day ago
```

### Iniciar el servidor de Ollama

Ollama corre automáticamente como servicio local en:

>http://localhost:11434

Si necesitás iniciarlo manualmente, ejecutá:

```bash
ollama serve
```

### Probar el modelo con una consulta

Podés hacer una prueba rápida para verificar que responde correctamente:

```bash
curl http://localhost:11434/api/generate -d "{\"model\": \"llama3\", \"prompt\": \"Hola, ¿cómo estás?\"}"
```

Deberías recibir una respuesta en formato JSON similar a:

```json
{
  "model": "llama3",
  "created_at": "2025-11-03T14:20:12Z",
  "response": "¡Hola! Estoy listo para ayudarte.",
  "done": true
}
```

### Configurar tu proyecto para usar Ollama

Asegurate de que tu asistente apunte a la URL local del servidor Ollama:

```python
# sistant_charly.py
OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO = "llama3"
```

Luego podrás hacer peticiones desde tu asistente o servidor Flask, por ejemplo:

```python
payload = {
    "model": MODELO,
    "prompt": "Explica brevemente qué es la inteligencia artificial."
}
response = requests.post(OLLAMA_URL, json=payload)
print(response.json()["response"])
```

✅ Con esto, tu modelo local estará completamente operativo y listo para integrarse con el asistente Charly.

## Cómo ejecutar el proyecto
### Iniciar el servidor MCP
```powershell
.\venv\Scripts\activate
python mcp_server.py
```

Debería ver un mensaje:
Servidor MCP iniciado en http://localhost:8000/mcp

Podés probarlo con:
```powershell
curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"hora_actual\",\"params\":{}}"`
```

### Iniciar el asistente de voz
```powershell
python assistant_charly.py
```
Luego de escuchar el mensaje de inicio, probá decir:

- “Charly, ¿qué hora es?”
- “Charly, buscá en Wikipedia a Albert Einstein.”
- “Charly, abrí el bloc de notas.”
- “Charly, cómo está el clima en Mendoza.”

## Herramientas disponibles (FastMCP)

| Herramienta | Descripción | Ejemplo de uso |
|---------------|---------------|---------------|
| prueba(number) | Función de ejemplo matemática | <mcp>{"tool":"prueba","args":{"number":8}}</mcp> |
| hora_actual() | Hora y fecha actuales | <mcp>{"tool":"hora_actual","args":{}} |
| abrir_programa(nombre)	 | Abre programas o URLs | <mcp>{"tool":"abrir_programa","args":{"nombre":"notepad"}} |
| buscar_wikipedia(consulta) | Devuelve resumen de Wikipedia en español | <mcp>{"tool":"buscar_wikipedia","args":{"consulta":"Python"}} |
| obtener_clima(ciudad) | Usa https://wttr.in/{ciudad}?format=j1 para obtener clima resumido | <mcp>{"tool":"obtener_clima","args":{"ciudad":"Madrid"}} |