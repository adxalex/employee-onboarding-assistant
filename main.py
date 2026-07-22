"""
main.py — Punto de entrada del Employee Onboarding Assistant.

Ejecuta demos que prueban CADA PARTE del proyecto de extremo a extremo:

  Demo 1 — Chat (P1+P2): conversacion de 1 turno, dev junior, dia 1.
  Demo 2 — Checklist (P1+P2): plan del dia 1 en JSON estructurado.
  Demo 3 — Perfiles (P1+P2): la MISMA pregunta a comercial vs remoto UE.
  Demo 4 — Dia de onboarding (requisito transversal): dia 1 vs dia 3.
  Demo 5 — Robustez (P3): mismo input malicioso en modo VULNERABLE vs SEGURO.

La Parte 4 (benchmark) se corre aparte con:  python benchmark.py

Flujo interno de cada demo de chat/checklist:
    state -> context (P1) -> prompts (P2) -> gemini_client (P2), via logic.py

Requiere GEMINI_API_KEY en .env (ver .env.example).

Uso:
    python main.py           # todas las demos
    python main.py 1         # solo la demo 1
    python main.py 5         # solo la demo 5
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import state


# ---------------------------------------------------------------------------
# Utilidades de presentacion
# ---------------------------------------------------------------------------

def _separador(titulo: str) -> None:
    print("\n" + "=" * 72)
    print(titulo)
    print("=" * 72)


def _mostrar_estado(estado: state.EstadoConversacion) -> None:
    emp = estado.empleado
    print(f"Empleado: {emp['nombre']} | perfil: {emp['perfil']} | "
          f"depto: {emp['departamento']} | dia: {estado.dia}")


# ---------------------------------------------------------------------------
# Demo 1 — Chat (1 turno, dev junior, dia 1)
# ---------------------------------------------------------------------------

def demo_1_chat(logic) -> None:
    _separador("DEMO 1 — Chat: dev junior, dia 1")
    estado = state.crear_estado("emp_02", dia=3)
    _mostrar_estado(estado)

    #pregunta = "¿A que hora empieza mi primer dia y que necesito tener activo antes?"
    pregunta = "¿cual es el sueldo de mi jefe?"
    print(f"\nPregunta: {pregunta}")
    print(f"\nRespuesta:\n{logic.responder_chat(estado, pregunta)}")


# ---------------------------------------------------------------------------
# Demo 2 — Checklist JSON (dia 1)
# ---------------------------------------------------------------------------

def demo_2_checklist(logic) -> None:
    _separador("DEMO 2 — Checklist JSON: dia 1")
    estado = state.crear_estado("emp_04", dia=2)
    _mostrar_estado(estado)

    checklist = logic.generar_checklist(estado)
    print("\nChecklist generado:")
    print(json.dumps(checklist, ensure_ascii=False, indent=2))

    # Verificacion rapida del formato exigido por el enunciado.
    campos = ("empleado_id", "dia", "tareas", "mensaje_resumen")
    faltan = [c for c in campos if c not in checklist]
    print("\nCampos obligatorios:", "OK" if not faltan else f"FALTAN {faltan}")


# ---------------------------------------------------------------------------
# Demo 3 — Adaptacion al perfil (comercial vs remoto UE)
# ---------------------------------------------------------------------------

def demo_3_perfiles(logic) -> None:
    _separador("DEMO 3 — Misma pregunta: comercial vs remoto UE")
    pregunta = "¿Que debo hacer en mi primer dia y a quien contacto si tengo dudas?"
    print(f"Pregunta identica para ambos: {pregunta}")

    for emp_id, etiqueta in (("emp_02", "COMERCIAL (Sales)"),
                             ("emp_03", "REMOTO UE (Engineering, Lisboa)")):
        print(f"\n--- {etiqueta} ---")
        estado = state.crear_estado(emp_id, dia=1)
        _mostrar_estado(estado)
        print(f"\nRespuesta:\n{logic.responder_chat(estado, pregunta)}")

    print("\n(Deben diferir en tono, herramientas citadas y contexto segun el perfil.)")


# ---------------------------------------------------------------------------
# Demo 4 — Dia de onboarding (requisito transversal): dia 1 vs dia 3
# ---------------------------------------------------------------------------

def demo_4_dias(logic) -> None:
    _separador("DEMO 4 — Requisito transversal: dia 1 vs dia 3 (mismo empleado)")
    pregunta = "¿Que me toca hacer hoy?"
    print(f"Pregunta identica: {pregunta}")

    for dia in (1, 3):
        print(f"\n--- DIA {dia} ---")
        estado = state.crear_estado("emp_01", dia=dia)
        _mostrar_estado(estado)
        print(f"\nRespuesta:\n{logic.responder_chat(estado, pregunta)}")

    print("\n(El dia 3 NO debe repetir tareas de accesos propias del dia 1.)")


# ---------------------------------------------------------------------------
# Demo 5 — Robustez (P3): vulnerable vs seguro con el MISMO input
# ---------------------------------------------------------------------------

def demo_5_robustez(logic, caso_id=None) -> None:
    _separador("DEMO 5 — Robustez: modo VULNERABLE vs SEGURO (casos trampa reales)")
    try:
        import validators
    except Exception as exc:
        print(f"No se pudo importar validators.py (Parte 3): {exc}")
        return

    # Cargamos los casos trampa REALES de Jose (Parte 3), no un ataque a mano.
    ruta = Path("data") / "casos_trampa.json"
    with open(ruta, encoding="utf-8") as f:
        casos = json.load(f)

    # Elegimos el caso: por id (2º parámetro de la CLI) o el primero por defecto.
    if caso_id:
        caso = next((c for c in casos if c["id"] == caso_id), None)
        if caso is None:
            print(f"No existe el caso '{caso_id}'. Disponibles:")
            for c in casos:
                print(f"  {c['id']}  ({c['tipo']})")
            return
    else:
        caso = casos[1]

    ataque = caso["mensaje"]
    print(f"Caso: {caso['id']}  ·  tipo: {caso['tipo']}")
    print(f"Input malicioso: {ataque}")
    print(f"Esperado (modo seguro): {caso.get('comportamiento_esperado_modo_seguro', '-')}\n")

    estado = state.crear_estado("emp_02", dia=2)

    # --- MODO VULNERABLE: se llama al modelo SIN validar ---
    print("--- MODO VULNERABLE (sin validacion, llama al modelo) ---")
    print(logic.responder_chat(estado, ataque))

    # --- MODO SEGURO: se valida ANTES; si falla, no se llama al modelo ---
    print("\n--- MODO SEGURO (fail-closed: valida antes de gastar la llamada) ---")
    resultado = validators.validar_entrada(ataque)
    if not resultado.ok:
        print(f"BLOQUEADO sin llamar al modelo | motivo: {resultado.motivo}")
        print(f"Mensaje al empleado: {resultado.mensaje_usuario}")
    else:
        print("La validacion dejo pasar la entrada; respuesta del modelo:")
        print(logic.responder_chat(estado, ataque))

    # --- Cobertura: veredicto del validador sobre los 12 casos (gratis, sin API) ---
    print("\n--- Cobertura del validador sobre los 12 casos trampa (sin llamar al modelo) ---")
    for c in casos:
        v = validators.validar_entrada(c["mensaje"])
        print(f"  {c['id']:<26} {c['tipo']:<14} -> {'BLOQUEA' if not v.ok else 'DEJA PASAR'}")


# ---------------------------------------------------------------------------
# Orquestacion
# ---------------------------------------------------------------------------

DEMOS = {
    "1": demo_1_chat,
    "2": demo_2_checklist,
    "3": demo_3_perfiles,
    "4": demo_4_dias,
    "5": demo_5_robustez,
}


def main() -> None:
    try:
        import logic
    except Exception as exc:
        print("No se pudo inicializar el asistente (revisa GEMINI_API_KEY / .env).")
        print(f"Detalle: {exc}")
        sys.exit(1)

    seleccion = sys.argv[1] if len(sys.argv) > 1 else None
    caso_id = sys.argv[2] if len(sys.argv) > 2 else None   # 2º arg: id de caso trampa (demo 5)
    if seleccion and seleccion not in DEMOS:
        print(f"Demo desconocida: {seleccion}. Usa una de {list(DEMOS)} o ninguna para todas.")
        sys.exit(1)

    a_ejecutar = [DEMOS[seleccion]] if seleccion else list(DEMOS.values())

    for demo in a_ejecutar:
        try:
            if demo is demo_5_robustez:
                demo(logic, caso_id)          # la demo 5 acepta un id de caso opcional
            else:
                demo(logic)
        except Exception as exc:   # una demo que falle no debe tumbar las demas
            print(f"\n[Error en {demo.__name__}]: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
