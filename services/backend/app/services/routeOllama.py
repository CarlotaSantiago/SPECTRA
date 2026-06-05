import requests
import json

def call_ollama (model_name: str, system_prompt: str, user_prompt: str, state: int, attempt: int = 1) -> str:
    
    if "ia.drordas.info" in model_name or "." in model_name:
        url = "http://ia.drordas.info:11434/api/chat"
        model_name = model_name.split("/")[-1]
        print(f"Usando modelo remoto: {model_name}")
    else:
        url = f"http://localhost:11434/api/chat"
        print(f"Usando modelo local: {model_name}")


    if state == 1:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {
                "stream": False,
                "temperature": 0.1,
                "top_p": 0.8,
                "max_tokens": 4096
            }
        }
    else:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {
                "stream": False,
                "temperature": 0.1,
                "top_p": 0.8,
                "max_tokens": 4096
            }
        }
    with open(f"payload_vuelta_{attempt}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4, ensure_ascii=False)
    try:
        print("Preguntando a " + model_name)
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("respuesta creada\n")
        content = response.json()
        
        content = content['message']['content'] if content['message']['content'] is not None else content['message']['response']
        print(content)
        return content
    except Exception as e:
        print(f"Error en Ollama: {e}")
        return {"error": "No se pudo obtener respuesta de la IA"}