#!/bin/sh
# Devin 4.0 — One-line installer
# Usage:
#   curl -fsSL https://github.com/kevinhamza/Devin-4.0/raw/main/scripts/install.sh | sh
#
# After install, run:  devin
set -e

REPO_URL="https://github.com/kevinhamza/Devin-4.0"
ENV_URL="https://raw.githubusercontent.com/kevinhamza/Devin-4.0/main/.env.example"
CONFIG_DIR="$HOME/.devin"
ENV_FILE="$CONFIG_DIR/.env"

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
    echo "ERROR: Python 3.9+ required. Current: $(python3 --version)"
    exit 1
}
echo "[1/3] Python OK ($(python3 --version))"

# ── 2. pip install ────────────────────────────────────────────────────────────
echo "[2/3] Installing devin-agi via pip..."
pip3 install --quiet --upgrade "git+$REPO_URL"
echo "      Done — 'devin' command is now available."

# ── 3. Create ~/.devin/.env config ───────────────────────────────────────────
echo "[3/3] Setting up config at $ENV_FILE ..."
mkdir -p "$CONFIG_DIR"
if [ -f "$ENV_FILE" ]; then
    echo "      $ENV_FILE already exists — skipping."
else
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "$ENV_URL" -o "$ENV_FILE" 2>/dev/null && \
            echo "      Created $ENV_FILE" || \
            touch "$ENV_FILE"
    else
        touch "$ENV_FILE"
    fi
fi

echo ""
echo "✅  Devin 4.0 installed!"
echo ""
echo "    Run:  devin"
echo ""
echo "    To add API keys (all optional):"
echo "    Edit $ENV_FILE"
echo ""
echo "    Examples:"
echo "      HF_TOKEN=hf_...           ← free at huggingface.co/settings/tokens"
echo "      GEMINI_API_KEY=AIza...    ← free tier at aistudio.google.com"
echo "      ANTHROPIC_API_KEY=sk-...  ← paid, best quality"
echo "      CLAUDE_SESSION_KEY=...    ← free via fcc-server proxy"
echo ""
echo "    No key needed — runs free on HuggingFace by default."
echo ""
