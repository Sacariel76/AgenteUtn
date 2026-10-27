
import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "src")
)

from src.protocol import encode_message, decode_message
from src.commands import handle_command
from src.aws_client import receive_messages, EXIT_STOP


async def _echo_handlers():
    """Devuelve helpers de sesión que registran los frames enviados."""
    sent = []

    async def send_message(message):
        sent.append(message)

    async def start_load(message):
        sent.append({
            "type": "result",
            "id": message.get("id"),
            "status": "error",
            "data": {"error": "sin carga en esta prueba"},
        })

    async def stop_load():
        pass

    return sent, send_message, start_load, stop_load


class TestIntegration(unittest.IsolatedAsyncioTestCase):

    async def test_ping_info_echo_generan_resultado_con_mismo_id(self):
        sent, send_message, start_load, stop_load = await _echo_handlers()

        async def handler(reader, writer):
            try:
                for name, command_id in (
                    ("ping", "p-1"),
                    ("info", "i-1"),
                    ("echo", "e-1"),
                ):
                    writer.write(encode_message({
                        "type": "command",
                        "id": command_id,
                        "name": name,
                        "args": {"text": "hola"} if name == "echo" else {},
                    }))
                    await writer.drain()
                for _ in range(3):
                    await asyncio.wait_for(
                        reader.readline(), timeout=2
                    )
            finally:
                writer.close()
                await writer.wait_closed()

        server = await asyncio.start_server(handler, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        async with server:
            reader, writer = await asyncio.open_connection(
                "127.0.0.1", port
            )
            try:
                task = asyncio.create_task(
                    receive_messages(
                        reader, writer,
                        send_message, start_load, stop_load,
                    )
                )
                await task
                self.assertEqual(
                    [(item["id"], item["status"]) for item in sent],
                    [("p-1", "ok"), ("i-1", "ok"), ("e-1", "ok")],
                )
                self.assertIn("hostname", sent[1]["data"])
                self.assertEqual(sent[2]["data"]["text"], "hola")
            finally:
                writer.close()
                await writer.wait_closed()

    async def test_stop_cierra_la_sesion_sin_reconectar(self):
        sent, send_message, start_load, stop_load = await _echo_handlers()

        async def handler(reader, writer):
            try:
                writer.write(encode_message({
                    "type": "command",
                    "id": "s-1",
                    "name": "stop",
                    "args": {},
                }))
                await writer.drain()
                await asyncio.wait_for(
                    reader.readline(), timeout=2
                )
            finally:
                writer.close()
                await writer.wait_closed()

        server = await asyncio.start_server(handler, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        async with server:
            reader, writer = await asyncio.open_connection(
                "127.0.0.1", port
            )
            try:
                code = await receive_messages(
                    reader, writer,
                    send_message, start_load, stop_load,
                )
            finally:
                writer.close()
                await writer.wait_closed()

        self.assertEqual(code, EXIT_STOP)
        self.assertTrue(sent[0]["data"]["stopping"])

    async def test_comunicacion_cliente_servidor(self):

        async def server_handler(reader, writer):
            try:
                command = {
                    "type": "command",
                    "id": "test-001",
                    "name": "ping",
                    "args": {},
                }

                writer.write(encode_message(command))
                await writer.drain()

                line = await asyncio.wait_for(
                    reader.readline(), timeout=5
                )
                response = decode_message(line)

                self.assertEqual(response["id"], "test-001")
                self.assertEqual(response["status"], "ok")
                self.assertTrue(response["data"]["pong"])

            finally:
                writer.close()
                await writer.wait_closed()

        server = await asyncio.start_server(
            server_handler, "127.0.0.1", 0
        )

        port = server.sockets[0].getsockname()[1]

        async with server:
            reader, writer = await asyncio.open_connection(
                "127.0.0.1", port
            )

            try:
                line = await asyncio.wait_for(
                    reader.readline(), timeout=5
                )
                command = decode_message(line)

                response = handle_command(command)
                writer.write(encode_message(response))
                await writer.drain()

                await asyncio.sleep(0.1)

            finally:
                writer.close()
                await writer.wait_closed()


if __name__ == "__main__":
    unittest.main()
