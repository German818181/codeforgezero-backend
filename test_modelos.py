import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("Buscando modelos compatibles...")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"Nombre: {m.name} | Descripción: {m.display_name}")