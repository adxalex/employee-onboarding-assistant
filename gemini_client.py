from google import genai
from google.genai import types

from config import (
    MODELO_PRINCIPAL,
    TEMPERATURE,
    MAX_OUTPUT_TOKENS_CHAT,
    MAX_OUTPUT_TOKENS_CHECKLIST,
)

from gemini_auth import configurar_gemini_api_key


# --------------------------------------------------------
# Inicialización
# --------------------------------------------------------

configurar_gemini_api_key()

client = genai.Client()


# --------------------------------------------------------
# Función interna
# --------------------------------------------------------

def _llamar_modelo(
    prompt: str,
    max_output_tokens: int,
) -> str:
    response = client.models.generate_content(
        model=MODELO_PRINCIPAL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=TEMPERATURE,
            max_output_tokens=max_output_tokens,
        ),
    )

    if response.text:
        return response.text.strip()

    return ""


# --------------------------------------------------------
# API pública
# --------------------------------------------------------

def generar_respuesta_chat(prompt: str) -> str:

    return _llamar_modelo(
        prompt,
        MAX_OUTPUT_TOKENS_CHAT,
    )


def generar_checklist_json(prompt: str) -> str:
    """
    Genera un checklist en formato JSON.

    Devuelve el JSON como texto.
    El parseo a dict se hace posteriormente en logic.py.
    """

    return _llamar_modelo(
        prompt,
        MAX_OUTPUT_TOKENS_CHECKLIST,
    )