"""list_modelos.py — muestra los modelos Gemini que TU cuenta puede usar.

Ejecuta:  python list_modelos.py
Copia los 2 que quieras comparar en GEMINI_MODELS del .env.
"""
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
cliente = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

print("Modelos que soportan generateContent (usables en el benchmark):\n")
for m in cliente.models.list():
    acciones = getattr(m, "supported_actions", None) or []
    if "generateContent" in acciones:
        # el nombre viene como "models/gemini-2.5-flash" -> quitamos el prefijo
        print("  ", m.name.replace("models/", ""))
