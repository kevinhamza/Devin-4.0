#!/bin/sh
# Devin 4.0 — One-line installer
# Usage:
#   curl -fsSL https://github.com/kevinhamza/Devin-4.0/raw/main/scripts/install.sh | sh
#
# After install, run:  devin
set -e

REPO_URL="https://github.com/kevinhamza/Devin-4.0"
ENV_URL="https://raw.githubusercontent.com/kevinhamza/Devin-4.0/main/.env.example"
ENV_DEST="$HOME/.devin.env"

echo ""
echo "┌────────────────────────────────────┐"
echo "│        Devin 4.0 Installer         │"
echo "└────────────────────────────────────┘"
echo ""

# ── 1. Python check ───────────────────────────────────────────────────────────
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 not found. Install Python 3.9+ and retry."
    exit 1
fi
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)' || {
    echo "ERROR: Python 3.9+ required."
    exit 1
}
echo "[1/3] Python OK ($(python3 --version))"

# ── 2. pip install from GitHub ────────────────────────────────────────────────
echo "[2/3] Installing devin via pip..."
pip3 install --quiet --upgrade "git+$REPO_URL"
echo "      Done — 'devin' command is now available."

# ── 3. .env setup (optional) ─────────────────────────────────────────────────
echo "[3/3] Setting up optional config..."
if [ -f "$ENV_DEST" ]; then
    echo "      $ENV_DEST already exists — skipping."
else
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "$ENV_URL" -o "$ENV_DEST" 2>/dev/null && \
            echo "      Created $ENV_DEST — edit it to add API keys (optional)." || \
            echo "      (Could not download .env.example — skipping)"
    fi
fi

echo ""
echo "✅  Devin 4.0 installed!"
echo ""
echo "    Run:   devin"
echo "    Help:  devin --help"
echo ""
echo "    API keys are optional. To add one:"
echo "    Edit $ENV_DEST (or export ANTHROPIC_API_KEY=... etc.)"
echo ""
