import os
import getpass

from dotenv import load_dotenv

# Evita configurar la clave varias veces durante la misma ejecución
_configured = False


def configurar_gemini_api_key() -> None:
    global _configured

    if _configured:
        returns

    # Cargar variables del archivo .env
    load_dotenv()

    # Pedir la clave únicamente si no existe
    if not os.getenv("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = getpass.getpass(
            "Introduce tu GEMINI_API_KEY: "
        )

    print(
        "GEMINI_API_KEY configurada:",
        "sí" if os.getenv("GEMINI_API_KEY") else "no",
    )

    _configured = True