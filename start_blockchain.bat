@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ROOT=%~dp0"
set "BLOCKCHAIN_DIR=%ROOT%blockchain"
set "STATE_DIR=%BLOCKCHAIN_DIR%\.local-state"
set "RPC_URL=http://127.0.0.1:8545"

echo.
echo ==========================================
echo AEGIS LOCAL BLOCKCHAIN STARTUP
echo ==========================================

if not exist "%BLOCKCHAIN_DIR%\package.json" (
    echo ERROR: Blockchain project not found at "%BLOCKCHAIN_DIR%".
    exit /b 1
)

if not exist "%BLOCKCHAIN_DIR%\node_modules\.bin\hardhat.cmd" (
    echo ERROR: Blockchain dependencies are missing.
    echo Run: cd /d "%BLOCKCHAIN_DIR%" ^&^& npm install
    exit /b 1
)

call "%ROOT%scripts\resolve_aegis_python.bat"
if errorlevel 1 exit /b 1

if not exist "%STATE_DIR%" mkdir "%STATE_DIR%"

echo Checking for an existing local RPC on port 8545...
call :check_rpc
set "RPC_CHECK=%ERRORLEVEL%"

if "%RPC_CHECK%"=="2" (
    echo ERROR: A service is already using port 8545, but it is not chain ID 31337.
    echo Stop that service or update the Aegis blockchain configuration.
    exit /b 1
)

if "%RPC_CHECK%"=="0" (
    echo Local chain is already running. Reusing it.
) else (
    where anvil >nul 2>nul
    if not errorlevel 1 (
        echo Starting Anvil with persistent local state.
        start "Aegis Persistent Blockchain" cmd /k "anvil --host 127.0.0.1 --port 8545 --chain-id 31337 --state ""%STATE_DIR%\aegis-chain-state.json"" --state-interval 5"
    ) else (
        echo WARNING: Anvil was not found. Starting Hardhat's temporary in-memory chain.
        echo Hardhat fallback loses chain history when its node exits.
        start "Aegis Hardhat Blockchain" cmd /k "cd /d ""%BLOCKCHAIN_DIR%"" && npm run node"
    )
)

echo Waiting for the local blockchain RPC...
set "RPC_READY=0"
for /l %%N in (1,1,90) do (
    call :check_rpc
    if not errorlevel 1 (
        set "RPC_READY=1"
        goto :rpc_ready
    )
    timeout /t 1 /nobreak >nul
)
:rpc_ready
if not "!RPC_READY!"=="1" (
    echo ERROR: Blockchain RPC did not become ready within 90 seconds.
    echo Check the node window for startup errors.
    exit /b 1
)

pushd "%BLOCKCHAIN_DIR%"
if errorlevel 1 (
    echo ERROR: Could not enter the blockchain project folder.
    exit /b 1
)

echo Checking whether the configured contract is deployed...
node -e "const d=require('./deployments/localhost-deployment.json');const {ethers}=require('ethers');(async()=>{const p=new ethers.providers.JsonRpcProvider('%RPC_URL%');const c=await p.getCode(d.AegisAudit);process.exit(c==='0x'?1:0)})().catch(()=>process.exit(1))"
if errorlevel 1 (
    echo Contract is not present on this chain. Deploying AegisAudit...
    call npm run deploy
    if errorlevel 1 (
        echo ERROR: Contract deployment failed.
        popd
        exit /b 1
    )
) else (
    echo Existing AegisAudit contract found. Keeping its address and chain history.
)

echo Configuring the AegisAudit contract...
call npx hardhat run scripts/setup.js --network localhost
if errorlevel 1 (
    echo ERROR: Contract setup failed.
    popd
    exit /b 1
)
popd

echo.
echo Checking Aegis backend on port 8001...
powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if errorlevel 1 (
    echo Applying pending backend database migrations...
    "%AEGIS_PYTHON%" -m alembic -c "%ROOT%backend\alembic.ini" upgrade head
    if errorlevel 1 (
        echo ERROR: Database migrations failed. Backend was not started.
        exit /b 1
    )
    echo Starting Aegis backend in a new window...
    start "Aegis Backend" cmd /k "cd /d ""%ROOT%"" && ""%AEGIS_PYTHON%"" -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8001"
) else (
    echo Aegis backend is already running.
)

echo.
echo Blockchain startup complete.
echo RPC:      %RPC_URL%
echo Backend:  http://127.0.0.1:8001
where anvil >nul 2>nul
if errorlevel 1 (
    echo NOTE: This session is using Hardhat's in-memory chain. Install Anvil and rerun
    echo       this file to preserve blockchain state across normal restarts.
) else (
    echo State:    %STATE_DIR%\aegis-chain-state.json
)
echo Keep the blockchain node window open while using Aegis.
echo.
if /i not "%AEGIS_NO_PAUSE%"=="1" pause
exit /b 0

:check_rpc
node -e "fetch('%RPC_URL%',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',method:'eth_chainId',params:[],id:1}),signal:AbortSignal.timeout(2000)}).then(r=>r.json()).then(r=>process.exit(r.result==='0x7a69'?0:2)).catch(()=>process.exit(1))" >nul 2>nul
exit /b %ERRORLEVEL%
