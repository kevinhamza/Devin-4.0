@echo off
REM ========================================================
REM Devin Project - Windows Installation Script
REM This script sets up the Devin project on Windows systems.
REM Author: [Your Name or Team]
REM ========================================================

echo Welcome to the Devin Project Setup for Windows!
echo This script will install all necessary dependencies and configure the system.

REM Step 1: Check for Administrative Privileges
echo Checking for administrative privileges...
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Please run this script as an administrator.
    pause
    exit /b 1
)

REM Step 2: Update System and Install Required Software
echo Updating system packages and verifying required software...
REM Optionally include commands to verify Python, Git, etc.

REM Step 3: Set up a Virtual Environment
echo Setting up a Python virtual environment...
python -m venv env
if exist env (
    echo Virtual environment created successfully.
) else (
    echo Failed to create a virtual environment. Ensure Python is installed and added to PATH.
    pause
    exit /b 1
)

REM Step 4: Activate the Virtual Environment and Install Dependencies
echo Activating the virtual environment...
call env\Scripts\activate.bat

echo Installing required Python packages...
pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies. Check your network connection or requirements file.
    deactivate
    pause
    exit /b 1
)

REM Step 5: Set Environment Variables (Optional)
echo Configuring environment variables...
setx DEVIN_HOME "%~dp0"
setx PYTHONPATH "%~dp0"

REM Step 6: Finalize Installation
echo Installation completed successfully!
echo To start Devin, run "python main.py" from the project directory.

REM Cleanup
deactivate
echo Virtual environment deactivated. Installation complete.
pause
