# Employee Onboarding Assistant – Parte 2

## Objetivo

La Parte 2 del proyecto consiste en implementar un asistente de onboarding basado en un modelo de lenguaje (Gemini), siguiendo una arquitectura modular y desacoplada.

El objetivo principal es que el asistente sea capaz de:

* mantener una conversación con un empleado;
* responder utilizando únicamente el contexto relevante;
* generar un checklist de onboarding en formato JSON;
* mantener un historial limitado de la conversación;
* adaptarse al perfil del empleado y al día de onboarding.

---

# Arquitectura

La solución se ha diseñado siguiendo el principio de **responsabilidad única (Single Responsibility Principle)**, de forma que cada módulo se encargue de una única tarea.

```
Usuario
    │
    ▼
logic.py
    │
    ├────────► context.py
    │
    ├────────► state.py
    │
    ▼
prompts.py
    │
    ▼
gemini_client.py
    │
    ▼
Gemini API
```

Esta separación permite modificar un componente sin afectar al resto del sistema.

---

# Archivos desarrollados

## config.py

Centraliza toda la configuración del asistente.

Incluye:

* modelo de Gemini utilizado;
* temperatura;
* límite de tokens;
* máximo de documentos enviados al modelo;
* máximo de FAQ;
* máximo de historial.

Separar la configuración de la lógica facilita el mantenimiento del proyecto y evita valores hardcodeados.

---

## gemini_auth.py

Gestiona la autenticación con Gemini.

Su funcionamiento es:

1. Carga automáticamente el archivo `.env`.
2. Busca la variable `GEMINI_API_KEY`.
3. Si no existe, solicita la clave mediante `getpass`.
4. Configura la API únicamente una vez durante la ejecución.

De esta forma la clave nunca queda escrita dentro del código.

---

## gemini_client.py

Es el único módulo que conoce la API de Gemini.

Sus responsabilidades son:

* crear el cliente;
* enviar prompts;
* devolver únicamente el texto generado.

No contiene lógica de negocio ni conoce empleados, documentos o historial.

Esto permite sustituir Gemini por otro proveedor modificando únicamente este archivo.

---

## prompts.py

Construye dinámicamente los prompts enviados al modelo.

Recibe:

* datos del empleado;
* día de onboarding;
* documentos seleccionados;
* FAQ relevantes;
* historial reciente;
* pregunta del usuario.

Con toda esta información genera un prompt estructurado mediante delimitadores claros.

También implementa un prompt específico para la generación del checklist, obligando al modelo a devolver un JSON válido.

---

## logic.py

Es el orquestador principal del asistente.

Coordina el flujo completo:

1. Recibe la pregunta del usuario.
2. Solicita el contexto relevante a `context.py`.
3. Recupera el historial desde `state.py`.
4. Construye el prompt utilizando `prompts.py`.
5. Envía el prompt a Gemini mediante `gemini_client.py`.
6. Guarda la respuesta en el historial.

Para la generación del checklist sigue el mismo proceso utilizando el contexto específico del día de onboarding.

---

# Flujo del asistente

```
Empleado
    │
    ▼
Pregunta
    │
    ▼
logic.py
    │
    ▼
context.py
(selección de documentos y FAQ)
    │
    ▼
state.py
(historial)
    │
    ▼
prompts.py
(construcción del prompt)
    │
    ▼
gemini_client.py
(llamada a Gemini)
    │
    ▼
Respuesta
```

---

# Gestión del contexto

Uno de los requisitos del ejercicio era **no enviar toda la documentación al modelo**.

Para cumplir este requisito:

* `context.py` selecciona únicamente los documentos relevantes.
* El número máximo de documentos y FAQ enviados está limitado desde `config.py`.
* `prompts.py` únicamente transforma ese contexto en un prompt, sin realizar ninguna selección adicional.

Con ello se reduce el número de tokens enviados y se mejora la calidad de las respuestas.

---

# Historial de conversación

El historial se mantiene mediante `state.py`.

Solo se conservan los últimos turnos definidos en la configuración para evitar que el contexto crezca indefinidamente.

Este historial se incorpora al prompt para que el asistente mantenga la continuidad de la conversación.

---

# Checklist

El asistente puede generar un checklist personalizado para cada empleado.

El proceso consiste en:

* obtener el contexto correspondiente al día de onboarding;
* construir un prompt específico;
* solicitar al modelo un JSON válido;
* convertir la respuesta en un diccionario de Python para poder trabajar posteriormente con ella.

---

# Decisiones de diseño

Durante el desarrollo se han seguido los siguientes principios:

* separación clara de responsabilidades;
* arquitectura modular;
* reutilización de funciones;
* configuración centralizada;
* prompts dinámicos;
* mínimo contexto enviado al modelo;
* código fácilmente mantenible y escalable.

Esta organización permite ampliar el proyecto en el futuro sin necesidad de modificar toda la aplicación. Por ejemplo, sería posible sustituir Gemini por otro proveedor de modelos de lenguaje modificando únicamente `gemini_client.py`.
![Cabecera](assets/cabecera_thebridge.png)

# Team Challenge · Sprint 05–07 — Employee Onboarding Assistant

Construir en equipo el producto **Employee Onboarding Assistant** para **Bridge SA** (empresa ficticia del reto): un copiloto que acompaña a **empleados nuevos** en sus primeros días — responde dudas con documentación interna, genera checklists y sabe cuándo derivar a People o IT.

Esta práctica integra conceptos de:
- **Prompt & Context Engineering**, 
- **Assistant Engineering & Robustez**,
- **Arquitecturas y evaluación de modelos**
---

## Material proporcionado

**Datos y plantillas** que habrá que utilizar para implementar el asistente.

| Recurso | Uso |
|---------|-----|
| `data/` | Lore de Bridge SA, documentos de onboarding, FAQ, empleados demo, casos trampa de ejemplo |
| `entregables/` | Plantillas de matriz, recomendación y rúbrica |

---

## Entregables finales

1. **Repositorio GitHub** con código reproducible y README bien documentado.
2. **Asistente funcional** con las capacidades descritas abajo (conversación, checklist, día de onboarding).
3. **Robustez** — demo vulnerable vs seguro + 5 casos trampa propios.
4. **Benchmark** — mínimo 10 casos, **2 modelos** comparados (mismas condiciones), resultados en `output/`.
5. **`entregables/matriz_decision.md`** y **`entregables/recomendacion.md`** completos.

---

## Trabajo en equipo y Git

Gestión del proyecto con **GitHub desde el primer día**. La **organización interna del equipo** (quién hace qué y en qué orden) la decidís vosotros.

### Reglas mínimas

- Crear el **repositorio en GitHub** al inicio, no al final del reto.
- **Mínimo una PR revisada y mergeada por miembro** del equipo.
- Integrar con **pull requests** hacia `develop`; resolver conflictos en la rama antes del merge.
- **No subir claves** — usar `.env` y `.gitignore`.
- README del repo: cómo clonar, instalar dependencias, configurar API keys y ejecutar las demos.

### Buenas prácticas con Git

Flujo de ramas recomendado:

| Rama | Uso |
|------|-----|
| `main` | Código estable y entregable. **No trabajéis directamente aquí.** |
| `develop` | Integración del trabajo del equipo. |
| Ramas secundarias | Una rama por bloque de trabajo, creada desde `develop`. |

**Convención de ramas** (minúsculas, descriptivas):

- `feature/contexto-datos` — Parte 1
- `feature/asistente-modular` — Parte 2
- `feature/robustez` — Parte 3
- `feature/benchmark` — Parte 4
- `fix/parseo-json-checklist` — correcciones puntuales

**Flujo recomendado:**

```text
develop ──► feature/tu-tarea ──► commits ──► PR ──► merge a develop
                                              │
develop ──────────────────────────────────────┘
       │
       └──► cuando todo esté listo y probado ──► merge a main
```

- Commits **pequeños y con mensaje claro** (qué funcionalidad o archivo tocaste).
- **Nunca** subas `.env` ni `.venv/`.
- Antes de mergear a `main`, `develop` debe ejecutar las demos sin errores pendientes.

---

## Estructura de proyecto

Ejemplo **orientativo** — podéis organizarlo distinto si lo explicáis en vuestro README:

```text
employee-onboarding-assistant/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── config.py              # perfiles, modelos, límites de contexto
├── gemini_auth.py         # carga de API key (o equivalente para otro proveedor)
├── gemini_client.py       # llamadas al LLM
├── context.py             # selección de docs/FAQ relevantes
├── prompts.py             # construcción dinámica de prompts
├── state.py               # perfil empleado + historial
├── logic.py               # orquestación (turnos, checklist, modos)
├── validators.py          # validación y dominio acotado
├── main.py                # demos numeradas y reproducibles
├── benchmark.py           # Parte 4 — ejecución del benchmark y export a output/
├── data/                  # datos del TC (copiar tal cual)
├── entregables/           # Añade aquí tus conclusiones finales
│   ├── matriz_decision.md
│   ├── recomendacion.md
│   └── rubrica_benchmark.md
└── output/                # resultados de benchmark
```


Evitad un único script monolítico. Intentad mantener **separación de responsabilidades** (configuración, prompts, contexto, lógica, validación, etc.).

---

## Capacidades del asistente

El producto debe cubrir **dos funcionalidades** y un **requisito transversal**:

### 1. Conversación (chat)

El empleado escribe una pregunta libre. El asistente responde en **texto**, usando documentación relevante y, si aplica, historial reciente (máx. **4 turnos** en contexto).

**Ejemplo:** *«¿A qué canales de Slack tengo que unirme?»* → respuesta breve citando la política de canales.

### 2. Checklist de la semana 1 (JSON)

**Qué hace:** el equipo (o una demo en `main.py`) le pasa al asistente **quién es el empleado** y **qué día de onboarding le toca** (1–5). El asistente **no responde en texto libre**: devuelve un **plan del día** en JSON con tareas concretas, basadas en la documentación de Bridge SA.

**Ejemplo de uso:** Laura (`emp_01`), dev junior, **día 1** → el asistente genera un JSON con tareas como unirse a Slack, asistir a la reunión de bienvenida y contactar con su buddy.

**Campos mínimos del JSON:**

| Campo | Significado |
|-------|-------------|
| `empleado_id` | Identificador del empleado (p. ej. `emp_01` en `empleados_demo.json`) |
| `dia` | Día de onboarding simulado (1–5) |
| `tareas` | Lista de acciones para ese día |
| `tareas[].titulo` | Qué debe hacer el empleado, en lenguaje claro |
| `tareas[].fuente_doc` | Id del documento de `onboarding_docs.json` que justifica la tarea |
| `tareas[].completada` | `false` al generar el plan (el empleado aún no la ha hecho) |
| `mensaje_resumen` | Frase corta de orientación para ese día |

**Ejemplo de salida** (ilustrativo; vuestra lista de tareas puede tener más entradas):

```json
{
  "empleado_id": "emp_01",
  "dia": 1,
  "tareas": [
    {
      "id": "t01",
      "titulo": "Unirse a los canales obligatorios de Slack (#general, #anuncios y canal de departamento)",
      "completada": false,
      "fuente_doc": "doc_it_02"
    },
    {
      "id": "t02",
      "titulo": "Asistir a la reunión de bienvenida de las 9:30 y saludar a tu buddy en Slack",
      "completada": false,
      "fuente_doc": "doc_bienvenida_01"
    }
  ],
  "mensaje_resumen": "Primer día: Dar accesos básicos al empleado."
}
```

### 3. Día de onboarding simulado (requisito transversal)

El asistente debe conocer en qué **día de onboarding** (1–5) está el empleado y reflejarlo tanto en el **chat** como en el **checklist**:

- **Día 1:** tono de bienvenida; tareas de accesos y primeros pasos.
- **Día 3:** no repetir lo del día 1; priorizar tareas de integración (pair programming, primera issue, etc.).

Podéis guardar el día en el state, en la ficha del empleado o donde encaje en vuestra arquitectura.

---

## Tipos de empleado - roles que soporta el asistente

El asistente debe **adaptarse** al menos a estos tres perfiles (tono, contexto y ejemplos distintos):

| Perfil | Uso |
|--------|-----|
| Dev junior | Engineering, primer empleo — tono didáctico |
| Comercial | Sales — menos técnico, herramientas comerciales |
| Remoto en UE | Políticas cross-border, remoto internacional |

Empleados de prueba: `data/empleados_demo.json`.  
Contexto de la empresa: `data/empresa.json`.

---

## Reglas para desarrollar el asistente

**El asistente SÍ** ayuda con: herramientas corporativas, primeros pasos, cultura, vacaciones según documentación, a quién contactar.

**El asistente NO debe:**

- Inventar políticas, plazos o cifras no documentadas.
- Responder sobre salarios o datos de otros empleados.
- Atender consultas de **participantes externos** de los programas formativos de Bridge SA (derivar: “solo onboarding de empleados”).
- Llamar al modelo en modo seguro si la validación falla (**fail-closed**).

---

# Parte 1 — Contexto y datos

**Objetivo:** conocer el trasfondo de Bridge SA y acordar en el equipo qué hace el producto antes de programar el LLM.

1. Copiar `data/` y plantillas a vuestro repositorio.
2. Leer `data/empresa.json`, `onboarding_docs.json`, `faq_onboarding.json` y `empleados_demo.json`.
3. Acordar en el equipo cuándo escalar a RRHH, IT, manager u `onboarding@bridgesa.example`.

### Revisión de datos (Persona 1)

Comprobación de que `data/` tiene lo que `context.py` necesita (campos `departamento`, `tags`, `cuerpo`, `doc_id`, etc.). Automatizada en `context.validar_datos()`; `python context.py` la ejecuta y muestra avisos.

- `onboarding_docs.json`: 13 docs, todos con `id`, `titulo`, `departamento`, `tags`, `cuerpo`. OK.
- `faq_onboarding.json`: 16 FAQ, todas con `doc_id` apuntando a un doc existente. OK.
- `empleados_demo.json`: ampliado de 5 a **85 empleados** (coincide con `empresa.json.tamano_aproximado`), todos con los campos que usa `context.py`. Sigue cubriendo los 3 perfiles exigidos (`dev_junior`, `comercial`, `remoto_eu`) y ahora incluye el departamento `people` además de `engineering`/`sales`/`operations`. `context.validar_datos()` ya no exige exactamente 5: compara contra `tamano_aproximado`.
- **Aviso (esperado, no bloqueante):** solo `doc_eng_01` (engineering) y `doc_sales_01` (sales) tienen un plan día a día redactado como texto libre ("Día 1: ... Día 2: ..."). `emp_04` (Miguel Ángel Toro) es de `operations`, departamento sin ese plan, así que su checklist se genera con el fallback fijo `DOCS_GENERICOS_POR_DIA` de `context.py` en vez de un texto "Día N" específico. Si el equipo incorpora más empleados de `people`, `it` o `curriculum`, aplica el mismo fallback.
- **Nota:** los documentos de IT (`doc_it_01/02/03`) usan `"departamento": "it"`, que no aparece en la lista `empresa.departamentos` (solo `engineering`, `sales`, `operations`, `people`, `curriculum`). Es intencional — son transversales a todos los departamentos —, pero implica que el bonus por departamento de `seleccionar_contexto()` nunca aplicará a estos docs salvo que se añada `it` como departamento de empleado.
- `data/convenio.json` no está en la tabla de datos del enunciado; si no lo usa ninguna parte del asistente, confirmar con el equipo si debe quedarse en `data/` o retirarse antes de la entrega.

---

# Parte 2 — Asistente modular

**Objetivo:** implementar conversación + checklist con arquitectura por capas (S5 + S6).

1. Cliente del LLM — podéis basaros en proyectos de sprint (Gemini u otro proveedor).
2. Selección de contexto **sin volcar todo** el JSON (p. ej. máx. 3 docs + 2 FAQ por turno; filtro por departamento o keywords).
3. Prompts dinámicos con delimitadores claros (`<empleado>`, `<docs>`, `<pregunta>` o equivalente).
4. Historial conversacional acotado (máx. 4 turnos en el prompt).
5. Integración del **día de onboarding** (1–5) en chat y checklist.
6. **`main.py`** (o equivalente) con al menos **3 demos** ejecutables:
   - **Demo 1:** conversación de 1 turno (empleado tipo dev junior).
   - **Demo 2:** checklist JSON para día 1.
   - **Demo 3:** mismo mensaje con empleado comercial vs remoto UE — respuestas distintas (documentar en README).

### Contexto y tokens

- No enviar todos los documentos en cada llamada.
- Truncar textos largos si hace falta.
- Documentar en README qué estrategia de selección de contexto usáis.

### Estrategia de selección de contexto (`context.py`)

Dos funciones, dos estrategias distintas porque resuelven problemas distintos:

**`seleccionar_contexto(pregunta, empleado)` — para el chat.**
Hay una pregunta libre, así que se puntúa por relevancia:
1. Se tokeniza la pregunta y el título+cuerpo+tags de cada doc (y pregunta+respuesta+tags de cada FAQ), en minúsculas y sin tildes, quitando stopwords en español.
2. Puntuación = nº de palabras en común entre la pregunta y el doc/FAQ, **+2 puntos de bonus** si el `departamento` del doc coincide con el `departamento` del empleado (para que, ante empate, gane el documento de su propio equipo).
3. Se ordenan por puntuación y se devuelven como máximo **3 docs + 2 FAQ** — no todo el JSON —, suficiente para cubrir la pregunta principal y un par de referencias, sin inflar el prompt ni el gasto de tokens.
4. **Fallback:** si nada puntúa por encima de 0 (pregunta ambigua o fuera de las palabras clave conocidas), se usa un contexto fijo mínimo (bienvenida + programa buddy) en vez de una lista vacía, para que el asistente tenga algo que citar antes de derivar a RRHH/IT.
5. **Truncado defensivo:** el `cuerpo` de cada doc devuelto se recorta a `MAX_CHARS_DOC` (500 caracteres) antes de entregarlo. Con los docs actuales (todos cortos) no recorta nada, pero protege si algún doc o artículo de convenio creciera.

**`seleccionar_docs_checklist(empleado, dia)` — para el checklist.**
No hay pregunta que buscar por palabras: ya sabemos el departamento y el día exacto, así que la selección es determinista, no por búsqueda:
1. `onboarding_docs.json` no tiene un campo `dia`. Los planes día a día de Engineering y Sales están escritos como texto libre dentro del `cuerpo` de `doc_eng_01` y `doc_sales_01` ("Día 1: ... Día 2: ..."). `context.py` parsea ese texto con una regex y recorta solo el fragmento del día pedido.
2. Departamentos sin ese plan redactado (`operations`, `people`, `it`, `curriculum`) no tienen un doc equivalente, así que usan un **fallback fijo por día** (`DOCS_GENERICOS_POR_DIA`) más el doc general de su propio departamento si existe (`doc_ops_01`, `doc_people_01`). Sin este fallback, empleados como `emp_04` (Operations) se quedarían sin checklist a partir del día 1.
3. `context.validar_datos()` avisa en consola qué empleados demo caen en este fallback, para que el equipo lo tenga presente al diseñar prompts/checklist en Parte 2.

### Gestión del estado (`state.py`)

`state.py` guarda, por sesión de chat, el empleado activo (`context.obtener_empleado()`), el día de onboarding simulado (1-5) y el historial de turnos:

- `crear_estado(empleado_id, dia=1)` → `EstadoConversacion`.
- `avanzar_dia(estado, dia)` → cambia el día (valida rango 1-5), sin tocar el historial.
- `registrar_turno(estado, pregunta, respuesta)` → añade un turno y recorta a los últimos `MAX_TURNOS_HISTORIAL` (4), tal como pide el enunciado ("historial conversacional acotado, máx. 4 turnos en el prompt").
- `historial_como_texto(estado)` → formatea el historial para meterlo en el prompt (p. ej. dentro de `<historial>`).

Es solo el "contenedor" del estado; no decide qué mostrar (eso sigue siendo `context.py`) ni construye el prompt (eso es `prompts.py`, Parte 2).

### Regla de escalado (`context.regla_escalado()`)

Da respuesta al punto 3 de Parte 1 ("acordar en el equipo cuándo escalar a RRHH, IT, manager u onboarding@bridgesa.example"), pero como función en vez de solo acuerdo en texto. Dado el resultado de `seleccionar_contexto()`, decide en este orden:

1. **Dato sensible** (salario, bonus, equity...) → siempre escala a People, sin mirar el contexto encontrado — refuerza la regla de "no responder sobre salarios ni datos de otros empleados".
2. **Sin contexto relevante** (ni docs ni FAQ, ni con fallback) → escala a `onboarding@bridgesa.example`.
3. **El doc mejor puntuado es de IT o People** → sugiere ese contacto como apoyo (no bloquea la respuesta).
4. **Cualquier otro caso** → no hace falta escalar; se puede responder con el contexto encontrado.

No bloquea nada por sí sola — eso es responsabilidad de `validators.py` en Parte 3 (fail-closed). `regla_escalado()` solo decide **a quién** derivar cuando haga falta.

---

# Parte 3 — Robustez

**Objetivo:** endurecer el sistema.

### Tareas

1. Validación de entrada (longitud, vacío, patrones sospechosos de inyección).
2. Rechazo **sin llamar al modelo** para fuera de dominio y datos sensibles.
3. Demo **vulnerable vs seguro** con el **mismo input** malicioso o límite.
4. Crear **5 casos trampa propios** (redacción del equipo; no copiar literalmente los ejemplos). Deben cubrir:
   - Inyección (“ignora instrucciones anteriores…”).
   - Pregunta salarial / bonus.
   - Fuera de dominio (p. ej. ayuda con un ejercicio de un programa formativo externo).
   - Política no documentada.
   - Ambigüedad baja médica vs laboral.
5. Consultad `data/casos_trampa_ejemplo.json` solo como referencia.
6. Documentar la comparativa vulnerable vs seguro (README del repo o doc breve).
---

# Parte 4 — Benchmark y decisión de modelo

**Objetivo:** elegir modelo con datos.

### Tareas

1. Dataset de benchmark — **mínimo 10 casos** (partid de `plantilla_preguntas_benchmark.json`).
2. Comparar **2 modelos** con la **misma** temperatura (recomendado: `0.2`) y el **mismo proveedor** (condiciones equivalentes).
3. Generar CSV e informe en `output/` (latencia, tokens).
4. Evaluar con `entregables/rubrica_benchmark.md` (escala 1–3).
5. Completar `entregables/matriz_decision.md` y `entregables/recomendacion.md`.
6. Incluir párrafo **«¿Qué pasaría si duplicáramos el tráfico?»** (tokens × volumen).

---

## Proveedor de modelos de IA

El enunciado está **planteado para Google Gemini**, pero si preferís **otro proveedor** (OpenAI, Cohere, Hugging Face, etc.), **podéis hacerlo**: adaptad el cliente en vuestro repo y documentad en el README qué API y modelos usáis.

**Parte 4:** el benchmark mínimo exige **2 modelos comparados** bajo las mismas condiciones. Por defecto se sugieren 2 modelos Gemini; si usáis otro proveedor, comparad 2 modelos de ese proveedor. 

**Opcional:** estudio **entre dos proveedores** (p. ej. Gemini vs OpenAI):

- Mismo subset de casos del benchmark (5–10 casos bastan).
- Misma temperatura y criterios de `entregables/rubrica_benchmark.md`.
- Comparar calidad, latencia, cumplimiento de JSON (checklist) y tokens.
---

## Requisitos técnicos

- Python 3.10+
- **API de un LLM** — el enunciado propone **Gemini** ([Google AI Studio](https://aistudio.google.com/)); otros proveedores válidos si lo documentáis en el README
- Claves en `.env` (p. ej. `GEMINI_API_KEY`); **nunca** en el repo
- Dependencias: `pip install -r requirements.txt`

**Entorno virtual (ejemplo):**

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # editar GEMINI_API_KEY
```

---

## Orden sugerido de las partes

Las cuatro partes tienen un orden lógico (contexto → asistente → robustez → benchmark), pero **cómo repartís el trabajo en 2 semanas lo decidís vosotros**.

---

## Presentación final (~10 min)

1. Contexto: qué problema resuelve el Employee Onboarding Assistant en Bridge SA.
2. Demo en vivo: conversación + checklist + un caso trampa en modo seguro.
3. Resultado del benchmark y modelo elegido.
4. Riesgo principal si lo desplegarais mañana.
5. Mostrar conclusiones reflejadas en vuestros entregables.
