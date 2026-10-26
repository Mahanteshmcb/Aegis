"""Loopback HTTP gateway between Aegis and the Mega onboard-LED sketch."""
from __future__ import annotations

import argparse
import hmac
import logging
import os
import time
from collections.abc import Iterable
from contextlib import asynccontextmanager
from threading import Lock
from typing import Any, Callable, Literal

import uvicorn
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

DEVICE_ID = "mega-onboard-led-01"
BAUD_RATE = 115200
logger = logging.getLogger("aegis.arduino_gateway")


class GatewayCommand(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    schema_name: Literal["aegis.device-command.v1"] = Field(alias="schema")
    command_id: str = Field(min_length=1, max_length=40, pattern=r"^[A-Za-z0-9-]+$")
    device_id: str
    tenant_id: int
    zone_id: int | None
    command: str
    parameters: dict[str, Any]
    issued_at: str


class ArduinoSerialGateway:
    def __init__(
        self,
        serial_port: Any | None,
        device_id: str = DEVICE_ID,
        serial_port_factory: Callable[[], Any] | None = None,
    ) -> None:
        self._serial_port = serial_port
        self._device_id = device_id
        self._serial_port_factory = serial_port_factory
        self._lock = Lock()

    @property
    def serial_open(self) -> bool:
        return self._serial_port is not None and getattr(self._serial_port, "is_open", True)

    def close(self) -> None:
        with self._lock:
            self._close_serial_port()

    def _close_serial_port(self) -> None:
        serial_port = self._serial_port
        self._serial_port = None
        close = getattr(serial_port, "close", None)
        if callable(close):
            try:
                close()
            except OSError:
                logger.warning("Could not close the stale Arduino serial connection", exc_info=True)

    def _connect(self) -> None:
        if self._serial_port_factory is None:
            raise OSError("Arduino serial connection is unavailable")
        self._serial_port = self._serial_port_factory()

    def execute(self, command: GatewayCommand) -> dict[str, Any]:
        if command.device_id != self._device_id:
            raise HTTPException(status_code=404, detail="Device is not registered on this gateway")
        if command.command.lower() not in {"on", "off"}:
            raise HTTPException(status_code=422, detail="This pilot gateway accepts only on and off")
        if command.parameters:
            raise HTTPException(status_code=422, detail="This pilot gateway does not accept parameters")

        target_state = "ON" if command.command.lower() == "on" else "OFF"
        frame = (
            f"AEGIS/1,{command.command_id},{self._device_id},LED_{target_state}\n"
        ).encode("ascii")
        with self._lock:
            for attempt in range(2):
                try:
                    if not self.serial_open:
                        self._close_serial_port()
                        self._connect()
                    written = self._serial_port.write(frame)
                    if written is not None and written != len(frame):
                        raise OSError("Incomplete serial command write")
                    self._serial_port.flush()
                    response = self._serial_port.readline()
                    if response:
                        break
                    if attempt == 0 and self._serial_port_factory is not None:
                        logger.warning("Arduino did not acknowledge; reconnecting and retrying once")
                        self._close_serial_port()
                        self._connect()
                        continue
                    raise HTTPException(status_code=504, detail="Arduino did not acknowledge the command")
                except HTTPException:
                    raise
                except (OSError, TimeoutError, RuntimeError) as exc:
                    logger.warning("Arduino serial transport failed; reconnecting", exc_info=True)
                    self._close_serial_port()
                    if attempt == 1:
                        raise HTTPException(
                            status_code=503,
                            detail="Arduino serial transport is unavailable; check the USB connection",
                        ) from exc
                    try:
                        self._connect()
                    except (OSError, TimeoutError, RuntimeError) as reconnect_exc:
                        raise HTTPException(
                            status_code=503,
                            detail="Arduino serial transport is unavailable; check the USB connection",
                        ) from reconnect_exc

        try:
            fields = response.decode("ascii").strip().split(",")
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=502, detail="Arduino returned a non-ASCII response") from exc
        expected = ["AEGIS/1", command.command_id, "OK", target_state]
        if fields != expected:
            logger.warning("Arduino rejected or mismatched command response: %s", fields[:4])
            raise HTTPException(status_code=502, detail="Arduino response did not confirm the requested state")

        return {
            "accepted": True,
            "confirmed": True,
            "command_id": command.command_id,
            "device_id": self._device_id,
            "state": target_state,
        }


def create_gateway_app(
    serial_port: Any | None,
    token: str,
    serial_port_factory: Callable[[], Any] | None = None,
) -> FastAPI:
    if len(token) < 32:
        raise ValueError("Arduino gateway token must contain at least 32 characters")
    gateway = ArduinoSerialGateway(serial_port, serial_port_factory=serial_port_factory)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        gateway.close()

    app = FastAPI(
        title="Aegis Arduino LED Gateway",
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.serial_port = serial_port

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {
            "status": "running",
            "device_id": DEVICE_ID,
            "serial_open": gateway.serial_open,
        }

    @app.post("/commands")
    def execute_command(
        command: GatewayCommand,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        expected = f"Bearer {token}"
        if authorization is None or not hmac.compare_digest(authorization, expected):
            raise HTTPException(status_code=401, detail="Invalid gateway credentials")
        return gateway.execute(command)

    return app


def open_serial_port(port: str) -> Any:
    try:
        import serial
        import serial.tools.list_ports
    except ImportError as exc:
        raise RuntimeError("Install backend requirements to use the Arduino gateway (pyserial)") from exc

    try:
        resolved_port = resolve_serial_port(port, serial.tools.list_ports.comports())
    except (AttributeError, OSError) as exc:
        raise RuntimeError(f"Could not find Arduino Mega serial port {port}: {exc}") from exc
    logger.info("Opening Arduino Mega serial port %s at %s baud", resolved_port, BAUD_RATE)
    connection = serial.Serial(port=resolved_port, baudrate=BAUD_RATE, timeout=2, write_timeout=2)
    time.sleep(2)
    connection.reset_input_buffer()
    return connection


def resolve_serial_port(port: str, available_ports: Iterable[Any]) -> str:
    if port.lower() == "auto":
        preferred_port = None
    else:
        preferred_port = next(
            (candidate.device for candidate in available_ports if candidate.device.lower() == port.lower()),
            None,
        )
        if preferred_port is not None:
            return preferred_port

    mega_usb_ids = {(0x2341, 0x0042), (0x2A03, 0x0042), (0x2341, 0x0010)}
    candidates = [
        candidate
        for candidate in available_ports
        if (candidate.vid, candidate.pid) in mega_usb_ids
        or "arduino mega" in (candidate.description or "").lower()
        or "mega 2560" in (candidate.description or "").lower()
        or "ch340" in (candidate.description or "").lower()
    ]
    if len(candidates) == 1:
        return candidates[0].device
    if len(candidates) > 1:
        raise RuntimeError("Multiple Arduino Mega boards found; set AEGIS_ARDUINO_SERIAL_PORT to the correct COM port")
    if preferred_port is None:
        raise RuntimeError("No Arduino Mega serial port found; connect the board or set AEGIS_ARDUINO_SERIAL_PORT")
    raise RuntimeError(f"Arduino Mega serial port {port} is not available")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local Aegis Arduino Mega LED gateway")
    parser.add_argument("--port", default=os.getenv("AEGIS_ARDUINO_SERIAL_PORT", "COM9"))
    parser.add_argument("--http-port", type=int, default=8765)
    args = parser.parse_args()

    from backend.config import settings

    token = settings.arduino_gateway_token
    if token is None or len(token.get_secret_value()) < 32:
        parser.error("Set AEGIS_ARDUINO_GATEWAY_TOKEN to a random secret of at least 32 characters in .env")
    try:
        serial_port = open_serial_port(args.port)
    except (OSError, RuntimeError) as exc:
        logger.warning("Arduino is not currently available (%s); gateway will retry on the next command", exc)
        serial_port = None

    logger.info("Starting Arduino Mega gateway for %s at %s baud", args.port, BAUD_RATE)
    uvicorn.run(
        create_gateway_app(
            serial_port,
            token.get_secret_value(),
            serial_port_factory=lambda: open_serial_port(args.port),
        ),
        host="127.0.0.1",
        port=args.http_port,
    )


if __name__ == "__main__":
    main()
