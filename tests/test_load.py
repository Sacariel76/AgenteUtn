
"""Pruebas de la carga HTTP controlada (comando load)."""

import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "src")
)

from load_command import parse_target, run_load


class ParseTargetTests(unittest.TestCase):

    def test_puerto_por_defecto(self):
        self.assertEqual(
            parse_target("http://44.214.54.41"),
            ("44.214.54.41", 80, "/"),
        )

    def test_puerto_y_ruta(self):
        self.assertEqual(
            parse_target("http://44.214.54.41:8080/ruta?x=1"),
            ("44.214.54.41", 8080, "/ruta?x=1"),
        )

    def test_rechaza_https(self):
        with self.assertRaises(ValueError):
            parse_target("https://44.214.54.41")

    def test_rechaza_vacio(self):
        with self.assertRaises(ValueError):
            parse_target("")


class RunLoadTests(unittest.IsolatedAsyncioTestCase):

    async def test_inundacion_contra_servidor_local(self):
        async def handler(reader, writer):
            try:
                while True:
                    raw = await reader.readline()
                    if not raw:
                        break
                    if raw == b"\r\n":
                        writer.write(
                            b"HTTP/1.1 200 OK\r\n"
                            b"Content-Length: 2\r\n"
                            b"Connection: close\r\n"
                            b"\r\n"
                            b"ok"
                        )
                        await writer.drain()
                        break
            finally:
                writer.close()
                await writer.wait_closed()

        server = await asyncio.start_server(handler, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        async with server:
            data = await run_load(
                f"http://127.0.0.1:{port}/",
                duration=1,
                concurrency=3,
            )

        self.assertGreaterEqual(data["sent"], 1)
        self.assertGreaterEqual(data["errors"], 0)
        self.assertEqual(data["duration_s"], 1)
        self.assertGreater(data["rps"], 0)

    async def test_target_invalido_lanza_error(self):
        with self.assertRaises(ValueError):
            await run_load("ftp://nada", duration=1, concurrency=1)

    def test_duracion_no_numerica_usa_default(self):
        from load_command import _as_int
        self.assertEqual(_as_int("no-numerico", 30), 30)
        self.assertEqual(_as_int(15, 30), 15)
        self.assertEqual(_as_int(None, 30), 30)


if __name__ == "__main__":
    unittest.main()
