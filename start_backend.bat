@echo off
setlocal
cd /d "%~dp0"

call "%~dp0scripts\resolve_aegis_python.bat"
if errorlevel 1 exit /b 1

echo Applying pending backend database migrations...
"%AEGIS_PYTHON%" -m alembic -c "%~dp0backend\alembic.ini" upgrade head
if errorlevel 1 (
  echo ERROR: Database migrations failed. Backend was not started.
  exit /b 1
)

echo Starting Aegis backend at http://127.0.0.1:8001
"%AEGIS_PYTHON%" -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8001
