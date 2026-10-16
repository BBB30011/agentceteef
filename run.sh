#!/usr/bin/env bash
# ==============================================================================
#  ⚡ Agent CeTeEf (agentceteef) — Universal CLI Launcher
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. Pastikan virtual environment siap
if [ ! -d ".venv" ]; then
    echo "[*] Menyiapkan environment pertama kali..."
    ./setup.sh
fi

# 2. Tangani shortcut perintah ramah pengguna
cmd="$1"
case "$cmd" in
    ""|"interactive"|"-i")
        echo "[*] Membuka Interactive Launcher Wizard..."
        uv run --offline ctf-solve --interactive 2>/dev/null || uv run ctf-solve --interactive
        ;;
    "demo")
        echo "[*] Menjalankan pemecahan tantangan demo..."
        uv run --offline ctf-solve --challenge ./challenges/demo_sanity --no-submit 2>/dev/null || uv run ctf-solve --challenge ./challenges/demo_sanity --no-submit
        ;;
    "tokenless")
        echo "[*] Menjalankan profil Tokenless (Antigravity CLI / Host Sandbox)..."
        uv run --offline ctf-solve --profile tokenless 2>/dev/null || uv run ctf-solve --profile tokenless
        ;;
    "fast")
        echo "[*] Menjalankan profil Fast Swarm..."
        uv run --offline ctf-solve --profile fast 2>/dev/null || uv run ctf-solve --profile fast
        ;;
    "smart")
        echo "[*] Menjalankan profil Smart / Deep Swarm..."
        uv run --offline ctf-solve --profile smart 2>/dev/null || uv run ctf-solve --profile smart
        ;;
    "scan")
        shift
        target="${1:-./challenges/demo_sanity}"
        echo "[*] Menjalankan Automated Security Recon pada '$target'..."
        uv run --offline ctf-solve --scan "$target" 2>/dev/null || uv run ctf-solve --scan "$target"
        ;;
    "decode")
        shift
        uv run --offline ctf-solve --quick-decode "$*" 2>/dev/null || uv run ctf-solve --quick-decode "$*"
        ;;
    "hash")
        shift
        uv run --offline ctf-solve --quick-hash "$*" 2>/dev/null || uv run ctf-solve --quick-hash "$*"
        ;;
    "report")
        uv run --offline ctf-solve --report 2>/dev/null || uv run ctf-solve --report
        ;;
    "report-html")
        echo "[*] Mengekspor laporan kompetisi ke ctf_report.html..."
        uv run --offline ctf-solve --export-html ctf_report.html 2>/dev/null || uv run ctf-solve --export-html ctf_report.html
        ;;
    "test")
        echo "[*] Menjalankan unit & integration test suite..."
        uv run --offline pytest -v 2>/dev/null || uv run pytest -v
        ;;
    "lint")
        echo "[*] Memeriksa kualitas kode dengan Ruff..."
        uv run --offline ruff check backend tests 2>/dev/null || uv run ruff check backend tests
        ;;
    *)
        # Teruskan argumen apa pun langsung ke ctf-solve
        uv run --offline ctf-solve "$@" 2>/dev/null || uv run ctf-solve "$@"
        ;;
esac
