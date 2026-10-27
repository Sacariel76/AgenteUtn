
"""Política de reconexión para pruebas locales."""

MAX_ATTEMPTS = 3
RETRY_SECONDS = 5


def reconnect_decision(event: dict, attempts: int = 0) -> dict:
    """Determina si corresponde reintentar una conexión."""

    if not isinstance(event, dict):
        raise ValueError("El evento debe ser un diccionario")

    if not isinstance(attempts, int) or attempts < 0:
        raise ValueError("Número de intentos inválido")

    if event.get("type") == "bye":
        return {"retry": False, "delay": 0}

    if event.get("type") == "error":
        if event.get("code") == "auth":
            return {"retry": False, "delay": 0}
        if event.get("code") != "busy":
            return {"retry": False, "delay": 0}

    elif event.get("type") != "connection_lost":
        return {"retry": False, "delay": 0}

    if attempts >= MAX_ATTEMPTS:
        return {"retry": False, "delay": 0}

    return {"retry": True, "delay": RETRY_SECONDS}
