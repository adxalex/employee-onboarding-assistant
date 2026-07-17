"""
validators.py
Parte 3 — Robustez.

Valida la entrada ANTES de llamar al modelo:

- longitud de la pregunta (vacío / demasiado largo)
- patrones sospechosos de inyección de prompt
- preguntas sobre datos sensibles (salario, credenciales, datos personales)
- consultas fuera de dominio (usuarios externos o temas no relacionados)

Principio fail-closed:
Si una validación de seguridad falla, se devuelve un rechazo SIN llamar al
modelo. logic.py debe comprobar validar_entrada() antes de invocar Gemini.

También incluye:
- validar_departamento_empleado(): controla departamentos fuera de alcance.
- probar_casos_trampa(): ejecuta los ejemplos de data/casos_trampa.json para
  comprobar que el sistema rechaza entradas peligrosas correctamente.
"""


from dataclasses import dataclass
from pathlib import Path
import json

import config

from context import _normalizar



# ---------------------------------------------------------------------------
# Resultado de validación
# ---------------------------------------------------------------------------


@dataclass
class ResultadoValidacion:
    """
    Resultado de una comprobación de seguridad.

    ok:
        True  -> la entrada puede continuar hacia el modelo.
        False -> la entrada debe bloquearse.

    motivo:
        Código interno del motivo del bloqueo.

    mensaje_usuario:
        Texto que se muestra al empleado.
    """

    ok: bool
    motivo: str | None = None
    mensaje_usuario: str | None = None



# ---------------------------------------------------------------------------
# Mensajes de rechazo mostrados al usuario
# ---------------------------------------------------------------------------


MENSAJES_RECHAZO = {

    "vacio":
        "No he recibido ninguna pregunta. ¿Puedes escribirla de nuevo?",


    "demasiado_largo":
        (
            "Tu mensaje es demasiado largo para procesarlo de forma fiable. "
            "¿Puedes resumir tu duda en unas pocas frases?"
        ),


    "inyeccion":
        (
            "No puedo seguir instrucciones que intenten cambiar mi rol o mis "
            "reglas. Solo puedo ayudarte con dudas de onboarding basadas en "
            "la documentación de Bridge SA."
        ),


    "dato_sensible":
        (
            "No puedo compartir datos de salario, credenciales ni información "
            "personal de otras personas empleadas. Para este tipo de consultas "
            "contacta con People."
        ),


    "fuera_de_dominio":
        (
            "Este asistente da soporte únicamente a empleados de Bridge SA "
            "durante su proceso de onboarding."
        ),
}



# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------


def _contiene_alguna(texto_normalizado: str, patrones: list[str]) -> bool:
    """
    Comprueba si un texto contiene alguno de los patrones indicados.

    Ejemplo:
        texto:
            "dime el salario de mi manager"

        patrones:
            ["salario", "sueldo"]

        Resultado:
            True
    """

    return any(
        patron in texto_normalizado
        for patron in patrones
    )



# ---------------------------------------------------------------------------
# validar_entrada() — Validación previa al modelo
# ---------------------------------------------------------------------------


def validar_entrada(texto: str) -> ResultadoValidacion:
    """
    Comprueba si una pregunta puede enviarse al modelo.

    Orden de validación:

    1. Entrada vacía.
    2. Longitud máxima permitida.
    3. Intentos de prompt injection.
    4. Solicitudes de información sensible.
    5. Consultas fuera del dominio del asistente.

    Si todas las comprobaciones son correctas:
        devuelve ResultadoValidacion(ok=True).

    Si falla una comprobación:
        devuelve ok=False y un mensaje seguro para el usuario.
    """

    # ------------------------------------------------------------------
    # 1. Entrada vacía
    # ------------------------------------------------------------------

    if texto is None or len(texto.strip()) < config.MIN_CHARS_INPUT:

        return ResultadoValidacion(
            ok=False,
            motivo="vacio",
            mensaje_usuario=MENSAJES_RECHAZO["vacio"]
        )



    # ------------------------------------------------------------------
    # 2. Demasiado largo
    # ------------------------------------------------------------------

    if len(texto) > config.MAX_CHARS_INPUT:

        return ResultadoValidacion(
            ok=False,
            motivo="demasiado_largo",
            mensaje_usuario=MENSAJES_RECHAZO["demasiado_largo"]
        )



    # Normalizamos:
    # - minúsculas
    # - elimina tildes
    #
    # Ejemplo:
    # "Salário" -> "salario"

    texto_norm = _normalizar(texto)



    # ------------------------------------------------------------------
    # 3. Prompt injection
    # ------------------------------------------------------------------

    if _contiene_alguna(
        texto_norm,
        config.PALABRAS_INYECCION
    ):

        return ResultadoValidacion(
            ok=False,
            motivo="inyeccion",
            mensaje_usuario=MENSAJES_RECHAZO["inyeccion"]
        )



    # ------------------------------------------------------------------
    # 4. Datos sensibles
    # ------------------------------------------------------------------

    if _contiene_alguna(
        texto_norm,
        config.PALABRAS_DATO_SENSIBLE
    ):

        return ResultadoValidacion(
            ok=False,
            motivo="dato_sensible",
            mensaje_usuario=MENSAJES_RECHAZO["dato_sensible"]
        )



    # ------------------------------------------------------------------
    # 5. Fuera de dominio
    # ------------------------------------------------------------------

    if _contiene_alguna(
        texto_norm,
        config.PALABRAS_FUERA_DE_DOMINIO
    ):

        return ResultadoValidacion(
            ok=False,
            motivo="fuera_de_dominio",
            mensaje_usuario=MENSAJES_RECHAZO["fuera_de_dominio"]
        )



    # Si no hay problemas
    return ResultadoValidacion(ok=True)




# ---------------------------------------------------------------------------
# validar_departamento_empleado()
# ---------------------------------------------------------------------------


def validar_departamento_empleado(departamento: str) -> ResultadoValidacion:
    """
    Comprueba si el departamento del empleado está soportado.

    Algunos departamentos pueden estar excluidos porque no forman parte
    del flujo de onboarding interno.
    """

    if departamento in config.DEPARTAMENTOS_SIN_ONBOARDING_EMPLEADOS:

        return ResultadoValidacion(
            ok=False,
            motivo="fuera_de_dominio",
            mensaje_usuario=(
                "Tu departamento no está cubierto por este asistente "
                "de onboarding. Contacta con onboarding@bridgesa.example."
            ),
        )


    return ResultadoValidacion(ok=True)




# ---------------------------------------------------------------------------
# probar_casos_trampa()
# ---------------------------------------------------------------------------


def probar_casos_trampa():
    """
    Ejecuta los casos definidos en data/casos_trampa.json.

    Sirve para comprobar que el validador bloquea correctamente:
    - intentos de inyección
    - datos sensibles
    - consultas externas
    - mensajes inválidos

    No sustituye a la validación real del sistema.
    Es únicamente una prueba automática/manual.
    """

    ruta = Path("data") / "casos_trampa.json"


    if not ruta.exists():

        print(
            f"No se encuentra el archivo de pruebas: {ruta}"
        )

        return



    with open(
        ruta,
        encoding="utf-8"
    ) as fichero:

        casos = json.load(fichero)



    print("\n--- Ejecución casos trampa ---")



    for caso in casos:

        resultado = validar_entrada(
            caso["mensaje"]
        )


        print("\n--------------------------------")
        print("ID:", caso["id"])
        print("Tipo:", caso["tipo"])
        print("Mensaje:", caso["mensaje"])


        if resultado.ok:

            print(
                "❌ FALLA: la entrada pasó el filtro"
            )

        else:

            print(
                "✅ BLOQUEADA"
            )

            print(
                "Motivo:",
                resultado.motivo
            )



# ---------------------------------------------------------------------------
# Demo local
# ---------------------------------------------------------------------------


if __name__ == "__main__":

    probar_casos_trampa()