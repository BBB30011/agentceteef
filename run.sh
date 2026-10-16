#!/usr/bin/env bash
# ==============================================================================
#  CTF Agent Swarm — One-Click Interactive Launcher
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. Pastikan virtual environment siap
if [ ! -d ".venv" ]; then
    echo "[*] Menyiapkan environment pertama kali..."
    ./setup.sh
fi

# 2. Jalankan CTF Agent dengan interactive wizard jika tanpa argumen
if [ $# -eq 0 ]; then
    uv run --offline ctf-solve --interactive 2>/dev/null || uv run ctf-solve --interactive
else
    uv run --offline ctf-solve "$@" 2>/dev/null || uv run ctf-solve "$@"
fi
