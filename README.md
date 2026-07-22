# Employee Onboarding Assistant — Bridge SA

Copiloto que acompaña a **empleados nuevos** en sus primeros días: responde dudas
con la documentación interna, genera el checklist del día y sabe cuándo derivar a
People o IT.

Team Challenge · Sprint 05–07 — Bootcamp AI Engineering (The Bridge).

---

## Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/adxalex/employee-onboarding-assistant.git
cd employee-onboarding-assistant

# 2. Entorno virtual
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 3. Dependencias
pip install -r requirements.txt

# 4. Claves de API
copy .env.example .env        # Windows  (cp en macOS/Linux)
```

Edita el `.env` con tus claves:

```env
GEMINI_API_KEY=tu_clave
GEMINI_MODELS=gemini-2.5-flash,gemini-3.5-flash

DEEPSEEK_API_KEY=tu_clave
DEEPSEEK_MODELS=deepseek-chat,deepseek-reasoner

# Qué corre el benchmark: deepseek | gemini | ambos
BENCH_MODE=gemini
```

> El `.env` está en `.gitignore` — **nunca se sube al repositorio**.
> Para ver qué modelos acepta tu cuenta: `python list_modelos.py`

---

## Cómo ejecutar

```bash
python main.py 1     # Parte 2 — chat (dev junior, día 1)
python main.py 2     # Parte 2 — checklist JSON del día
python main.py 3     # Partes 1+2 — misma pregunta: comercial vs remoto UE
python main.py 4     # transversal — día 1 vs día 3
python main.py 5     # Parte 3 — vulnerable vs seguro
python main.py       # todas las demos

python benchmark.py  # Parte 4 — corre el benchmark según BENCH_MODE
python evaluar.py    # Parte 4 — genera entregables/matriz_decision.md
```

---

## Arquitectura: integración entre módulos

Diagrama generado a partir de los `import` reales de cada módulo.

```mermaid
flowchart TB
    DATA[("data/*.json")]
    CFG["config.py"]
    DS[("dataset_benchmark.json")]

    subgraph ASIS["ASISTENTE — responde al empleado"]
        direction TB
        CTX["context.py"]
        ST["state.py"]
        PR["prompts.py"]
        CL["gemini_client.py"]
        LO["logic.py"]
        VAL["validators.py"]
        MA["main.py"]
    end

    subgraph BENCH["BENCHMARK — Parte 4"]
        direction TB
        BL["bench_llm.py"]
        BE["benchmark.py"]
        EV["evaluar.py"]
    end

    OUT[("output/ + matriz")]

    %% Flujo principal del asistente (linea solida = camino directo)
    DATA --> CTX
    CTX --> ST
    CTX --> PR
    ST --> LO
    PR --> LO
    CL --> LO
    LO --> MA
    VAL --> MA

    %% config es transversal (punteado)
    CFG -.-> CL
    CFG -.-> VAL

    %% Flujo del benchmark (linea solida)
    DS --> BE
    BL --> BE
    BE --> EV
    EV --> OUT

    %% El benchmark REUTILIZA modulos del asistente (punteado)
    CTX -. reutiliza .-> BE
    PR -. reutiliza .-> BE
    ST -. reutiliza .-> BE

    classDef asis fill:#1f4e79,stroke:#0d2b45,color:#fff
    classDef bench fill:#5c2d82,stroke:#33174a,color:#fff
    classDef ext fill:#2f2f2f,stroke:#111,color:#eee

    class CTX,ST,PR,CL,LO,VAL,MA asis
    class BL,BE,EV bench
    class DATA,CFG,DS,OUT ext
```

> **Cómo leerlo:** las líneas **sólidas** son el camino principal de cada bloque;
> las **punteadas** son conexiones transversales (`config` global y los módulos que
> el benchmark **reutiliza** del asistente).

**Nota de diseño:** `benchmark.py` **no pasa por `logic.py`**. Orquesta directamente
`context` → `prompts` → `bench_llm`, porque cada caso del benchmark debe ser
independiente (`logic.py` acumula historial, pensado para chat interactivo).

---

## Recorrido de una petición en ejecución

```mermaid
flowchart LR
    A["Entrada<br/>empleado + día 1-5 + pregunta"] --> B{"validar_entrada<br/>P3 · Jose"}
    B -->|"falla"| R["RECHAZO fail-closed<br/>no se llama al modelo<br/>deriva a People / IT"]
    B -->|"ok"| C["seleccionar_contexto<br/>P1 · David<br/>máx 3 docs + 2 FAQ"]
    C --> D["construir_prompt<br/>P2 · Mihaela<br/>delimitadores + día + historial"]
    D --> E["gemini_client<br/>P2 · Mihaela<br/>llamada al LLM"]
    E --> F["Salida A: CHAT<br/>texto breve con fuentes"]
    E --> G["Salida B: CHECKLIST<br/>JSON del día"]

    classDef p1 fill:#1f6f4a,stroke:#0d3b28,color:#fff
    classDef p2 fill:#1f4e79,stroke:#0d2b45,color:#fff
    classDef p3 fill:#7a3b1f,stroke:#452110,color:#fff
    classDef alerta fill:#8b2c2c,stroke:#4a1414,color:#fff

    class C p1
    class D,E p2
    class B p3
    class R alerta
```

---

## Mapa de módulos, partes y responsables

| Módulo | Parte | Responsable | Qué hace | Depende de |
|--------|-------|-------------|----------|------------|
| `config.py` | común | David | Modelos, temperatura, límites | — |
| `context.py` | 1 | David | Carga `data/` y selecciona docs/FAQ relevantes | — |
| `state.py` | 1 | David | Empleado + día + historial (≤4 turnos) | `context` |
| `prompts.py` | 2 | Mihaela | Construye los prompts con delimitadores | — |
| `gemini_auth.py` | 2 | Mihaela | Carga `GEMINI_API_KEY` desde `.env` | — |
| `gemini_client.py` | 2 | Mihaela | Llamada a Gemini | `config`, `gemini_auth` |
| `logic.py` | 2 | Mihaela | Orquesta chat y checklist | `context`, `state`, `prompts`, `gemini_client` |
| `main.py` | 2 | Mihaela | Demos 1-5 ejecutables | `logic`, `state`, `validators` |
| `validators.py` | 3 | Jose | Validación fail-closed de la entrada | `config`, `context` |
| `bench_llm.py` | 4 | Adixon | Cliente multi-proveedor (Gemini/DeepSeek) | — |
| `benchmark.py` | 4 | Adixon | Corre el dataset contra N modelos y mide | `context`, `state`, `prompts`, `bench_llm` |
| `evaluar.py` | 4 | Adixon | Chequeos automáticos + matriz de decisión | — |
| `list_modelos.py` | 4 | Adixon | Lista los modelos disponibles de la cuenta | — |

---

## Requisitos técnicos

- Python 3.10+
- Dependencias en `requirements.txt`: `google-genai`, `openai`, `python-dotenv`
- Claves en `.env` (nunca en el repositorio)
