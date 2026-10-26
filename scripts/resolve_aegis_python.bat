@echo off
rem Sets AEGIS_PYTHON for the calling batch file without changing machine PATH.
if defined AEGIS_PYTHON goto validate_python

if defined CONDA_PREFIX if exist "%CONDA_PREFIX%\python.exe" (
  set "AEGIS_PYTHON=%CONDA_PREFIX%\python.exe"
  goto validate_python
)

if exist "%USERPROFILE%\.conda\envs\aegis\python.exe" (
  set "AEGIS_PYTHON=%USERPROFILE%\.conda\envs\aegis\python.exe"
  goto validate_python
)

set "AEGIS_PYTHON=python"

:validate_python
"%AEGIS_PYTHON%" -c "import alembic, fastapi, serial, uvicorn" >nul 2>nul
if errorlevel 1 (
  echo ERROR: Aegis backend or migration dependencies are missing from "%AEGIS_PYTHON%".
  echo Activate the aegis Conda environment, or set AEGIS_PYTHON to its python.exe.
  echo Install dependencies with: "%AEGIS_PYTHON%" -m pip install -r backend\requirements.txt
  exit /b 1
)
exit /b 0
