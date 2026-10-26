# Aegis Local Demo Startup

## Start the local demo

From the repository root, double-click `start_aegis.bat` or run:

```powershell
.\start_aegis.bat
```

The launcher reuses services already listening on Aegis's local ports and
starts the blockchain, backend, frontend, and configured Arduino gateway in
separate terminals. Keep those terminals open while using the demo. The
blockchain launcher uses Anvil's persisted state when Anvil is installed;
without Anvil it uses Hardhat's in-memory chain, whose history is lost when
that node stops. Pending backend database migrations are applied before the
launcher starts a backend that is not already running. It checks for service
listeners after launch and prints a warning with the relevant window or
hardware checks if a listener does not appear; read that terminal's output
before relying on the service.

The launcher uses the active Conda environment, then the standard
`%USERPROFILE%\.conda\envs\aegis` interpreter, then `python` on `PATH`. To use
a different Python installation, set `AEGIS_PYTHON` to its full `python.exe`
path before running the batch file. Install the backend dependencies from the
repository root with:

```powershell
python -m pip install -r backend\requirements.txt
```

Install Node.js 18 or newer and install frontend/blockchain packages once if
they are not already present:

```powershell
cd frontend
npm install
cd ..\blockchain
npm install
cd ..
```

Open the frontend at `http://localhost:3000`; if Next.js reports another port,
use the URL printed in its terminal. The backend API is at
`http://127.0.0.1:8001/docs`.

## Arduino Mega onboard-LED pilot

This optional pilot uses one Mega over USB on COM9 by default. It is not a
general multi-device or remote-site gateway.

1. Upload the restricted pilot sketch and verify the LED commands using the
   safety steps in [the hardware handoff](HARDWARE_INTEGRATION_HANDOFF.md).
   Keep the 9 V battery disconnected for this USB-powered onboard-LED test.
2. Configure `AEGIS_ARDUINO_GATEWAY_TOKEN` in the repository-root `.env` with
   a private generated token. Do not commit or share it. The backend and
   gateway use the same token; restart both the backend and gateway after
   changing it.
3. Close Arduino IDE Serial Monitor so the gateway can claim COM9.
4. Run `start_aegis.bat`. If the token is absent, the launcher clearly skips
   the gateway; the blockchain, backend, and frontend can still run.
5. In the 3D Scene, register the physical actuator with ID
   `mega-onboard-led-01`, type `onboard_led`, and connection **Arduino Mega
   onboard LED (USB gateway)**. Send **off** before stopping the gateway.

For a different physical device, use a distinct physical identity and a
protocol/adapter that explicitly supports that device, then test it
independently before connecting it to Aegis. The current gateway only supports
this Mega's onboard LED and `LED_ON`/`LED_OFF`; do not reuse simulator IDs or
assume another USB device is supported. Devices at other locations need a
local gateway at each site and a securely designed network connection; the
loopback pilot must not be exposed to a LAN or WAN.

### Repeatable checklist for each additional device

1. Record its manufacturer/model, physical location, unique asset ID, power
   requirements, interface/protocol, supported readings and commands, and
   expected safe state. Do not wire it based only on another device's diagram.
2. Confirm the local gateway and an Aegis adapter support that exact hardware
   and protocol. The current Mega LED gateway is single-device and cannot
   register additional devices by changing an ID.
3. Test the hardware locally first: verify valid commands/readings, rejection
   of unsupported commands, acknowledgement or timeout behavior, and the
   defined safe state on disconnect. Keep mains and hazardous loads out of the
   prototype.
4. Register a new physical identity in Aegis and map it to its real location.
   Keep simulator assets separate; don't make a simulated reading or command
   look like a physical verification.
5. Record the test results and whether they were directly observed or
   owner-reported in the [hardware progress log](HARDWARE_INTEGRATION_HANDOFF.md).

## Individual service launchers

- `start_blockchain.bat` starts or reuses the blockchain and backend.
- `start_backend.bat` runs the backend in the current terminal.
- `start_frontend.bat` runs the frontend in the current terminal.
- `start_arduino_gateway.bat` runs the gateway in the current terminal; set
  `AEGIS_ARDUINO_SERIAL_PORT` first if the board is not on COM9.

Each service terminal displays its own errors and logs. Stop a service with
Ctrl+C in that service's terminal; send the LED **off** first.
