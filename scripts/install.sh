#!/bin/bash

# Devin 4.0 — One-line install script
# Usage: curl -fsSL https://github.com/kevinhamza/Devin-4.0/raw/main/scripts/install.sh | sh
set -e

REPO="https://github.com/kevinhamza/Devin-4.0"
DEST="${DEVIN_INSTALL_DIR:-$HOME/Devin-4.0}"

echo "--- Devin 4.0 Installer ---"

# 1. Check for Python 3.9+
echo "[1/5] Checking for Python 3.9+..."
if ! command -v python3 &>/dev/null || ! python3 -c 'import sys; assert sys.version_info >= (3, 9)' &>/dev/null; then
    echo "ERROR: Python 3.9 or higher is required. Please install it and try again."
    exit 1
fi
echo "Python check passed."

# 2. Clone or update the repo
echo "[2/5] Installing Devin 4.0 to $DEST..."
if [ -d "$DEST/.git" ]; then
    echo "Existing install found — pulling latest changes..."
    git -C "$DEST" pull --ff-only
else
    git clone --depth=1 "$REPO" "$DEST"
fi
cd "$DEST"

# 3. Install Python dependencies
echo "[3/5] Installing Python dependencies..."
pip3 install --quiet --upgrade pip
pip3 install --quiet -r requirements.txt
echo "Dependencies installed."

# 4. Check optional external tools (warnings only)
echo "[4/5] Checking optional external tools..."
for tool in adb ros2; do
    if ! command -v "$tool" &>/dev/null; then
        echo "  WARNING: '$tool' not found. Related modules will be limited."
    fi
done

# 5. Set up .env
echo "[5/5] Setting up environment file..."
if [ -f ".env" ]; then
    echo ".env already exists — skipping."
else
    cp .env.example .env
    echo "Created .env from .env.example. Edit it to add your API keys (optional)."
fi

echo ""
echo "✅ Devin 4.0 installed at: $DEST"
echo ""
echo "To start:"
echo "  cd $DEST"
echo "  python3 agent.py"
echo ""
echo "Or use the shell launcher:"
echo "  chmod +x $DEST/devin && $DEST/devin"
