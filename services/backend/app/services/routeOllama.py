import requests
import json

def call_ollama (model_name: str, system_prompt: str, user_prompt: str):
    url = "http://localhost:11434/api/chat"

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False,
         "options": {
            "temperature": 0.1,
            "top_p": 0.8,
            "top_k": 20,
            "num_ctx": 8192
        }
    }
    with open("payload.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4, ensure_ascii=False)
    try:
        print("Preguntando a" + model_name)
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("respuesta creada\n")
        content = response.json()
        content = content['message']['content']
        print(content)
        return json.loads(content)
    except Exception as e:
        print(f"Error en Ollama: {e}")
        return {"error": "No se pudo obtener respuesta de la IA"}