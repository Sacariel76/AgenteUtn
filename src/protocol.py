import json

MAX_MESSAGE_BYTES = 65536


def encode_message(message: dict) -> bytes:
    """Convierte un diccionario en una línea JSON."""
    data = (
        json.dumps(message, ensure_ascii=False, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")

    if len(data) > MAX_MESSAGE_BYTES:
        raise ValueError("Mensaje demasiado grande")

    return data


def decode_message(data: bytes) -> dict:
    """Valida y decodifica una línea JSON."""
    if not isinstance(data, bytes):
        raise ValueError("El mensaje debe ser bytes")
    if len(data) > MAX_MESSAGE_BYTES:
        raise ValueError("Mensaje demasiado grande")

    if not data.endswith(b"\n"):
        raise ValueError("El mensaje debe terminar en salto de línea")

    try:
        message = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Mensaje JSON inválido") from error

    if not isinstance(message, dict):
        raise ValueError("El mensaje debe ser un objeto JSON")

    return message
