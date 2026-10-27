
import asyncio
import contextlib

from identity import build_hello, build_heartbeat
from protocol import encode_message, decode_message
from command_dispatcher import dispatch_command

HOST = "54.88.121.40"
PORT = 8443
HEARTBEAT_INTERVAL = 10
MAX_MESSAGE_SIZE = 65536


async def recibir_mensajes(reader, writer):
    """Recibe mensajes y responde exclusivamente a ping."""

    while True:
        raw = await reader.readline()

        if not raw:
            print("Servidor desconectado.")
            return

        if len(raw) > MAX_MESSAGE_SIZE:
            print("Mensaje demasiado grande.")
            return

        try:
            mensaje = decode_message(raw)
        except (ValueError, UnicodeError) as error:
            print(f"Mensaje inválido: {error}")
            continue

        if (
            mensaje.get("type") == "command"
            and mensaje.get("name") == "ping"
        ):
            try:
                respuesta = dispatch_command(mensaje)
            except (ValueError, KeyError) as error:
                print(f"PING inválido: {error}")
                continue

            writer.write(encode_message(respuesta))
            await writer.drain()

            print(
                f"PING recibido: {mensaje['id']} "
                "-> PONG enviado"
            )

        elif mensaje.get("type") in ("bye", "error"):
            print(f"Servidor informó: {mensaje}")
            return

        else:
            print("Mensaje ignorado.")


async def enviar_heartbeat(writer):
    """Envía señales periódicas de actividad."""

    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL)

        writer.write(encode_message(build_heartbeat()))
        await writer.drain()

        print("HEARTBEAT enviado.")


async def iniciar_cliente(agent_id, host=HOST, port=PORT):
    reader, writer = await asyncio.wait_for(
        asyncio.open_connection(host, port),
        timeout=5,
    )

    print(f"Conectado a VM de diagnóstico: {agent_id}")

    try:
        writer.write(encode_message(build_hello(agent_id)))
        await writer.drain()
        print("HELLO enviado.")

        receiver = asyncio.create_task(
            recibir_mensajes(reader, writer)
        )
        heartbeat = asyncio.create_task(
            enviar_heartbeat(writer)
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
        print("Conexión cerrada.")
