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