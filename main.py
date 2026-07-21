
"""
main.py — Punto de entrada del Employee Onboarding Assistant (Parte 2).
 
Ejecuta 3 demos que muestran el asistente en funcionamiento de extremo a
extremo (context.py -> state.py -> prompts.py -> gemini_client.py, todo
orquestado por logic.py):
 
  Demo 1: conversación de 1 turno con un empleado dev junior (día 1).
  Demo 2: generación del checklist en JSON para el día 1.
  Demo 3: la MISMA pregunta lanzada a un perfil comercial y a un perfil
          remoto en la UE, para comprobar que el asistente adapta la
          respuesta al perfil/departamento del empleado.
 
Requiere GEMINI_API_KEY en el entorno o en un archivo .env (ver
.env.example). Si no está configurada, gemini_auth.py la pedirá por
consola al importar logic.py.
 
Uso:
    python main.py            # ejecuta las 3 demos
    python main.py 1          # ejecuta solo la demo 1
    python main.py 2          # ejecuta solo la demo 2
    python main.py 3          # ejecuta solo la demo 3
"""
 
from __future__ import annotations
 
import json
import sys
 
import state
 
 
def _separador(titulo: str) -> None:
    print("\n" + "=" * 70)
    print(titulo)
    print("=" * 70)
 
 
def _mostrar_estado(estado: state.EstadoConversacion) -> None:
    emp = estado.empleado
    print(
        f"Empleado: {emp['nombre']}  |  perfil: {emp['perfil']}  |  "
        f"departamento: {emp['departamento']}  |  día: {estado.dia}"
    )
 
 
# ---------------------------------------------------------------------------
# Demo 1 — conversación de 1 turno (empleado dev junior)
# ---------------------------------------------------------------------------
 
def demo_1_chat_dev_junior(logic) -> None:
    _separador("DEMO 1 — Conversación (1 turno) con un dev junior, día 1")
 
    estado = state.crear_estado("emp_01", dia=1)
    _mostrar_estado(estado)
 
    pregunta = "¿A qué hora empieza mi primer día y qué necesito tener activo antes?"
    print(f"\nEmpleado pregunta: {pregunta}")
 
    respuesta = logic.responder_chat(estado, pregunta)
    print(f"\nAsistente responde:\n{respuesta}")
 
 
# ---------------------------------------------------------------------------
# Demo 2 — checklist en JSON para el día 1
# ---------------------------------------------------------------------------
 
def demo_2_checklist_dia1(logic) -> None:
    _separador("DEMO 2 — Checklist en JSON para el día 1")
 
    estado = state.crear_estado("emp_01", dia=1)
    _mostrar_estado(estado)
 
    checklist = logic.generar_checklist(estado)
    print("\nChecklist generado:")
    print(json.dumps(checklist, ensure_ascii=False, indent=2))
 
 
# ---------------------------------------------------------------------------
# Demo 3 — mismo mensaje, comercial vs remoto UE
# ---------------------------------------------------------------------------
 
def demo_3_comparacion_perfiles(logic) -> None:
    _separador("DEMO 3 — Misma pregunta, perfil comercial vs remoto UE")
 
    pregunta = "¿Qué debo hacer en mi primer día y a quién contacto si tengo dudas?"
    print(f"Pregunta (idéntica para ambos): {pregunta}")
 
    print("\n--- Perfil comercial (Sales) ---")
    estado_comercial = state.crear_estado("emp_02", dia=1)
    _mostrar_estado(estado_comercial)
    respuesta_comercial = logic.responder_chat(estado_comercial, pregunta)
    print(f"\nAsistente responde:\n{respuesta_comercial}")
 
    print("\n--- Perfil remoto UE (Engineering, Lisboa) ---")
    estado_remoto = state.crear_estado("emp_03", dia=1)
    _mostrar_estado(estado_remoto)
    respuesta_remoto = logic.responder_chat(estado_remoto, pregunta)
    print(f"\nAsistente responde:\n{respuesta_remoto}")
 
    print(
        "\n(Compara ambas respuestas: deberían diferir en tono, herramientas "
        "y contexto citado según el departamento/perfil de cada empleado.)"
    )
 
 
# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------
 
DEMOS = {
    "1": demo_1_chat_dev_junior,
    "2": demo_2_checklist_dia1,
    "3": demo_3_comparacion_perfiles,
}
 
 
def main() -> None:
    try:
        import logic
    except Exception as exc:  # noqa: BLE001 - queremos un mensaje claro para el usuario
        print("No se pudo inicializar el asistente (revisa GEMINI_API_KEY / .env).")
        print(f"Detalle: {exc}")
        sys.exit(1)
 
    seleccion = sys.argv[1] if len(sys.argv) > 1 else None
 
    demos_a_ejecutar = [DEMOS[seleccion]] if seleccion in DEMOS else DEMOS.values()
 
    for demo in demos_a_ejecutar:
        try:
            demo(logic)
        except Exception as exc:  # noqa: BLE001 - una demo no debe tumbar las demás
            print(f"\n[Error ejecutando {demo.__name__}]: {exc}")
 
 
if __name__ == "__main__":
    main()