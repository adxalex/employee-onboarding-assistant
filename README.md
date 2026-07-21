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
flowchart TD
    CONFIG["config.py<br/>modelos · temperatura · límites"]

    subgraph DATOS["data/ — datos del reto"]
        D1[("onboarding_docs.json<br/>faq_onboarding.json<br/>empleados_demo.json<br/>convenio.json")]
        D2[("dataset_benchmark.json")]
    end

    subgraph P1["Parte 1 · David — Contexto y datos"]
        CONTEXT["context.py<br/>seleccionar_contexto<br/>seleccionar_docs_checklist"]
        STATE["state.py<br/>crear_estado · historial ≤4"]
    end

    subgraph P2["Parte 2 · Mihaela — Asistente modular"]
        PROMPTS["prompts.py<br/>construir_prompt_chat<br/>construir_prompt_checklist"]
        AUTH["gemini_auth.py<br/>carga API key"]
        CLIENT["gemini_client.py<br/>llamada a Gemini"]
        LOGIC["logic.py<br/>responder_chat<br/>generar_checklist"]
        MAIN["main.py<br/>demos 1-5"]
    end

    subgraph P3["Parte 3 · Jose — Robustez"]
        VAL["validators.py<br/>validar_entrada"]
    end

    subgraph P4["Parte 4 · Adixon — Benchmark"]
        BLLM["bench_llm.py<br/>Gemini + DeepSeek"]
        BENCH["benchmark.py<br/>runner del benchmark"]
        EVAL["evaluar.py<br/>chequeos + matriz"]
        LIST["list_modelos.py<br/>utilidad"]
    end

    OUT[("output/<br/>benchmark_*.csv + .json")]
    MATRIZ[("entregables/<br/>matriz_decision.md")]

    D1 --> CONTEXT
    CONTEXT --> STATE
    CONFIG --> CLIENT
    AUTH --> CLIENT
    CONFIG --> VAL
    CONTEXT --> VAL

    CONTEXT --> LOGIC
    STATE --> LOGIC
    PROMPTS --> LOGIC
    CLIENT --> LOGIC

    LOGIC --> MAIN
    STATE --> MAIN
    VAL --> MAIN

    D2 --> BENCH
    CONTEXT --> BENCH
    STATE --> BENCH
    PROMPTS --> BENCH
    BLLM --> BENCH
    BENCH --> OUT
    OUT --> EVAL
    D2 --> EVAL
    EVAL --> MATRIZ

    classDef p1 fill:#1f6f4a,stroke:#0d3b28,color:#fff
    classDef p2 fill:#1f4e79,stroke:#0d2b45,color:#fff
    classDef p3 fill:#7a3b1f,stroke:#452110,color:#fff
    classDef p4 fill:#5c2d82,stroke:#33174a,color:#fff
    classDef shared fill:#4a4a4a,stroke:#222,color:#fff
    classDef file fill:#2f2f2f,stroke:#111,color:#ddd

    class CONTEXT,STATE p1
    class PROMPTS,AUTH,CLIENT,LOGIC,MAIN p2
    class VAL p3
    class BLLM,BENCH,EVAL,LIST p4
    class CONFIG shared
    class D1,D2,OUT,MATRIZ file
```

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
