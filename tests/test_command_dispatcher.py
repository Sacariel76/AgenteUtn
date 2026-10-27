
import sys
import unittest
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "src")
)

from command_dispatcher import dispatch_command


class TestCommandDispatcher(unittest.TestCase):

    def test_ping(self):
        result = dispatch_command({
            "type": "command",
            "id": "abc123",
            "name": "ping",
            "args": {},
        })

        self.assertEqual(result["type"], "result")
        self.assertEqual(result["id"], "abc123")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["data"], {"pong": True})

    def test_info(self):
        result = dispatch_command({
            "type": "command",
            "id": "abc124",
            "name": "info",
            "args": {},
        })

        self.assertEqual(result["status"], "ok")
        self.assertIsInstance(result["data"], dict)

    def test_comando_no_permitido(self):
        result = dispatch_command({
            "type": "command",
            "id": "abc125",
            "name": "load",
            "args": {},
        })

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["id"], "abc125")

    def test_id_obligatorio(self):
        with self.assertRaises(ValueError):
            dispatch_command({
                "type": "command",
                "name": "ping",
                "args": {},
            })


if __name__ == "__main__":
    unittest.main()
