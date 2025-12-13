from openai import OpenAI
from dotenv import load_dotenv
import os
import time

# Load il file .env -> so it takes the api key (remember to create it)
load_dotenv()

# Client OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

# Fall back to call if another free model is not available
FREE_MODELS = [
    "mistralai/devstral-2512:free", # Damn Frog Eater from the other side of the Apls
    "nex-agi/deepseek-v3.1-nex-n1:free",
    "openai/gpt-oss-120b:free",
    "google/gemma-3n-e2b-it:free",
    "meta-llama/llama-guard-4-12b:free",
    "openrouter/auto"
]

# 3 tries for models distanced by a 2 second delay each one then fallback to the next one
def narrate(character, state, user_input, retries=3, delay=2):
    """
    Generate the narrative by trying the free models in order.
    If a model fails, try the next one.
    retries: total number of attempts per model in case of rate limiting
    delay: seconds to wait before retrying
    """
    messages = [
        {
            # System prompt defining the role of the AI
            "role": "system",
            "content": (
                "Sei il master di una text adventure fantasy stile D&D. "
                "Descrivi ambienti, PNG ed eventi in modo immersivo. "
                "Non decidere mai al posto del giocatore."
            )
        },
        {
            # Provide character details from character dictionary
            "role": "system",
            "content": f"Scheda personaggio: {character}"
        },
        {
            "role": "system",
            "content": f"Stato avventura: {state}"
        },
        {
            # User input prompt
            "role": "user",
            "content": user_input
        }
    ]

    for model in FREE_MODELS:
        for attempt in range(retries):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=400
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"[WARN] Model {model} failed on attempt {attempt+1}/{retries}: {e}")
                time.sleep(delay)

    return "Il narratore è momentaneamente senza voce. Riprova tra poco."

# --- Test CLI ---
if __name__ == "__main__":
    print("MAIN RUNNING")

    result = narrate(
        character={"nome": "Arin", "classe": "Guerriero"},
        state={"luogo": "Taverna Iniziale", "quest": "Nessuna"},
        user_input="Descrivi una taverna fantasy"
    )

    print("RESULT:")
    print(result)