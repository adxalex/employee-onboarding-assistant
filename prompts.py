"""
prompts.py — construcción dinámica de prompts para el Employee Onboarding Assistant.

Este módulo NO llama al modelo y NO selecciona contexto.
Solo transforma la información recibida (empleado, docs, FAQ, historial...)
en prompts claros y acotados para Gemini.

Entradas esperadas:
- empleado: dict de empleados_demo.json (vía state/context).
- docs: lista de documentos ya seleccionados por context.seleccionar_contexto()
  o context.seleccionar_docs_checklist().
- faqs: lista de FAQ ya seleccionadas por context.seleccionar_contexto().
- historial: texto ya formateado por state.historial_como_texto().
- fragmento_dia: texto específico del día extraído por
  context.seleccionar_docs_checklist().
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Formateo de contexto
# ---------------------------------------------------------------------------

def _formatear_empleado(empleado: dict, dia: int) -> str:
    """Bloque compacto con el perfil del empleado."""

    return f"""
ID: {empleado.get("id")}
Nombre: {empleado.get("nombre")}
Rol: {empleado.get("rol")}
Departamento: {empleado.get("departamento")}
Perfil: {empleado.get("perfil")}
Modalidad: {empleado.get("modalidad")}
Ubicación: {empleado.get("ubicacion")}
Idioma preferido: {empleado.get("idioma_preferido")}
Manager: {empleado.get("manager")}
Día de onboarding: {dia}
""".strip()


def _formatear_docs(docs: list[dict]) -> str:
    """Convierte los documentos seleccionados en un bloque legible para el LLM."""

    if not docs:
        return "No hay documentos relevantes."

    bloques = []

    for doc in docs:
        bloques.append(
            f"""
[{doc.get("id")}]

Título: {doc.get("titulo")}
Departamento: {doc.get("departamento")}

Contenido:
{doc.get("cuerpo", "")}
""".strip()
        )

    return "\n\n---\n\n".join(bloques)


def _formatear_faqs(faqs: list[dict]) -> str:
    """Convierte las FAQ seleccionadas en un bloque compacto."""

    if not faqs:
        return "No hay FAQ relevantes."

    bloques = []

    for faq in faqs:
        bloques.append(
            f"""
[{faq.get("id")}]

Pregunta:
{faq.get("pregunta")}

Respuesta corta:
{faq.get("respuesta_corta")}

Documento relacionado:
{faq.get("doc_id")}
""".strip()
        )

    return "\n\n---\n\n".join(bloques)


# ---------------------------------------------------------------------------
# Prompt de conversación
# ---------------------------------------------------------------------------

def construir_prompt_chat(
    empleado: dict,
    dia: int,
    pregunta: str,
    docs: list[dict],
    faqs: list[dict],
    historial: str = "",
) -> str:
    """
    Construye el prompt para el modo conversación.

    El contexto YA viene filtrado por context.seleccionar_contexto().
    El historial YA viene recortado y formateado por state.historial_como_texto().
    """

    empleado_txt = _formatear_empleado(empleado, dia)
    docs_txt = _formatear_docs(docs)
    faqs_txt = _formatear_faqs(faqs)
    historial_txt = historial.strip() or "Sin historial previo."

    return f"""
Eres el Employee Onboarding Assistant de Bridge SA.

Tu misión es ayudar EXCLUSIVAMENTE a empleados nuevos durante sus primeros días.

REGLAS OBLIGATORIAS:
- Usa únicamente la información incluida en <documentos> y <faqs>.
- Si algo no aparece en el contexto, dilo claramente.
- No inventes políticas, fechas, cifras ni procedimientos.
- No compartas información de otros empleados.
- Mantén un tono cercano, profesional y útil.
- Adapta la respuesta al perfil del empleado y al día de onboarding.
- Responde en español salvo que el empleado pida otro idioma.

<empleado>
{empleado_txt}
</empleado>

<documentos>
{docs_txt}
</documentos>

<faqs>
{faqs_txt}
</faqs>

<historial>
{historial_txt}
</historial>

<pregunta_actual>
{pregunta}
</pregunta_actual>

Instrucciones finales:
- Prioriza la información de los documentos frente a las FAQ si hubiera conflicto.
- Sé breve (3-8 frases normalmente).
- Si el empleado está en día 1, prioriza accesos, bienvenida y primeros pasos.
- Si está en día 3 o superior, evita repetir tareas ya propias del día 1.
""".strip()


# ---------------------------------------------------------------------------
# Prompt de checklist
# ---------------------------------------------------------------------------

def construir_prompt_checklist(
    empleado: dict,
    dia: int,
    docs: list[dict],
    fragmento_dia: str | None = None,
) -> str:
    """
    Construye el prompt para generar el checklist JSON.

    El contexto YA viene seleccionado por context.seleccionar_docs_checklist().
    Si existe fragmento_dia, contiene únicamente el texto del día actual.
    """

    empleado_txt = _formatear_empleado(empleado, dia)
    docs_txt = _formatear_docs(docs)

    contexto_dia = (
        fragmento_dia.strip()
        if fragmento_dia
        else "No hay un fragmento específico del día; usa los documentos proporcionados."
    )

    return f"""
Eres el Employee Onboarding Assistant de Bridge SA.

Tu tarea es generar el plan del día de onboarding para un empleado nuevo.

IMPORTANTE:
- Usa SOLO la información del contexto.
- No inventes tareas.
- No añadas explicaciones.
- Devuelve EXCLUSIVAMENTE un JSON válido.
- No uses Markdown.
- No escribas texto antes ni después del JSON.

La estructura debe ser EXACTAMENTE:

{{
  "empleado_id": "...",
  "dia": 1,
  "tareas": [
    {{
      "id": "t01",
      "titulo": "...",
      "completada": false,
      "fuente_doc": "doc_xxx"
    }}
  ],
  "mensaje_resumen": "..."
}}

<empleado>
{empleado_txt}
</empleado>

<contexto_del_dia>
{contexto_dia}
</contexto_del_dia>

<documentos_fuente>
{docs_txt}
</documentos_fuente>

Genera entre 3 y 6 tareas concretas y accionables para el día {dia}.

Cada tarea debe:
- empezar con un verbo (Unirse, Asistir, Configurar, Revisar, Contactar...),
- ser específica,
- incluir una única acción principal,
- usar como fuente_doc el id de uno de los documentos proporcionados.

El mensaje_resumen debe ser una frase corta orientativa para ese día.
""".strip()