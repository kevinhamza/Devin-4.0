@echo off
:: Devin AGI launcher for Windows
setlocal EnableDelayedExpansion

cd /d "%~dp0"

:: Load .env into environment
if exist .env (
    for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
        set "%%A=%%B"
    )
)

:: Run compiled JS if available
if exist dist\cli.js (
    node dist\cli.js %*
    goto :eof
)

:: Try ts-node (dev mode)
where ts-node >nul 2>&1
if %errorlevel% == 0 (
    ts-node src\cli.ts %*
    goto :eof
)

:: Try tsx
where tsx >nul 2>&1
if %errorlevel% == 0 (
    tsx src\cli.ts %*
    goto :eof
)

echo [ERROR] No runtime found. Run: npm install and npm run build
exit /b 1
