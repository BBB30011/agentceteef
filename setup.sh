#!/usr/bin/env bash
set -e

echo "=============================================="
echo "  CTF Agent Swarm — Environment Setup"
echo "=============================================="

# 1. Check Python
PYTHON_BIN=$(which python3 || echo "")
if [ -z "$PYTHON_BIN" ]; then
    echo "[-] Error: python3 is not installed."
    exit 1
fi
echo "[+] Detected Python: $($PYTHON_BIN --version)"

# 2. Check or install uv
if ! command -v uv &> /dev/null; then
    echo "[*] Installing astral uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi
echo "[+] uv version: $(uv --version)"

# 3. Setup virtualenv and dependencies
echo "[*] Syncing dependencies with uv..."
uv sync --offline 2>/dev/null || uv sync

# 4. Copy .env if not exists
if [ ! -f ".env" ]; then
    echo "[*] Creating .env from .env.example..."
    cp .env.example .env
    echo "[!] Please edit .env with your CTFd credentials and API keys!"
else
    echo "[+] .env file already exists."
fi

# 5. Check Docker
echo "[*] Checking Docker status..."
if command -v docker &> /dev/null && docker ps &> /dev/null; then
    echo "[+] Docker daemon is running and accessible."
    if ! docker images -q ctf-sandbox &> /dev/null || [ -z "$(docker images -q ctf-sandbox)" ]; then
        echo "[i] Docker sandbox image 'ctf-sandbox' is not built yet."
        echo "    Run 'make build-sandbox' or 'docker build -f sandbox/Dockerfile.sandbox -t ctf-sandbox .' when ready."
    else
        echo "[+] Sandbox image 'ctf-sandbox' is ready."
    fi
else
    echo "[!] Docker is not accessible. CTF Agent will automatically use Local Sandbox mode."
fi

echo ""
echo "[✓] Setup complete! You can now run:"
echo "    uv run ctf-solve --help"
echo "    uv run ctf-solve --challenge <path_to_challenge>"
echo "    uv run ctf-solve"
echo "=============================================="
