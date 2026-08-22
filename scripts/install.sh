#!/bin/bash

# Devin AGI Installation Script for Linux/macOS
set -e

echo "--- Starting Devin AGI Setup ---"

# 1. Check for Python 3.9+
echo "[1/5] Checking for Python 3.9+..."
if ! command -v python3 &> /dev/null || ! python3 -c 'import sys; assert sys.version_info >= (3, 9)' &> /dev/null; then
    echo "ERROR: Python 3.9 or higher is required. Please install it and try again."
    exit 1
fi
echo "Python check passed."

# 2. Create Python Virtual Environment
echo "[2/5] Creating Python virtual environment in './venv'..."
python3 -m venv venv
source venv/bin/activate
echo "Virtual environment created and activated."

# 3. Install Dependencies
echo "[3/5] Installing dependencies from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt
echo "Dependencies installed successfully."

# 4. Check for External Tools
echo "[4/5] Checking for external tools..."
if ! command -v adb &> /dev/null; then
    echo "WARNING: 'adb' (Android Debug Bridge) not found. The mobile integration module will not function."
fi
if ! command -v ros2 &> /dev/null; then
    echo "WARNING: 'ros2' not found. The robotics modules will have limited functionality."
fi

# 5. Setup Environment File
echo "[5/5] Setting up environment file..."
if [ -f ".env" ]; then
    echo ".env file already exists. Skipping creation."
else
    cp .env.template .env
    echo "Created .env file from template. Please edit this file to add your API keys."
fi

echo ""
echo "--- ✅ Devin AGI Setup Complete ---"
echo "To activate the environment, run: source venv/bin/activate"
echo "To start the application, run: python main.py"
