
import asyncio

from protocol import encode_message, decode_message


async def main():
    reader, writer = await asyncio.open_connection(
        "127.0.0.1", 9000
    )

    try:
        message = {
            "type": "hello",
            "agent_id": "laboratorio-local"
        }

        writer.write(encode_message(message))
        await writer.drain()

        response = await asyncio.wait_for(
            reader.readline(), timeout=5
        )

        print("Respuesta:", decode_message(response))

    finally:
        writer.close()
        await writer.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
