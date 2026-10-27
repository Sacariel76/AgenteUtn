
"""
AgenteUTN - aws_client.py
Versión 1.7 - Cliente TCP de diagnóstico

Funciones:
- Conexión TCP a la VM de diagnóstico
- Envío de HELLO
- Envío periódico de HEARTBEAT
- Recepción de PING
- Envío de PONG con el ID original
- Manejo de ERROR y BYE
- Cierre ordenado de conexión

Solo admite PING como comando remoto.
"""

import asyncio
import contextlib

from identity import build_hello, build_heartbeat
from protocol import encode_message, decode_message
from command_dispatcher import dispatch_command


# Configuración del túnel SSH de diagnóstico
HOST = "54.88.121.40"
PORT = 8443

HEARTBEAT_INTERVAL = 10
MAX_MESSAGE_SIZE = 65536
CONNECT_TIMEOUT = 5


async def receive_messages(reader, writer):
    """Recibe comandos de diagnóstico y responde con el mismo ID."""

    while True:
        try:
            raw = await reader.readline()

        except asyncio.LimitOverrunError:
            print("Mensaje demasiado grande.")
            return

        if not raw:
            print("El servidor cerró la conexión.")
            return

        if len(raw) > MAX_MESSAGE_SIZE:
            print("Mensaje demasiado grande.")
            return

        try:
            message = decode_message(raw)

        except (ValueError, UnicodeError) as error:
            print(f"Mensaje inválido: {error}")
            continue

        message_type = message.get("type")

        if (message_type == "command" and
                message.get("name") in {"ping", "info"}):
            try:
                response = dispatch_command(message)

            except (ValueError, KeyError) as error:
                error_response = {
                    "type": "result",
                    "id": message.get("id"),
                    "status": "error",
                    "data": {"error": str(error)},
                }
                writer.write(encode_message(error_response))
                await writer.drain()
                continue

            writer.write(encode_message(response))
            await writer.drain()

            print(
                f"Comando recibido: {message['name']} "
                f"({message['id']}) -> resultado enviado"
            )

        elif message_type == "command":
            response = {
                "type": "result",
                "id": message.get("id"),
                "status": "error",
                "data": {"error": "Comando no permitido"},
            }
            writer.write(encode_message(response))
            await writer.drain()

        elif message_type == "bye":
            print("El servidor solicitó la desconexión.")
            return

        elif message_type == "error":
            code = message.get("code", "desconocido")
            print(f"Error del servidor: {code}")
            return

        else:
            print(
                f"Mensaje ignorado: {message_type}"
            )


async def send_heartbeats(writer):
    """Envía HEARTBEAT cada diez segundos."""

    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL)

        writer.write(
            encode_message(build_heartbeat())
        )

        await writer.drain()

        print("HEARTBEAT enviado.")


async def connect_diagnostic(agent_id: str):
    """Establece la sesión de diagnóstico TCP."""

    print("\nConectando a la VM de diagnóstico...")
    print(f"Destino: {HOST}:{PORT}")
    print(f"Agente: {agent_id}")
    print("Presioná Ctrl+C para desconectar.")

    reader, writer = await asyncio.wait_for(
        asyncio.open_connection(
            HOST,
            PORT,
            limit=MAX_MESSAGE_SIZE,
        ),
        timeout=CONNECT_TIMEOUT,
    )

    receiver = None
    heartbeat = None

    try:
        writer.write(
            encode_message(build_hello(agent_id))
        )
        await writer.drain()

        print("HELLO enviado.")

        receiver = asyncio.create_task(
            receive_messages(reader, writer)
        )

        heartbeat = asyncio.create_task(
            send_heartbeats(writer)
        )

        done, pending = await asyncio.wait(
            {receiver, heartbeat},
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()

        for task in pending:
            with contextlib.suppress(
                asyncio.CancelledError
            ):
                await task

        for task in done:
            task.result()

    finally:
        for task in (receiver, heartbeat):
            if task is not None and not task.done():
                task.cancel()
                with contextlib.suppress(
                    asyncio.CancelledError
                ):
                    await task

        writer.close()
        await writer.wait_closed()

        print("Conexión finalizada.")
