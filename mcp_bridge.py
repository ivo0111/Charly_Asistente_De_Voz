import requests
import json

MCP_URL = "http://localhost:8000/mcp"

def call_mcp_tool(tool_name: str, **kwargs):
    """
    Llama a una herramienta MCP a través del endpoint HTTP.
    """
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": tool_name,
            "params": kwargs
        }
        response = requests.post(MCP_URL, json=payload, timeout=10)
        response.raise_for_status()

        data = response.json()
        if "result" in data:
            return data["result"]
        elif "error" in data:
            return f"Error del servidor MCP: {data['error']}"
        else:
            return f"Respuesta inesperada: {data}"

    except Exception as e:
        return f"Error llamando a MCP: {e}"
