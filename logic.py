"""
logic.py

Orquestador principal del Employee Onboarding Assistant.

Responsabilidades:
- Obtener el contexto adecuado.
- Construir el prompt.
- Llamar al modelo.
- Actualizar el estado de la conversación.
"""

import json

import context
import state

from prompts import (
    construir_prompt_chat,
    construir_prompt_checklist,
)

from gemini_client import (
    generar_respuesta_chat,
    generar_checklist_json,
)


# ----------------------------------------------------------------------
# CHAT
# ----------------------------------------------------------------------

def responder_chat(
    estado: state.EstadoConversacion,
    pregunta: str,
) -> str:
    """
    Genera una respuesta para el chat.

    Args:
        estado:
            Estado actual de la conversación.

        pregunta:
            Pregunta del empleado.

    Returns:
        Respuesta generada por Gemini.
    """

    # Seleccionar contexto
    resultado_contexto = context.seleccionar_contexto(
        pregunta=pregunta,
        empleado=estado.empleado,
    )

    # Historial formateado
    historial = state.historial_como_texto(estado)

    # Construcción del prompt
    prompt = construir_prompt_chat(
        empleado=estado.empleado,
        dia=estado.dia,
        pregunta=pregunta,
        documentos=resultado_contexto["docs"],
        faqs=resultado_contexto["faqs"],
        historial=historial,
    )

    # Llamada al modelo
    respuesta = generar_respuesta_chat(prompt)

    # Guardar conversación
    state.registrar_turno(
        estado,
        pregunta,
        respuesta,
    )

    return respuesta


# ----------------------------------------------------------------------
# CHECKLIST
# ----------------------------------------------------------------------

def generar_checklist(
    estado: state.EstadoConversacion,
) -> dict:
    """
    Genera el checklist del día actual.

    Args:
        estado:
            Estado del empleado.

    Returns:
        Diccionario Python con el checklist.
    """

    resultado = context.seleccionar_docs_checklist(
        empleado=estado.empleado,
        dia=estado.dia,
    )

    prompt = construir_prompt_checklist(
        empleado=estado.empleado,
        dia=estado.dia,
        documentos=resultado["docs"],
        fragmento_dia=resultado["fragmento_dia"],
    )

    respuesta = generar_checklist_json(prompt)

    try:
        return json.loads(respuesta)

    except json.JSONDecodeError:

        return {
            "error": "Gemini no devolvió un JSON válido.",
            "respuesta_modelo": respuesta,
        }


# ----------------------------------------------------------------------
# CAMBIO DE DÍA
# ----------------------------------------------------------------------

def cambiar_dia(
    estado: state.EstadoConversacion,
    nuevo_dia: int,
) -> None:
    """
    Cambia el día de onboarding.
    """

    state.avanzar_dia(
        estado,
        nuevo_dia,
    )


# ----------------------------------------------------------------------
# NUEVA CONVERSACIÓN
# ----------------------------------------------------------------------

def reiniciar_chat(
    estado: state.EstadoConversacion,
) -> None:
    """
    Elimina el historial manteniendo empleado y día.
    """

    state.reiniciar_historial(estado)