"""
state.py — Persona 1 (David): gestión del estado de la conversación.

Guarda, para una sesión de chat con un empleado, tres cosas:

- Qué empleado es (perfil, departamento... cargado desde empleados_demo.json
  vía context.obtener_empleado()).
- En qué día de onboarding simulado (1-5) está — el requisito transversal
  del enunciado ("el asistente debe conocer en qué día está el empleado y
  reflejarlo tanto en el chat como en el checklist").
- El historial de turnos recientes, acotado a MAX_TURNOS_HISTORIAL (4),
  para el "historial conversacional acotado (máx. 4 turnos en el prompt)"
  que pide la Parte 2.

No decide NADA sobre qué contenido mostrar (eso es seleccionar_contexto() /
seleccionar_docs_checklist() en context.py, o el prompt en prompts.py);
solo lleva la cuenta de en qué punto está la conversación.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import context

MAX_TURNOS_HISTORIAL = 4
DIAS_VALIDOS = (1, 2, 3, 4, 5)


@dataclass
class Turno:
    pregunta: str
    respuesta: str


@dataclass
class EstadoConversacion:
    empleado: dict
    dia: int = 1
    historial: list[Turno] = field(default_factory=list)

    @property
    def empleado_id(self) -> str:
        return self.empleado["id"]

    @property
    def departamento(self) -> str:
        return self.empleado.get("departamento")

    @property
    def perfil(self) -> str:
        return self.empleado.get("perfil")


def _validar_dia(dia: int) -> None:
    if dia not in DIAS_VALIDOS:
        raise ValueError(f"Día de onboarding fuera de rango (1-5): {dia}")


def crear_estado(empleado_id: str, dia: int = 1) -> EstadoConversacion:
    """Crea el estado inicial de conversación para `empleado_id` (p. ej.
    'emp_01'), cargando el empleado desde empleados_demo.json vía
    context.obtener_empleado(). Lanza ValueError si el día no está en 1-5
    o si el empleado no existe (propagado desde context.obtener_empleado)."""
    empleado = context.obtener_empleado(empleado_id)
    _validar_dia(dia)
    return EstadoConversacion(empleado=empleado, dia=dia)


def avanzar_dia(estado: EstadoConversacion, dia: int) -> EstadoConversacion:
    """Actualiza el día de onboarding simulado (1-5). No borra el historial:
    cambiar de día no es una conversación nueva, solo cambia qué tareas/
    contexto tocan."""
    _validar_dia(dia)
    estado.dia = dia
    return estado


def registrar_turno(estado: EstadoConversacion, pregunta: str, respuesta: str) -> EstadoConversacion:
    """Añade un turno (pregunta + respuesta) al historial y lo recorta a los
    últimos MAX_TURNOS_HISTORIAL, tal como pide el enunciado: 'historial
    conversacional acotado, máx. 4 turnos en el prompt'."""
    estado.historial.append(Turno(pregunta=pregunta, respuesta=respuesta))
    estado.historial = estado.historial[-MAX_TURNOS_HISTORIAL:]
    return estado


def historial_como_texto(estado: EstadoConversacion) -> str:
    """Formatea el historial acotado como texto plano listo para meter en el
    prompt (p. ej. dentro de un delimitador <historial>...</historial> en
    prompts.py). Devuelve cadena vacía si no hay turnos previos."""
    if not estado.historial:
        return ""
    lineas = []
    for turno in estado.historial:
        lineas.append(f"Empleado: {turno.pregunta}")
        lineas.append(f"Asistente: {turno.respuesta}")
    return "\n".join(lineas)


def reiniciar_historial(estado: EstadoConversacion) -> EstadoConversacion:
    """Vacía el historial sin tocar empleado ni día (p. ej. si el equipo
    quiere un botón de 'nueva conversación')."""
    estado.historial = []
    return estado


if __name__ == "__main__":
    estado = crear_estado("emp_01", dia=1)
    print(f"Empleado: {estado.empleado['nombre']} | depto: {estado.departamento} | perfil: {estado.perfil} | día: {estado.dia}")

    registrar_turno(estado, "¿A qué hora empiezo el primer día?", "A las 9:30, con la reunión de bienvenida.")
    registrar_turno(estado, "¿Y mi buddy?", "Te escribe por Slack el día laborable anterior.")
    print("\n--- Historial tras 2 turnos ---")
    print(historial_como_texto(estado))

    for i in range(5):
        registrar_turno(estado, f"Pregunta {i}", f"Respuesta {i}")
    print(f"\nTurnos en historial tras 7 registros (debe ser {MAX_TURNOS_HISTORIAL}): {len(estado.historial)}")

    avanzar_dia(estado, 3)
    print(f"Nuevo día: {estado.dia}")

    try:
        avanzar_dia(estado, 9)
    except ValueError as e:
        print(f"Validación de día fuera de rango OK: {e}")
