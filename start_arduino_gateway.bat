@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not defined AEGIS_ARDUINO_SERIAL_PORT set "AEGIS_ARDUINO_SERIAL_PORT=COM9"
call "%~dp0scripts\resolve_aegis_python.bat"
if errorlevel 1 (
  pause
  exit /b 1
)
echo Starting the one-device Arduino gateway on %AEGIS_ARDUINO_SERIAL_PORT%.
"%AEGIS_PYTHON%" -m hardware.arduino_mega_led.gateway --port "%AEGIS_ARDUINO_SERIAL_PORT%"
if errorlevel 1 (
  echo Arduino gateway stopped with an error.
  pause
)
