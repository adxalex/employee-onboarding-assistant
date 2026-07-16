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
