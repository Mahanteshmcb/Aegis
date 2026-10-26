@echo off
setlocal
cd /d "%~dp0"

where node >nul 2>nul
if errorlevel 1 (
  echo ERROR: Node.js 18 or newer is required. Install Node.js and try again.
  exit /b 1
)
node -e "process.exit(Number(process.versions.node.split('.')[0]) >= 18 ? 0 : 1)"
if errorlevel 1 (
  echo ERROR: Node.js 18 or newer is required. Update Node.js and try again.
  exit /b 1
)

if not exist "%~dp0frontend\node_modules\next\dist\bin\next" (
  echo ERROR: Frontend dependencies are missing.
  echo Run: cd /d "%~dp0frontend" ^&^& npm install
  exit /b 1
)

cd /d "%~dp0frontend"
echo Starting Aegis frontend. Next.js will print the actual local URL.
npm run dev
