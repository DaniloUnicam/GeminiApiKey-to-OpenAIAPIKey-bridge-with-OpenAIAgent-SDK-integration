import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner
from agents.run import RunConfig

# IMPORTANTE: A seconda della versione dell'SDK OpenAI Agents che stai usando,
# l'importazione di OpenAIChatCompletionsModel potrebbe variare. 
# Di solito si trova qui:
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

# Imposta la domanda da porre all'agente
domanda_da_porre = "What are we discussing now?"

# Specifica il nome dell'agente
agent_name = "Assistant"

# Specifica le istruzioni dell'agente
agent_instructions = "You are a helpful assistant."

# Specifica il modello Gemini da utilizzare
agent_model = "gemini-2.5-flash"

# 1. Carica le variabili d'ambiente dal file .env (assicurati di avere un file chiamato .env nella stessa cartella)
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY_env")

def main():
    if not gemini_api_key:
        raise ValueError("La variabile d'ambiente GEMINI_API_KEY non è impostata nel file .env")

    # 2. Crea un client asincrono per chiamare le API di Google Gemini utilizzando l'endpoint compatibile con OpenAI
    external_client = AsyncOpenAI(
        api_key=gemini_api_key,
        # Endpoint compatibile con OpenAI per accedere a Gemini
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

    # 3. Definisci il wrapper del modello
    model = OpenAIChatCompletionsModel(
        model=agent_model,
        openai_client=external_client
    )

    # 4. Configurazione di esecuzione dell'agente
    config = RunConfig(
        # Passiamo il modello direttamente nella configurazione 
        # per evitare che l'agente tenti di caricarlo come un modello locale, 
        # il che causerebbe un errore 404.
        tracing_disabled=True 
    )

    # 5. Definisci l'agente
    agent = Agent(
        name=agent_name, 
        instructions=agent_instructions, 
        model=model
    )

    # 6. Esegui l'agente
    print("Avvio dell'agente in corso...")
    result = Runner.run_sync(
        agent, 
        domanda_da_porre,
        run_config=config
    )

    # 7. Output finale
    print("\n---------------| Final Output | -------------------")
    print(result.final_output)

if __name__ == "__main__":
    main()