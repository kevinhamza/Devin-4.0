@echo off
:: Devin AGI 4.0 — Windows Launcher
:: Routes all flags to main.py (Python) — no longer uses legacy TypeScript CLI.
setlocal EnableDelayedExpansion

cd /d "%~dp0"

:: Load .env into environment
if exist .env (
    for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
        set "line=%%A"
        if not "!line:~0,1!" == "#" (
            if not "%%A" == "" (
                set "%%A=%%B"
            )
        )
    )
)

:: Find Python
set PYTHON=
for %%P in (python3.12 python3.11 python3.10 python3 python) do (
    if "!PYTHON!" == "" (
        where %%P >nul 2>&1
        if !errorlevel! == 0 set PYTHON=%%P
    )
)
if "!PYTHON!" == "" (
    echo ERROR: Python 3 not found. Install Python 3.9+ and add it to PATH.
    exit /b 1
)

:: Activate venv if present
if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat 2>nul
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat 2>nul

:: Route flags
set ARG1=%~1

if /i "%ARG1%" == "--help"    goto :show_help
if /i "%ARG1%" == "-h"        goto :show_help
if /i "%ARG1%" == "--version" ( echo Devin AGI v4.0.0 & exit /b 0 )
if /i "%ARG1%" == "-V"        ( echo Devin AGI v4.0.0 & exit /b 0 )

if /i "%ARG1%" == "--setup" goto :setup
if /i "%ARG1%" == "--install-deps" goto :setup

if /i "%ARG1%" == "--test" (
    !PYTHON! agent.py --test
    exit /b !errorlevel!
)

if /i "%ARG1%" == "--status" (
    !PYTHON! main.py --status
    exit /b !errorlevel!
)

if /i "%ARG1%" == "--caps" (
    !PYTHON! main.py --caps
    exit /b !errorlevel!
)

if /i "%ARG1%" == "--no-agent" (
    !PYTHON! main.py --no-agent
    exit /b !errorlevel!
)

if /i "%ARG1%" == "--voice" (
    set DEVIN_VOICE_MODE=1
    !PYTHON! main.py --voice
    exit /b !errorlevel!
)

if /i "%ARG1%" == "--provider" (
    if "%~2" == "" (
        echo ERROR: --provider requires an argument
        exit /b 1
    )
    set DEVIN_PROVIDER=%~2
    !PYTHON! main.py --provider %~2
    exit /b !errorlevel!
)

:: Default: full module load via main.py then REPL
!PYTHON! main.py %*
exit /b !errorlevel!

:show_help
echo Devin AGI v4.0.0
echo.
echo Usage:
echo   devin                        Interactive REPL (full module load)
echo   devin "do something"         One-shot prompt
echo   devin --voice                Voice command mode
echo   devin --provider hf          Force HuggingFace provider
echo   devin --provider claude       Force Claude provider
echo   devin --test                 Run core test suite
echo   devin --status               Module load status
echo   devin --caps                 Capability summary
echo   devin --no-agent             Load modules only
echo   devin --setup                Install dependencies
echo   devin --version              Show version
echo.
echo Set API keys in .env (never in code):
echo   HF_TOKEN, ANTHROPIC_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY
exit /b 0

:setup
echo Installing dependencies...
!PYTHON! -m pip install --upgrade pip
if exist requirements.txt !PYTHON! -m pip install -r requirements.txt
echo Done.
exit /b 0
