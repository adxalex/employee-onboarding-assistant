# Recomendación de modelo — Employee Onboarding Assistant

**Ejecución de referencia:** `benchmark_ambos_20260723_152802` — 15 casos × 4 modelos
(2 Gemini + 2 DeepSeek), temperatura 0.2, mismas condiciones (mismo prompt por caso,
construido con `context` + `prompts` reales del asistente).

---

## Modelo recomendado: `gemini-flash-lite-latest`

Para el **chat en tiempo real** del onboarding, recomendamos **`gemini-flash-lite-latest`**.

| Modelo | Latencia media | Tokens medios | Rúbrica (1–3) | Chequeos auto |
|--------|---------------:|--------------:|:-------------:|:-------------:|
| **gemini-flash-lite-latest** | **1.4 s** | **842** | 2.90 | 6/8 |
| gemini-3.5-flash | 6.5 s | 858 | 2.92 | 7/8 |
| deepseek-chat | 3.0 s | 890 | 2.97 | 7/8 |
| deepseek-reasoner | 5.0 s | 1112 | 2.97 | 7/8 |

### Por qué

1. **La calidad es un empate técnico.** Los cuatro modelos puntúan entre 2.90 y 2.97
   sobre 3 en la rúbrica (fidelidad, relevancia, tono). Ninguno destaca en calidad de
   forma decisiva, así que la elección se dirime en **latencia y coste**.

2. **Es el más rápido, con diferencia.** 1.4 s de media frente a los 6.5 s de
   `gemini-3.5-flash` (**~5× más rápido**). En un chat que un empleado usa en directo,
   la latencia es lo que define si la experiencia se siente fluida o lenta.

3. **Es el más barato.** Menor consumo de tokens de salida → menor coste por consulta.

4. **La seguridad no penaliza la elección.** Los cuatro modelos rechazaron o derivaron
   correctamente los cinco casos trampa (salario, inyección de prompt, fuera de dominio,
   política inexistente, ambigüedad médica). La robustez la aporta el **prompt**, no el
   modelo; por eso todos aprueban y la seguridad no es el criterio diferenciador.

### Alternativa
`deepseek-chat` (rúbrica 2.97, 3.0 s) es la opción **si se prioriza calidad sobre
velocidad**, y sirve además como respaldo cross-proveedor (evita depender de un único
proveedor).

### No recomendados
- **`gemini-3.5-flash`**: el más lento (hasta 10.8 s en checklists) sin ventaja de
  calidad, y con una **alucinación** detectada (inventó "26 días" de vacaciones en
  bench_03, cifra no documentada).
- **`deepseek-reasoner`**: buena calidad, pero **+30% de tokens** (1112 vs 842) y más
  lento por su razonamiento interno. Caro para un chat de alto volumen.

---

## Riesgo principal si se desplegara mañana

La **diferenciación por día de onboarding es gruesa**: el prompt solo distingue día 1
vs día ≥3 explícitamente, así que en días 2, 4 y 5 el asistente apenas cambia su
comportamiento. Además, los modelos "pensantes" (3.5-flash, reasoner) pueden **truncar
el checklist JSON** si el presupuesto de tokens no contempla el razonamiento — hay que
fijar `thinking_budget=0` o subir `MAX_OUTPUT_TOKENS_CHECKLIST` antes de producción.

---

## ¿Qué pasaría si duplicáramos el tráfico?

**Escenario base (estimado):** ~10 empleados nuevos al mes, cada uno con ~30
interacciones durante su primera semana → **~300 consultas/mes**.

Con el modelo recomendado (`gemini-flash-lite-latest`, 842 tokens/consulta, de los que
**677 son de entrada** y 165 de salida):

| | Consultas/mes | Tokens de entrada | Tokens de salida | Tokens totales |
|--|--:|--:|--:|--:|
| **Base** | 300 | 203.100 | 49.500 | **252.600** |
| **Tráfico ×2** | 600 | 406.200 | 99.000 | **505.200** |

**El coste escala de forma prácticamente lineal:** doblar el tráfico ≈ doblar los tokens
≈ doblar el coste de API. No hay economías de escala automáticas — cada consulta paga su
propio contexto.

**El punto clave para controlar el coste está en la ENTRADA, no en la salida.** El 80%
de los tokens (677 de 842) son el **contexto que enviamos** en cada prompt (los docs y
FAQ seleccionados). Por tanto, si el tráfico se duplica, la palanca más efectiva para
contener el gasto no es acortar las respuestas, sino **afinar la selección de contexto**
(`context.py`): enviar menos documentos o truncarlos más agresivamente reduce el coste de
**cada** llamada.

**Cuidado con los modelos pensantes a escala:** `deepseek-reasoner` gasta 396 tokens de
salida (2.4× los 165 de flash-lite). Con el tráfico duplicado, esa diferencia se amplifica
y encarece notablemente la factura — otra razón para preferir un modelo ligero en
alto volumen.
