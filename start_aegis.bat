@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "AEGIS_ROOT=%~dp0"

echo.
echo ==========================================
echo AEGIS LOCAL DEMO - START ALL
echo ==========================================

call "%AEGIS_ROOT%scripts\resolve_aegis_python.bat"
if errorlevel 1 goto startup_failed

where node >nul 2>nul
if errorlevel 1 (
  echo ERROR: Node.js 18 or newer is required for the blockchain and frontend.
  goto startup_failed
)
node -e "process.exit(Number(process.versions.node.split('.')[0]) >= 18 ? 0 : 1)"
if errorlevel 1 (
  echo ERROR: Node.js 18 or newer is required. Update Node.js and try again.
  goto startup_failed
)
if not exist "%AEGIS_ROOT%frontend\node_modules\next\dist\bin\next" (
  echo ERROR: Frontend dependencies are missing.
  echo Run: cd /d "%AEGIS_ROOT%frontend" ^&^& npm install
  goto startup_failed
)

echo.
echo [1/4] Starting blockchain and backend...
set "AEGIS_NO_PAUSE=1"
call "%AEGIS_ROOT%start_blockchain.bat"
if errorlevel 1 (
  set "AEGIS_NO_PAUSE="
  goto startup_failed
)
set "AEGIS_NO_PAUSE="

echo Checking backend listener...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$limit=(Get-Date).AddSeconds(45); do { if (Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue) { exit 0 }; Start-Sleep -Seconds 2 } while ((Get-Date) -lt $limit); exit 1" >nul 2>nul
if errorlevel 1 (
  echo WARNING: Backend did not listen on port 8001. Check the backend window.
) else (
  echo Backend is listening on port 8001.
)

echo.
echo [2/4] Starting frontend...
powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }" >nul 2>nul
if errorlevel 1 (
  start "Aegis Frontend" cmd /k "cd /d ""%AEGIS_ROOT%frontend"" && npm run dev"
) else (
  echo Port 3000 is already in use; not starting a duplicate frontend.
)
powershell -NoProfile -ExecutionPolicy Bypass -Command "$limit=(Get-Date).AddSeconds(60); do { if (Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue) { exit 0 }; Start-Sleep -Seconds 2 } while ((Get-Date) -lt $limit); exit 1" >nul 2>nul
if errorlevel 1 (
  echo WARNING: No listener appeared on port 3000. Check the frontend window and its printed URL.
) else (
  echo A listener is available on port 3000.
)

echo.
echo [3/4] Starting the Arduino gateway when configured...
if not exist "%AEGIS_ROOT%.env" (
  echo Root .env is missing. Gateway skipped; create it from .env.example and set the gateway token.
  goto gateway_done
)
findstr /r /c:"^AEGIS_ARDUINO_GATEWAY_TOKEN=." "%AEGIS_ROOT%.env" >nul 2>nul
if errorlevel 1 (
  echo Gateway token is not configured. Gateway skipped.
  echo Configure AEGIS_ARDUINO_GATEWAY_TOKEN in the root .env, then restart this launcher.
  goto gateway_done
)
powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }" >nul 2>nul
if errorlevel 1 (
  start "Aegis Arduino Gateway" cmd /k "cd /d ""%AEGIS_ROOT%"" && call start_arduino_gateway.bat"
) else (
  echo Port 8765 is already in use; not starting a duplicate gateway.
)
powershell -NoProfile -ExecutionPolicy Bypass -Command "$limit=(Get-Date).AddSeconds(20); do { if (Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue) { exit 0 }; Start-Sleep -Seconds 2 } while ((Get-Date) -lt $limit); exit 1" >nul 2>nul
if errorlevel 1 (
  echo WARNING: Gateway did not listen on port 8765. Check its window, COM port, and Serial Monitor.
) else (
  echo A gateway listener is available on port 8765.
)
:gateway_done

echo.
echo [4/4] Startup commands issued.
echo Blockchain RPC: http://127.0.0.1:8545
echo Backend API:    http://127.0.0.1:8001/docs
echo Frontend:       http://localhost:3000 (use the URL printed by Next.js if it selected another port)
echo Gateway health: http://127.0.0.1:8765/health (when configured and the Arduino is connected)
echo.
echo Keep every service window opened by this launcher open while using Aegis.
echo For the Arduino pilot, close Serial Monitor before starting the gateway.
powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }" >nul 2>nul
if not errorlevel 1 start "" http://localhost:3000
exit /b 0

:startup_failed
echo.
echo Aegis startup stopped because a prerequisite or service failed.
echo Read the messages above, correct the issue, then run start_aegis.bat again.
pause
exit /b 1
