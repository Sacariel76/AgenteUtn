
import getpass
import platform
import socket
import time


VERSION = "1.8"


def build_hello(agent_id: str, secret: str = "") -> dict:
    """Construye un mensaje de identificación compatible
    con el formato JSON documentado del laboratorio.
    """
    return {
        "type": "hello",
        "agent_id": agent_id,
        "hostname": socket.gethostname(),
        "os": f"{platform.system()} {platform.release()}",
        "user": getpass.getuser(),
        "version": VERSION,
        "secret": secret,
    }


def build_heartbeat() -> dict:
    """Construye una señal de actividad."""
    return {
        "type": "heartbeat",
        "ts": time.time(),
    }
