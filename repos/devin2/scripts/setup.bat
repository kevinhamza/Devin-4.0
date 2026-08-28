@echo off
rem Devin AGI Installation Script for Windows
echo --- Starting Devin AGI Setup ---

rem 1. Check for Python 3.9+
echo [1/5] Checking for Python 3.9+...
py -3 -c "import sys; assert sys.version_info >= (3, 9)"
if %errorlevel% neq 0 (
    echo ERROR: Python 3.9 or higher is required. Please install it and add it to your PATH.
    exit /b 1
)
echo Python check passed.

rem 2. Create Python Virtual Environment
echo [2/5] Creating Python virtual environment in '.\venv'...
py -3 -m venv venv
call .\venv\Scripts\activate.bat
echo Virtual environment created and activated.

rem 3. Install Dependencies
echo [3/5] Installing dependencies from requirements.txt...
pip install --upgrade pip
pip install -r requirements.txt
echo Dependencies installed successfully.

rem 4. Check for External Tools
echo [4/5] Checking for external tools...
where adb >nul 2>nul
if %errorlevel% neq 0 (
    echo WARNING: 'adb' (Android Debug Bridge) not found in PATH. The mobile integration module will not function.
)

rem 5. Setup Environment File
echo [5/5] Setting up environment file...
if exist .env (
    echo .env file already exists. Skipping creation.
) else (
    copy .env.template .env
    echo Created .env file from template. Please edit this file to add your API keys.
)

echo.
echo --- [SUCCESS] Devin AGI Setup Complete ---
echo To activate the environment, run: .\venv\Scripts\activate.bat
echo To start the application, run: py main.py
