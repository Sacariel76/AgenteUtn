
import asyncio
import unittest

from src.protocol import encode_message, decode_message
from src.commands import handle_command
from src.aws_client import receive_messages


class TestIntegration(unittest.IsolatedAsyncioTestCase):

    async def test_ping_e_info_generan_resultado_con_mismo_id(self):
        responses = []
        async def handler(reader, writer):
            try:
                for name, command_id in (("ping", "p-1"), ("info", "i-1")):
                    writer.write(encode_message({
                        "type": "command", "id": command_id,
                        "name": name, "args": {},
                    }))
                    await writer.drain()
                for _ in range(2):
                    responses.append(decode_message(await asyncio.wait_for(
                        reader.readline(), timeout=2
                    )))
            finally:
                writer.close()
                await writer.wait_closed()

        server = await asyncio.start_server(handler, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        async with server:
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            try:
                task = asyncio.create_task(receive_messages(reader, writer))
                await task
                self.assertEqual(
                    [(item["id"], item["status"]) for item in responses],
                    [("p-1", "ok"), ("i-1", "ok")],
                )
                self.assertIn("hostname", responses[1]["data"])
            finally:
                writer.close()
                await writer.wait_closed()

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
