# AgenteUTN

Agente zombie del laboratorio de **Seguridad de TI II (UTN)**. Compatible con el
servidor C2 del equipo (protocolo JSON por línea sobre TCP, ver
`Botnet_Cibersecurity` → `docs/protocolo.md`).

> **Ámbito autorizado del curso.** Se ejecuta únicamente contra las instancias
> propias del laboratorio (C2 y servidor víctima en AWS) con autorización del
> docente. La inundación `load` es acotada (≤ 120 s, ≤ 200 conexiones) y no debe
> usarse fuera del alcance autorizado.

## Comandos que implementa

| Comando | Args | Respuesta |
|---|---|---|
| `ping` | - | `{"pong": true}` |
| `info` | - | `{"hostname": ..., "os": ..., "python": ...}` |
| `echo` | `text` | `{"text": "<mismo texto>"}` |
| `stop` | - | `{"stopping": true}` y cierra **sin reconectar** |
| `load` | `target`, `duration`, `concurrency` | `{"sent": n, "errors": m, "rps": r, "duration_s": d}` |

- `load` corre en segundo plano: `ping` y `stop` siguen respondiendo durante la
  inundación, y `stop`/`bye`/caída del C2 cancelan los workers de inmediato.
- Conexión automática al C2 (`54.88.121.40:8443`), `heartbeat` cada 10 s y
  **reconexión automática** con espera de 5 s (máximo 3 intentos) cuando se
  pierde la conexión o el servidor responde `busy`. No reconecta tras `stop`,
  `bye` o `error auth`.

## Estructura

```text
src/
├── main.py               # Menú de la aplicación (punto de entrada del .exe)
├── aws_client.py         # Sesión TCP con el C2 (hello, comandos, load, reconexión)
├── load_command.py       # Inundación HTTP controlada (solo stdlib)
├── commands.py           # ping / info / stop / echo
├── command_dispatcher.py # Whitelist de comandos permitidos
├── protocol.py           # Codificación/decodificación JSON por línea (64 KB)
├── identity.py           # hello y heartbeat
├── response.py           # Construcción de frames result
├── server_events.py      # Interpretación de bye/error del servidor
├── reconnect_policy.py   # Política de reconexión (máx. 3 intentos, 5 s)
├── ping_client.py        # Cliente de prueba (solo ping, legado)
├── aws_diagnostic.py     # Cliente de diagnóstico local (legado)
└── local_client.py       # Cliente de prueba local (legado)
tests/                    # Suite de pruebas (40 pruebas)
carga_controlada/         # Locustfile alternativo (requiere locust, no se usa en el .exe)
installer/                # Instalador Inno Setup + 7-Zip redistribuible
```

## Ejecutar desde el código

```powershell
cd AgenteUtn
python src/main.py
```

Opción **5** del menú: conecta al C2 en modo zombie (se queda escuchando
comandos hasta `stop`/`bye`/Ctrl+C, con reconexión automática).

## Pruebas

```powershell
python -m unittest discover -s tests
```

Debe finalizar con `OK` (40 pruebas).

## Compilar el .exe

```powershell
pip install pyinstaller
python -m PyInstaller AgenteUTN.spec --noconfirm
```

Genera `dist/AgenteUTN.exe` (consola, sin dependencias externas).

## Generar el instalador

Con Inno Setup 6 instalado:

```powershell
cd installer
ISCC.exe AgenteUTN.iss
```

Genera `installer/output/AgenteUTN_Setup.exe` (instala AgenteUTN y 7-Zip).
