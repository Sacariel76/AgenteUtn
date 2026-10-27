
import platform
import socket


def handle_command(message: dict) -> dict:
    command_id = message.get("id")
    name = message.get("name")

    if name == "ping":
        return {
            "type": "result",
            "id": command_id,
            "status": "ok",
            "data": {"pong": True},
        }

    if name == "info":
        return {
            "type": "result",
            "id": command_id,
            "status": "ok",
            "data": {
                "hostname": socket.gethostname(),
                "os": platform.platform(),
                "python": platform.python_version(),
            },
        }

    if name == "stop":
        return {
            "type": "result",
            "id": command_id,
            "status": "ok",
            "data": {"stopping": True},
        }

    return {
        "type": "result",
        "id": command_id,
        "status": "error",
        "data": {"error": "Comando no soportado"},
    }
