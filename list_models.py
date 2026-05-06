import requests
import os
from dotenv import load_dotenv

print("Listing available Gemini models...")
try:
    # 1. Carica le variabili d'ambiente dal file .env (assicurati di avere un file chiamato .env nella stessa cartella)
    load_dotenv()

    gemini_api_key = os.getenv("GEMINI_API_KEY_env")

    # 2. Fai una richiesta GET all'endpoint dei modelli di Gemini
    response = requests.get(
        f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_api_key}",
        timeout=10
    )
    print("Status:", response.status_code)

    # 3. Stampa i modelli disponibili
    data = response.json()
    if "models" in data:
        print("\nAvailable models:")
        for model in data["models"]:
            print(f"  - {model.get('name', 'Unknown')}")
    else:
        print("Response:", data)
except Exception as e:
    print(f"Error: {e}")
