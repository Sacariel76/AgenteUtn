
"""Cliente TCP de diagnóstico de AgenteUTN.

Compatible con el servidor de prueba de ping.
No ejecuta comandos remotos distintos de ping.
"""

import asyncio
import contextlib

from identity import build_hello, build_heartbeat
from protocol import encode_message, decode_message
from command_dispatcher import dispatch_command

HOST = "127.0.0.1"
PORT = 8767

HEARTBEAT_INTERVAL = 10
MAX_MESSAGE_SIZE = 65536


async def receive_messages(reader, writer):
    """Recibe mensajes y responde exclusivamente a ping."""

    while True:
        raw = await reader.readline()

        if not raw:
            print("El servidor cerró la conexión.")
            return

        if len(raw) > MAX_MESSAGE_SIZE:
            print("Mensaje demasiado grande. Desconectando.")
            return

        try:
            message = decode_message(raw)
        except (ValueError, UnicodeError) as error:
            print(f"Mensaje inválido: {error}")
            continue

        message_type = message.get("type")

        if (
            message_type == "command"
            and message.get("name") == "ping"
        ):
            try:
                response = dispatch_command(message)
            except (ValueError, KeyError) as error:
                print(f"PING inválido: {error}")
                continue

            writer.write(encode_message(response))
            await writer.drain()

            print(
                f"PING recibido: {message['id']} "
                "-> PONG enviado"
            )

        elif message_type == "bye":
            print("Servidor solicitó desconexión.")
            return

        elif message_type == "error":
            print(f"Error informado por servidor: {message}")
            return

        else:
            print(f"Mensaje ignorado: {message_type}")


async def send_heartbeats(writer):
    """Envía una señal de actividad cada diez segundos."""

    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL)

        writer.write(
            encode_message(build_heartbeat())
        )
        await writer.drain()

        print("HEARTBEAT enviado.")


async def connect_diagnostic(agent_id: str):
    """Establece conexión TCP con la VM de diagnóstico."""

    reader, writer = await asyncio.wait_for(
        asyncio.open_connection(HOST, PORT),
        timeout=5,
    )

    print(
        f"Conectado a VM de diagnóstico "
        f"{HOST}:{PORT}"
    )
    print(f"ID del agente: {agent_id}")
    print("Presioná Ctrl+C para desconectar.")

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
            with contextlib.suppress(asyncio.CancelledError):
                await task

        for task in done:
            task.result()

    finally:
        writer.close()
        await writer.wait_closed()
        print("Conexión de diagnóstico finalizada.")
