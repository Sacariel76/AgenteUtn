
import unittest

from src.identity import build_hello, build_heartbeat


class TestIdentity(unittest.TestCase):

    def test_hello(self):
        message = build_hello("utn-prueba01")

        self.assertEqual(message["type"], "hello")
        self.assertTrue(message["agent_id"].startswith("utn-"))
        self.assertIn("hostname", message)
        self.assertIn("os", message)

    def test_heartbeat(self):
        message = build_heartbeat()

        self.assertEqual(message["type"], "heartbeat")
        self.assertIsInstance(message["ts"], float)


if __name__ == "__main__":
    unittest.main()
