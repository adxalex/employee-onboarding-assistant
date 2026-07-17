"""bench_llm.py — Parte 4: cliente LLM multi-proveedor del benchmark.

Por que existe (y no usamos gemini_client de P2 aqui):
- El benchmark necesita comparar proveedores distintos: DeepSeek (barato, para
  test) y Gemini (para la corrida real). gemini_client solo habla con Google.
- Necesitamos el CONTEO REAL de tokens (para el coste y el "que pasa si
  duplicamos el trafico"). gemini_client devuelve solo texto; aqui leemos el
  usage real de cada API.

El prompt sigue viniendo de P1 (context) + P2 (prompts). Esta capa solo se
encarga de ENVIARLO al proveedor elegido y medir.

DeepSeek expone una API compatible con OpenAI -> se usa el SDK `openai` con
base_url distinta. Gemini usa `google-genai`. Cada import es perezoso: solo se
carga la libreria del proveedor que uses.
"""

import os
import time
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()  # carga GEMINI_API_KEY / DEEPSEEK_API_KEY desde .env


@dataclass
class Respuesta:
    """Respuesta normalizada, igual para cualquier proveedor."""
    texto: str
    tokens_entrada: int
    tokens_salida: int
    latencia_s: float


def _llamar_deepseek(prompt, modelo, temperatura):
    from openai import OpenAI  # import perezoso
    cliente = OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com",   # <- lo que hace "OpenAI-compatible" a DeepSeek
    )
    inicio = time.perf_counter()
    r = cliente.chat.completions.create(
        model=modelo,
        temperature=temperatura,
        messages=[{"role": "user", "content": prompt}],
    )
    latencia = time.perf_counter() - inicio
    return Respuesta(
        texto=r.choices[0].message.content,
        tokens_entrada=r.usage.prompt_tokens,       # conteo REAL
        tokens_salida=r.usage.completion_tokens,
        latencia_s=latencia,
    )


def _llamar_gemini(prompt, modelo, temperatura):
    from google import genai            # import perezoso
    from google.genai import types
    cliente = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    inicio = time.perf_counter()
    r = cliente.models.generate_content(
        model=modelo,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=temperatura),
    )
    latencia = time.perf_counter() - inicio
    um = r.usage_metadata
    return Respuesta(
        texto=r.text or "",
        tokens_entrada=um.prompt_token_count,       # conteo REAL
        tokens_salida=um.candidates_token_count,
        latencia_s=latencia,
    )


def generar(prompt, proveedor, modelo, temperatura=0.2):
    """Envia el prompt al proveedor indicado y devuelve una Respuesta normalizada."""
    if proveedor == "deepseek":
        return _llamar_deepseek(prompt, modelo, temperatura)
    if proveedor == "gemini":
        return _llamar_gemini(prompt, modelo, temperatura)
    raise ValueError(f"Proveedor desconocido: {proveedor!r} (usa 'deepseek' o 'gemini')")
