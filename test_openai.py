import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

openaikey = os.getenv("OPENAI_API_KEY_env")

print("Testing OpenAI API client...")
try:
    client = OpenAI(api_key=openaikey)
    print("Client created successfully")
    
    print("Making test API call...")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Say hello"}],
        timeout=10
    )
    print("Response:", response.choices[0].message.content)
except Exception as e:
    print(f"Error: {e}")
