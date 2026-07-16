"""benchmark.py — Parte 4 · MODO INTEGRACION MULTI-PROVEEDOR (paso 5)

Corre el dataset usando el asistente REAL de tus companeros para construir el
prompt (context P1 + prompts P2) y lo envia a un proveedor via bench_llm:
    - "deepseek" -> barato, para pruebas.
    - "gemini"   -> para la corrida real / entregable.

El proveedor activo se elige con BENCH_PROVIDER (.env) o la constante PROVEEDOR.

Decisiones de diseno:
- NO usa logic.py (muta historial + bug de firma docs/documentos). Orquestamos
  los bloques directamente para que cada caso sea independiente.
- El prompt se construye UNA vez por caso y se envia IGUAL a los 2 modelos
  (mismas condiciones: lo unico que cambia es el modelo).
- Los tokens y la latencia son REALES (los da bench_llm desde cada API).
"""

import os
import json
import csv
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

import context
import state
import prompts
import bench_llm

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATASET_PATH = DATA_DIR / "dataset_benchmark.json"
OUTPUT_DIR = BASE_DIR / "output"

# QUE correr, elegido en .env: BENCH_MODE = "deepseek" | "gemini" | "ambos".
BENCH_MODE = os.getenv("BENCH_MODE", "deepseek")

# Los 2 modelos de cada proveedor a comparar (configurables en .env, separados por coma).
def _lista_modelos(env_var, defecto):
    valor = os.getenv(env_var)
    return [m.strip() for m in valor.split(",") if m.strip()] if valor else defecto

MODELOS_GEMINI = _lista_modelos("GEMINI_MODELS", ["gemini-2.5-flash", "gemini-2.5-pro"])
MODELOS_DEEPSEEK = _lista_modelos("DEEPSEEK_MODELS", ["deepseek-chat", "deepseek-reasoner"])


def combinaciones(modo):
    """Devuelve la lista de (proveedor, modelo) a ejecutar segun BENCH_MODE.
    - "gemini"   -> 2 modelos Gemini
    - "deepseek" -> 2 modelos DeepSeek
    - "ambos"    -> los 4 (estudio cross-proveedor, opcional del enunciado)
    """
    combos = []
    if modo in ("gemini", "ambos"):
        combos += [("gemini", m) for m in MODELOS_GEMINI]
    if modo in ("deepseek", "ambos"):
        combos += [("deepseek", m) for m in MODELOS_DEEPSEEK]
    if not combos:
        raise ValueError(f"BENCH_MODE invalido: {modo!r} (usa deepseek | gemini | ambos)")
    return combos


# Lista de ejecuciones: cada elemento es un par (proveedor, modelo).
EJECUCIONES = combinaciones(BENCH_MODE)

# Condicion controlada: MISMA temperatura para todos los modelos.
TEMPERATURA = 0.2


def cargar_casos():
    with open(DATASET_PATH, encoding="utf-8") as f:
        return json.load(f)["casos"]


def preparar_peticion(caso):
    """
    Construye el prompt para un caso con el asistente real (P1+P2).
    NO llama al modelo -> el prompt es identico para todos los modelos.
    Devuelve: (prompt, tipo)  con tipo in {"chat","checklist"}.
    """
    estado = state.crear_estado(caso["empleado_id"], dia=caso["dia"])

    if caso["formato"] == "checklist":
        ctx = context.seleccionar_docs_checklist(empleado=estado.empleado, dia=estado.dia)
        prompt = prompts.construir_prompt_checklist(
            empleado=estado.empleado, dia=estado.dia,
            docs=ctx["docs"], fragmento_dia=ctx["fragmento_dia"],
        )
        return prompt, "checklist"

    ctx = context.seleccionar_contexto(caso["pregunta"], estado.empleado)
    prompt = prompts.construir_prompt_chat(
        empleado=estado.empleado, dia=estado.dia, pregunta=caso["pregunta"],
        docs=ctx["docs"], faqs=ctx["faqs"], historial="",
    )
    return prompt, "chat"


def ejecutar_benchmark():
    casos = cargar_casos()
    resultados = []
    for caso in casos:
        prompt, _tipo = preparar_peticion(caso)          # 1 prompt por caso
        for proveedor, modelo in EJECUCIONES:             # mismo prompt, N (proveedor,modelo)
            try:
                r = bench_llm.generar(prompt, proveedor, modelo, TEMPERATURA)
                fila = {
                    "latencia_ms": round(r.latencia_s * 1000, 1),
                    "tokens_entrada": r.tokens_entrada, "tokens_salida": r.tokens_salida,
                    "tokens_total": r.tokens_entrada + r.tokens_salida,
                    "respuesta": r.texto, "error": "",
                }
                print(f"  {caso['id']:<10}{modelo:<22}{fila['latencia_ms']:>8}ms  "
                      f"tok {r.tokens_entrada}+{r.tokens_salida}")
            except Exception as e:
                # Un modelo caido (404, limite, red...) NO debe tumbar todo el benchmark.
                fila = {"latencia_ms": 0, "tokens_entrada": 0, "tokens_salida": 0,
                        "tokens_total": 0, "respuesta": "", "error": f"{type(e).__name__}: {e}"}
                print(f"  {caso['id']:<10}{modelo:<22}  ERROR: {type(e).__name__}")
            resultados.append({
                "id_caso": caso["id"], "tipo": caso["tipo"], "formato": caso["formato"],
                "proveedor": proveedor, "modelo": modelo,
                "comportamiento_esperado": caso["comportamiento_esperado"], **fila,
            })
    return resultados


def guardar_resultados(resultados):
    """
    Dos salidas con proposito distinto:
      - CSV  = solo METRICAS (para Excel y la matriz de decision). SIN la respuesta,
               que la volveria ilegible.
      - JSON = resultado COMPLETO (incluye la respuesta del modelo) para la
               evaluacion del paso 3 y para trazabilidad.
    """
    OUTPUT_DIR.mkdir(exist_ok=True)
    sello = datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta_csv = OUTPUT_DIR / f"benchmark_{BENCH_MODE}_{sello}.csv"
    ruta_json = OUTPUT_DIR / f"benchmark_{BENCH_MODE}_{sello}.json"

    # CSV: metricas, sin la columna "respuesta".
    columnas_csv = ["id_caso", "tipo", "formato", "proveedor", "modelo",
                    "comportamiento_esperado", "latencia_ms", "tokens_entrada",
                    "tokens_salida", "tokens_total", "error"]
    with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
        # extrasaction="ignore" -> ignora la clave "respuesta" que no esta en columnas_csv
        w = csv.DictWriter(f, fieldnames=columnas_csv, extrasaction="ignore")
        w.writeheader(); w.writerows(resultados)

    # JSON: todo, incluida la respuesta completa.
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    return ruta_csv, ruta_json


def main():
    print(f"Benchmark | modo={BENCH_MODE} | ejecuciones={EJECUCIONES} | temp={TEMPERATURA}\n")
    resultados = ejecutar_benchmark()
    ruta_csv, ruta_json = guardar_resultados(resultados)
    print(f"\nReportes guardados en:\n  {ruta_csv}\n  {ruta_json}")
    print(f"Total: {len(resultados)} ejecuciones "
          f"({len(resultados)//len(EJECUCIONES)} casos x {len(EJECUCIONES)} modelos)")


if __name__ == "__main__":
    main()
