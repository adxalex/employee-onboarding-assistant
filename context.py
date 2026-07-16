"""
context.py — Persona 1: Arquitecto del Contexto y Datos.

Carga los datos de data/ (documentos de onboarding, FAQ, empresa, empleados
demo) y expone dos funciones de selección de contexto que usará el resto del
asistente (logic.py / prompts.py):

- seleccionar_contexto(pregunta, empleado): para el CHAT (Parte 2, punto 2).
  Puntúa documentos y FAQ por solapamiento de palabras con la pregunta libre
  del empleado + un bonus si el departamento del doc coincide con el del
  empleado. Se limita a 3 docs + 2 FAQ por turno para no volcar los 13 docs
  / 16 FAQ enteros en cada llamada al modelo. El pool de documentos incluye
  también convenio.json (artículos del convenio colectivo: períodos de
  prueba, permisos, baja voluntaria, teletrabajo) vía
  cargar_documentos_contexto(), para poder citar cláusulas reales en vez de
  derivar siempre a RRHH cuando preguntan por el convenio. El `cuerpo` de
  cada doc se trunca defensivamente a MAX_CHARS_DOC caracteres antes de
  devolverlo (protección si algún doc creciera; con los actuales no recorta
  nada).

- seleccionar_docs_checklist(empleado, dia): para el CHECKLIST (Parte 2,
  punto 2 y "Día de onboarding simulado"). No usa búsqueda por palabras: no
  hay pregunta libre, así que la selección es determinista por
  departamento + día. onboarding_docs.json NO tiene un campo `dia`; los
  planes día a día de Engineering y Sales viven como texto libre dentro del
  `cuerpo` de doc_eng_01 y doc_sales_01 ("Día 1: ... Día 2: ..."), así que
  aquí se parsea ese texto. Los departamentos sin ese plan (operations,
  people, it, curriculum) usan un fallback fijo (ver DOCS_GENERICOS_POR_DIA).

- regla_escalado(pregunta, resultado_contexto): a quién derivar (Parte 1,
  punto 3: "acordar cuándo escalar a RRHH, IT, manager u onboarding"). No
  bloquea nada (eso es Parte 3 / validators.py); solo decide, dado el
  resultado de seleccionar_contexto(), si hace falta derivar y a qué
  contacto de empresa.json.

También incluye validar_datos(), una comprobación rápida de que
onboarding_docs.json, faq_onboarding.json, empresa.json y empleados_demo.json
tienen los campos que usa este módulo y que las referencias cruzadas
(faq.doc_id -> documentos) son válidas.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).resolve().parent / "data"


# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------

def _cargar_json(nombre_fichero: str):
    ruta = DATA_DIR / nombre_fichero
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def cargar_documentos() -> list[dict]:
    """Devuelve los 13 documentos de onboarding_docs.json."""
    return _cargar_json("onboarding_docs.json")


def cargar_faqs() -> list[dict]:
    """Devuelve las 16 preguntas frecuentes de faq_onboarding.json."""
    return _cargar_json("faq_onboarding.json")


def cargar_empresa() -> dict:
    """Devuelve el lore/estructura de Bridge SA (empresa.json)."""
    return _cargar_json("empresa.json")


def cargar_empleados() -> list[dict]:
    """Devuelve los 5 empleados demo de empleados_demo.json."""
    return _cargar_json("empleados_demo.json")


def cargar_convenio() -> list[dict]:
    """Devuelve los artículos del convenio colectivo (convenio.json), con el
    mismo esquema que onboarding_docs.json (id, titulo, departamento, tags,
    cuerpo) para poder puntuarlos igual en seleccionar_contexto()."""
    return _cargar_json("convenio.json")


def cargar_documentos_contexto() -> list[dict]:
    """Pool combinado para el CHAT: los 13 docs de onboarding_docs.json + los
    artículos de convenio.json (períodos de prueba, permisos, baja
    voluntaria, teletrabajo...). Se mantiene separado de cargar_documentos()
    porque seleccionar_docs_checklist() y validar_datos() operan
    específicamente sobre onboarding_docs.json (los únicos docs con plan
    día a día); el convenio no aporta nada a esa función."""
    return cargar_documentos() + cargar_convenio()


def obtener_empleado(empleado_id: str, empleados: Optional[list[dict]] = None) -> dict:
    """Busca un empleado por id (p. ej. 'emp_01') en empleados_demo.json."""
    empleados = empleados if empleados is not None else cargar_empleados()
    for emp in empleados:
        if emp["id"] == empleado_id:
            return emp
    raise ValueError(f"Empleado '{empleado_id}' no encontrado en empleados_demo.json")


# ---------------------------------------------------------------------------
# Utilidades de texto (para la puntuación por solapamiento de palabras)
# ---------------------------------------------------------------------------

_STOPWORDS_ES = {
    "el", "la", "los", "las", "de", "del", "un", "una", "unos", "unas", "y",
    "o", "a", "en", "que", "es", "por", "para", "con", "mi", "tu", "su",
    "al", "se", "lo", "como", "mas", "muy", "este", "esta", "esto", "ese",
    "esa", "eso", "cuando", "donde", "cual", "cuanto", "cuanta", "hay",
    "tengo", "tienes", "tiene", "debo", "puedo", "quiero", "necesito",
    "sobre", "si", "no", "me", "te", "le", "les", "mis", "tus", "sus",
    "soy", "eres", "somos", "sois", "son", "ser", "estar", "esta", "estan",
    "hacer", "hago", "haces", "hace", "que", "quien", "quienes", "las",
}


def _normalizar(texto: str) -> str:
    """minúsculas + sin tildes, para que 'días' y 'dias' puntúen igual."""
    texto = texto.lower()
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )


def _tokenizar(texto: str) -> set[str]:
    texto = _normalizar(texto)
    palabras = re.findall(r"[a-z0-9#]+", texto)
    return {p for p in palabras if p not in _STOPWORDS_ES and len(p) > 2}


def _bag_de_palabras_doc(doc: dict) -> set[str]:
    return _tokenizar(" ".join([doc.get("titulo", ""), doc.get("cuerpo", ""), " ".join(doc.get("tags", []))]))


def _bag_de_palabras_faq(faq: dict) -> set[str]:
    return _tokenizar(" ".join([faq.get("pregunta", ""), faq.get("respuesta_corta", ""), " ".join(faq.get("tags", []))]))


def _departamento_de_faq(faq: dict, documentos: list[dict]) -> Optional[str]:
    """Las FAQ no tienen campo 'departamento' propio: se hereda del doc que
    referencian vía doc_id, para poder aplicar el mismo bonus que a los docs."""
    doc = next((d for d in documentos if d["id"] == faq.get("doc_id")), None)
    return doc.get("departamento") if doc else None


# ---------------------------------------------------------------------------
# seleccionar_contexto() — CHAT (Parte 2, punto 2)
# ---------------------------------------------------------------------------

BONUS_DEPARTAMENTO = 2  # puntos extra si doc.departamento == empleado.departamento
MAX_DOCS = 3
MAX_FAQS = 2
MAX_CHARS_DOC = 500  # truncado defensivo del cuerpo antes de meterlo en el prompt


def _truncar(texto: str, max_chars: int = MAX_CHARS_DOC) -> str:
    """Corta `texto` a `max_chars` y añade '…' si se ha recortado. Protección
    defensiva por si algún doc (o el convenio) crece más de lo esperado; con
    los docs actuales (todos cortos) normalmente no recorta nada."""
    if len(texto) <= max_chars:
        return texto
    return texto[:max_chars].rstrip() + "…"

# Fallback cuando ninguna pregunta puntúa (pregunta genérica, mal formulada,
# o fuera de las palabras clave que conocemos): contexto mínimo de bienvenida
# + programa buddy, para que el asistente siempre tenga algo que citar antes
# de derivar a RRHH/IT en vez de alucinar.
DOC_FALLBACK_IDS = ["doc_bienvenida_01", "doc_people_01"]
FAQ_FALLBACK_IDS = ["faq_01", "faq_16"]


def _puntuar(palabras_pregunta: set[str], bag: set[str], doc_departamento, empleado_departamento) -> int:
    solapamiento = len(palabras_pregunta & bag)
    bonus = BONUS_DEPARTAMENTO if doc_departamento is not None and doc_departamento == empleado_departamento else 0
    return solapamiento + bonus


def seleccionar_contexto(
    pregunta: str,
    empleado: dict,
    documentos: Optional[list[dict]] = None,
    faqs: Optional[list[dict]] = None,
    max_docs: int = MAX_DOCS,
    max_faqs: int = MAX_FAQS,
) -> dict:
    """
    Selecciona hasta `max_docs` documentos y `max_faqs` FAQ relevantes para
    responder `pregunta`, dado `empleado` (dict con al menos "departamento").

    Puntuación = nº de palabras (sin stopwords, sin tildes) que la pregunta
    comparte con el doc/FAQ (título + cuerpo + tags, o pregunta + respuesta +
    tags) + BONUS_DEPARTAMENTO si el departamento del doc coincide con el
    del empleado. Esto favorece, ante empate de palabras, el documento del
    propio departamento del empleado.

    Por qué 3 docs + 2 FAQ y no todo el JSON: con 13 docs + 16 FAQ el texto
    cabría igualmente en el contexto de casi cualquier LLM actual, pero el
    enunciado pide explícitamente NO volcar todo el dataset en cada turno
    (ahorro de tokens/coste y evitar que el modelo se distraiga con
    información irrelevante). 3+2 es suficiente para cubrir la pregunta más
    relacionada y un par de referencias de apoyo.

    Fallback: si NINGÚN doc ni FAQ puntúa > 0, se devuelve un contexto fijo
    mínimo (DOC_FALLBACK_IDS / FAQ_FALLBACK_IDS) en vez de una lista vacía,
    para que el asistente pueda responder algo razonable ("no tengo esa
    info documentada, contacta con...") en lugar de quedarse sin contexto.
    """
    documentos = documentos if documentos is not None else cargar_documentos_contexto()
    faqs = faqs if faqs is not None else cargar_faqs()
    depto_empleado = empleado.get("departamento")
    palabras_pregunta = _tokenizar(pregunta)

    docs_puntuados = [
        (doc, _puntuar(palabras_pregunta, _bag_de_palabras_doc(doc), doc.get("departamento"), depto_empleado))
        for doc in documentos
    ]
    faqs_puntuadas = [
        (faq, _puntuar(palabras_pregunta, _bag_de_palabras_faq(faq), _departamento_de_faq(faq, documentos), depto_empleado))
        for faq in faqs
    ]

    docs_puntuados.sort(key=lambda par: par[1], reverse=True)
    faqs_puntuadas.sort(key=lambda par: par[1], reverse=True)

    docs_top = [doc for doc, score in docs_puntuados[:max_docs] if score > 0]
    faqs_top = [faq for faq, score in faqs_puntuadas[:max_faqs] if score > 0]

    if not docs_top and not faqs_top:
        docs_top = [d for d in documentos if d["id"] in DOC_FALLBACK_IDS]
        faqs_top = [f for f in faqs if f["id"] in FAQ_FALLBACK_IDS]

    docs_top = [{**d, "cuerpo": _truncar(d.get("cuerpo", ""))} for d in docs_top]

    return {"docs": docs_top, "faqs": faqs_top}


# ---------------------------------------------------------------------------
# seleccionar_docs_checklist() — CHECKLIST (Parte 2, punto 2 + "día simulado")
# ---------------------------------------------------------------------------

# Departamentos cuyo plan día a día SÍ está redactado como texto libre
# ("Día 1: ... Día 2: ...") dentro del cuerpo de un doc concreto.
DOC_PLAN_POR_DEPARTAMENTO = {
    "engineering": "doc_eng_01",
    "sales": "doc_sales_01",
}

# Fallback fijo por día para departamentos SIN plan día a día explícito
# (operations, people, it, curriculum...). Sin esto, empleados como emp_04
# (Operations) se quedarían sin checklist a partir del día 1.
DOCS_GENERICOS_POR_DIA = {
    1: ["doc_bienvenida_01", "doc_it_02"],
    2: ["doc_it_01", "doc_rrhh_01"],
    3: ["doc_people_01"],
    4: ["doc_cultura_01"],
    5: ["doc_beneficios_01"],
}

# Doc "de propio departamento" que se añade siempre al fallback genérico,
# si existe uno para ese departamento.
DOC_PROPIO_POR_DEPARTAMENTO = {
    "operations": "doc_ops_01",
    "people": "doc_people_01",
}

_PATRON_DIA = re.compile(r"Día\s*(\d+):\s*(.*?)(?=(?:Día\s*\d+:)|$)", re.IGNORECASE | re.DOTALL)


def _fragmento_del_dia(doc: dict, dia: int) -> Optional[str]:
    """Extrae el trozo de `doc['cuerpo']` correspondiente a 'Día {dia}: ...'.

    Necesario porque onboarding_docs.json no tiene un campo `dia`: el plan
    día a día vive como texto libre dentro del cuerpo de doc_eng_01 /
    doc_sales_01. Esto evita mandar los 5 días enteros al prompt cuando solo
    hace falta el día actual."""
    for numero, fragmento in _PATRON_DIA.findall(doc["cuerpo"]):
        if int(numero) == dia:
            return fragmento.strip().rstrip(". ") + "."
    return None


def seleccionar_docs_checklist(
    empleado: dict,
    dia: int,
    documentos: Optional[list[dict]] = None,
) -> dict:
    """
    Selecciona los documentos "fuente" para generar el checklist del `dia`
    (1-5) de `empleado`.

    A diferencia de seleccionar_contexto(), aquí NO hay pregunta libre que
    buscar por palabras: ya sabemos exactamente qué día y qué departamento
    es, así que la selección es determinista por departamento + día, no por
    solapamiento de palabras.

    - Si el departamento tiene un doc de plan día a día (engineering →
      doc_eng_01, sales → doc_sales_01), se devuelve ese doc junto con el
      fragmento de texto ya recortado para ese día (fragmento_dia), listo
      para citar como fuente_doc de cada tarea.
    - Si el departamento NO tiene plan día a día redactado (operations,
      people, it, curriculum, o cualquier futuro sin ese texto), se usa el
      fallback fijo por día (DOCS_GENERICOS_POR_DIA) + el doc general del
      propio departamento si existe (DOC_PROPIO_POR_DEPARTAMENTO).

    Devuelve:
        {"docs": [documentos fuente], "fragmento_dia": texto del día o None}
    """
    documentos = documentos if documentos is not None else cargar_documentos()
    docs_por_id = {d["id"]: d for d in documentos}
    depto = empleado.get("departamento")

    doc_plan_id = DOC_PLAN_POR_DEPARTAMENTO.get(depto)
    if doc_plan_id and doc_plan_id in docs_por_id:
        doc_plan = docs_por_id[doc_plan_id]
        fragmento = _fragmento_del_dia(doc_plan, dia)
        doc_plan_truncado = {**doc_plan, "cuerpo": _truncar(doc_plan.get("cuerpo", ""))}
        return {
            "docs": [doc_plan_truncado],
            "fragmento_dia": _truncar(fragmento) if fragmento else None,
        }

    ids_fallback = list(DOCS_GENERICOS_POR_DIA.get(dia, []))
    doc_propio_id = DOC_PROPIO_POR_DEPARTAMENTO.get(depto)
    if doc_propio_id and doc_propio_id not in ids_fallback:
        ids_fallback.append(doc_propio_id)

    docs_fallback = [docs_por_id[i] for i in ids_fallback if i in docs_por_id]
    docs_fallback = [{**d, "cuerpo": _truncar(d.get("cuerpo", ""))} for d in docs_fallback]
    return {"docs": docs_fallback, "fragmento_dia": None}


# ---------------------------------------------------------------------------
# regla_escalado() — a quién derivar (Parte 1, punto 3: "acordar cuándo
# escalar a RRHH, IT, manager u onboarding@bridgesa.example")
# ---------------------------------------------------------------------------

# Palabras que, si aparecen en la pregunta, fuerzan escalado por dato
# sensible SIN mirar el contexto encontrado — el asistente no debe intentar
# responder cifras de salario/bonus ni datos de otros empleados (regla
# explícita del enunciado: "El asistente NO debe... responder sobre
# salarios o datos de otros empleados").
_PALABRAS_SENSIBLES = {"sueldo", "salario", "nomina", "bonus", "cobra", "gana", "equity", "acciones"}

# Departamento del doc principal -> qué contacto de empresa.json aplica.
# engineering/sales/operations no tienen contacto dedicado: se deriva al
# manager del propio empleado en vez de a un email genérico.
_CONTACTO_POR_DEPARTAMENTO = {"it": "it", "people": "rrhh"}


def regla_escalado(pregunta: str, resultado_contexto: dict, empresa: Optional[dict] = None) -> dict:
    """
    Decide si esta pregunta debe derivarse a alguien en vez de responderse
    directamente, y a quién.

    No bloquea nada (eso es fail-closed / validators.py en Parte 3): esto es
    solo la tabla de derivación de Parte 1 para que el asistente sepa qué
    contacto mencionar cuando no debe o no puede responder por completo.

    Casos, en este orden:
    1. Dato sensible (`_PALABRAS_SENSIBLES`: salario, bonus...) -> escalar
       siempre a People, sin mirar el contexto encontrado.
    2. Sin contexto relevante (`seleccionar_contexto()` no encontró nada,
       ni con fallback) -> escalar a onboarding@bridgesa.example.
    3. El doc mejor puntuado es de un departamento con contacto dedicado
       (it/people) -> se sugiere ese contacto como apoyo, pero no bloquea
       la respuesta (`debe_escalar=False`).
    4. Cualquier otro caso -> no hace falta escalar; se sugiere al manager
       del empleado como contacto de referencia.

    Devuelve:
        {"debe_escalar": bool, "motivo": str, "contacto": str|None, "mensaje": str|None}
    """
    empresa = empresa if empresa is not None else cargar_empresa()
    contactos = empresa.get("contactos", {})
    palabras_pregunta = _tokenizar(pregunta)

    if palabras_pregunta & _PALABRAS_SENSIBLES:
        return {
            "debe_escalar": True,
            "motivo": "dato_sensible",
            "contacto": contactos.get("people_partner") or contactos.get("rrhh"),
            "mensaje": "No comparto cifras de salario, bonus o equity, ni datos de otras personas. Coméntalo con tu manager o con People en tu 1:1.",
        }

    docs = resultado_contexto.get("docs", [])
    faqs = resultado_contexto.get("faqs", [])

    if not docs and not faqs:
        return {
            "debe_escalar": True,
            "motivo": "sin_contexto",
            "contacto": contactos.get("onboarding"),
            "mensaje": "No tengo esto documentado. Escribe a onboarding@bridgesa.example para que te lo confirmen.",
        }

    depto_principal = docs[0].get("departamento") if docs else None
    clave_contacto = _CONTACTO_POR_DEPARTAMENTO.get(depto_principal)
    if clave_contacto and clave_contacto in contactos:
        return {
            "debe_escalar": False,
            "motivo": "contacto_departamento",
            "contacto": contactos[clave_contacto],
            "mensaje": None,
        }

    return {
        "debe_escalar": False,
        "motivo": "informativo",
        "contacto": None,
        "mensaje": None,
    }


# ---------------------------------------------------------------------------
# Validación de datos (tarea 3 de Persona 1)
# ---------------------------------------------------------------------------

def validar_datos(verbose: bool = True) -> list[str]:
    """Comprueba que data/ tiene lo que context.py necesita. Devuelve una
    lista de avisos (vacía si todo está OK). No lanza excepción: son avisos
    para el equipo, no errores fatales de carga."""
    avisos: list[str] = []

    documentos = cargar_documentos()
    faqs = cargar_faqs()
    empresa = cargar_empresa()
    empleados = cargar_empleados()

    if len(documentos) != 13:
        avisos.append(f"onboarding_docs.json tiene {len(documentos)} docs (se esperaban 13).")
    if len(faqs) != 16:
        avisos.append(f"faq_onboarding.json tiene {len(faqs)} FAQ (se esperaban 16).")
    tamano_esperado = empresa.get("tamano_aproximado")
    if tamano_esperado and len(empleados) != tamano_esperado:
        avisos.append(
            f"empleados_demo.json tiene {len(empleados)} empleados; "
            f"empresa.json.tamano_aproximado dice {tamano_esperado}."
        )

    campos_doc = {"id", "titulo", "departamento", "tags", "cuerpo"}
    for doc in documentos:
        faltan = campos_doc - doc.keys()
        if faltan:
            avisos.append(f"Doc '{doc.get('id')}' sin campos: {faltan}")

    convenio = cargar_convenio()
    for doc in convenio:
        faltan = campos_doc - doc.keys()
        if faltan:
            avisos.append(f"Artículo de convenio '{doc.get('id')}' sin campos: {faltan}")
    ids_convenio = {d["id"] for d in convenio}
    colisiones = ids_convenio & {d["id"] for d in documentos}
    if colisiones:
        avisos.append(f"IDs de convenio.json chocan con onboarding_docs.json: {colisiones}")

    ids_doc = {d["id"] for d in documentos}
    for faq in faqs:
        if faq.get("doc_id") not in ids_doc:
            avisos.append(f"FAQ '{faq.get('id')}' apunta a doc_id inexistente: {faq.get('doc_id')}")

    departamentos_empresa = {d["id"] for d in empresa.get("departamentos", [])}
    campos_emp = {"id", "nombre", "departamento", "rol", "fecha_inicio", "manager", "modalidad", "ubicacion", "idioma_preferido", "perfil"}
    for emp in empleados:
        faltan = campos_emp - emp.keys()
        if faltan:
            avisos.append(f"Empleado '{emp.get('id')}' sin campos: {faltan}")
        if emp.get("departamento") not in departamentos_empresa:
            avisos.append(
                f"Empleado '{emp.get('id')}' tiene departamento '{emp.get('departamento')}' "
                f"que no está en empresa.json.departamentos {sorted(departamentos_empresa)}."
            )
        if emp.get("departamento") not in DOC_PLAN_POR_DEPARTAMENTO:
            avisos.append(
                f"Empleado '{emp.get('id')}' es de '{emp.get('departamento')}', que no tiene plan "
                f"día a día en onboarding_docs.json; su checklist usará el fallback genérico "
                f"(ver DOCS_GENERICOS_POR_DIA en context.py)."
            )

    if verbose:
        if avisos:
            print(f"validar_datos(): {len(avisos)} aviso(s):")
            for a in avisos:
                print(f" - {a}")
        else:
            print("validar_datos(): todo OK, no hay avisos.")

    return avisos


if __name__ == "__main__":
    validar_datos()

    print("\n--- Demo seleccionar_contexto() ---")
    laura = obtener_empleado("emp_01")
    resultado = seleccionar_contexto("¿A qué canales de Slack tengo que unirme?", laura)
    print("Docs:", [d["id"] for d in resultado["docs"]])
    print("FAQs:", [f["id"] for f in resultado["faqs"]])

    print("\n--- Demo seleccionar_docs_checklist() (engineering, día 1) ---")
    print(seleccionar_docs_checklist(laura, 1))

    print("\n--- Demo seleccionar_docs_checklist() (operations, fallback) ---")
    miguel = obtener_empleado("emp_04")
    print(seleccionar_docs_checklist(miguel, 1))

    print("\n--- Demo seleccionar_contexto() con pregunta de convenio ---")
    resultado_convenio = seleccionar_contexto("¿Cuánto dura mi período de prueba según el convenio?", laura)
    print("Docs:", [d["id"] for d in resultado_convenio["docs"]])
    print("FAQs:", [f["id"] for f in resultado_convenio["faqs"]])

    print("\n--- Demo regla_escalado() ---")
    print("Dato sensible:", regla_escalado("¿Cuánto gana mi manager de bonus?", {"docs": [], "faqs": []}))
    print("Sin contexto:", regla_escalado("xyz pregunta rara sin relacion", {"docs": [], "faqs": []}))
    print("Contacto IT:", regla_escalado("¿Cómo activo Slack?", seleccionar_contexto("¿Cómo activo Slack?", laura)))
