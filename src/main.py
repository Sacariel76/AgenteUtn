
"""AgenteUTN - Aplicación principal de laboratorio."""

import asyncio
import json
import time
import uuid
import urllib.error
import urllib.request

from identity import build_hello, build_heartbeat
from commands import handle_command
from protocol import encode_message, decode_message
from aws_client import connect_diagnostic, EXIT_RETRY
from reconnect_policy import reconnect_decision


VERSION = "1.8"
VICTIMA_URL = "http://44.214.54.41/"


def mostrar(mensaje):
    """Muestra información JSON en consola."""
    print(
        json.dumps(
            mensaje,
            ensure_ascii=False,
            indent=2,
        )
    )


def verificar_victima():
    """Realiza una única solicitud HTTP de diagnóstico."""

    print("\nVerificando servidor víctima...")

    inicio = time.perf_counter()

    try:
        with urllib.request.urlopen(
            VICTIMA_URL,
            timeout=5,
        ) as respuesta:
            codigo = respuesta.status
            respuesta.read(1024)

        milisegundos = (
            time.perf_counter() - inicio
        ) * 1000

        print(f"Servidor: {VICTIMA_URL}")
        print(f"HTTP: {codigo}")
        print(f"Tiempo: {milisegundos:.2f} ms")

    except (
        urllib.error.URLError,
        TimeoutError,
    ) as error:
        print(f"Error de conexión: {error}")


def ejecutar_comando(nombre):
    """Ejecuta un comando de diagnóstico local."""

    mensaje = {
        "type": "command",
        "id": "diagnostico-local",
        "name": nombre,
        "args": {},
    }

    resultado = handle_command(
        decode_message(
            encode_message(mensaje)
        )
    )

    mostrar(resultado)


def conectar_vm(agent_id):
    """Conecta al C2 con reconexión automática según la política."""
    print("\nIniciando conexión con el servidor C2...")

    attempts = 0

    while True:
        try:
            exit_code = asyncio.run(connect_diagnostic(agent_id))

        except KeyboardInterrupt:
            print("\nDesconectado por el usuario.")
            return

        except (OSError, asyncio.TimeoutError) as error:
            print(f"\nError de conexión: {error}")
            exit_code = EXIT_RETRY

        if exit_code != EXIT_RETRY:
            print("\nSesión finalizada.")
            return

        attempts += 1

        decision = reconnect_decision(
            {"type": "connection_lost"},
            attempts=attempts,
        )

        if not decision["retry"]:
            print("\nReintentos agotados; el agente queda desconectado.")
            return

        print(
            f"\nReconectando en {decision['delay']} s "
            f"(intento {attempts})..."
        )
        time.sleep(decision["delay"])


def mostrar_menu():
    print("\n" + "=" * 48)
    print(f"       AgenteUTN - Versión {VERSION}")
    print("=" * 48)

    print("1. Ejecutar PING local")
    print("2. Mostrar información del equipo")
    print("3. Enviar HEARTBEAT local")
    print("4. Verificar servidor víctima")
    print("5. Conectar al servidor C2 (modo zombie)")
    print("6. Salir")

    print("=" * 48)


def main():
    agent_id = f"utn-{uuid.uuid4().hex[:12]}"

    print("\nAgenteUTN iniciado correctamente.")
    print(f"Identificador: {agent_id}")

    print("\nInformación del agente:")
    mostrar(build_hello(agent_id))

    while True:
        mostrar_menu()

        opcion = input(
            "\nSeleccioná una opción: "
        ).strip()

        if opcion == "1":
            print("\nPING local:")
            ejecutar_comando("ping")

        elif opcion == "2":
            print("\nInformación del equipo:")
            ejecutar_comando("info")

        elif opcion == "3":
            print("\nHEARTBEAT local:")
            mostrar(build_heartbeat())

        elif opcion == "4":
            verificar_victima()

        elif opcion == "5":
            conectar_vm(agent_id)

        elif opcion == "6":
            print("\nFinalizando AgenteUTN...")
            ejecutar_comando("stop")
            break

        else:
            print("\nOpción no válida.")


if __name__ == "__main__":
    main()
