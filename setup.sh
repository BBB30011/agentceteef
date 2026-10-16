#!/usr/bin/env bash
# ==============================================================================
#  ⚡ Agent CeTeEf (agentceteef) — Environment Setup & Diagnostic Wizard
# ==============================================================================
set -e

echo "=========================================================="
echo "  ⚡ Agent CeTeEf (agentceteef) — Environment Setup"
echo "=========================================================="

# 1. Check Python
PYTHON_BIN=$(command -v python3 || echo "")
if [ -z "$PYTHON_BIN" ]; then
    echo "[-] Error: python3 is not installed."
    exit 1
fi
echo "[+] Python: $($PYTHON_BIN --version)"

# 2. Check or install uv
if ! command -v uv &> /dev/null; then
    echo "[*] Menginstal paket manager astral uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi
echo "[+] Astral uv: $(uv --version)"

# 3. Setup virtualenv and dependencies
echo "[*] Melakukan sinkronisasi dependensi dengan uv..."
uv sync --offline 2>/dev/null || uv sync

# 4. Copy .env if not exists
if [ ! -f ".env" ]; then
    echo "[*] Membuat file .env dari template .env.example..."
    cp .env.example .env
    echo "[!] Jangan lupa sesuaikan kredensial di file .env jika diperlukan."
else
    echo "[+] File .env sudah ada."
fi

# 5. Check Docker & Sandbox
echo "[*] Memeriksa daemon Docker..."
if command -v docker &> /dev/null && docker ps &> /dev/null; then
    echo "[+] Docker: Daemon aktif dan berjalan normal."
    if ! docker images -q ctf-sandbox &> /dev/null || [ -z "$(docker images -q ctf-sandbox)" ]; then
        echo "[i] Image 'ctf-sandbox' belum di-build. (Opsional: jalankan 'make build-sandbox')"
    else
        echo "[+] Docker image 'ctf-sandbox' siap digunakan."
    fi
else
    echo "[i] Docker tidak aktif. Solver otomatis menggunakan mode isolasi Host Lokal (Kali Linux)."
fi

# 6. Check CTF Host Security Toolchain
echo ""
echo "=== Diagnostik Toolchain CTF Host ==="
for tool in checksec r2 gdb strings file python3; do
    if command -v "$tool" &> /dev/null; then
        echo "  [✓] $tool: $(command -v "$tool")"
    else
        echo "  [-] $tool: tidak ditemukan di PATH (opsional untuk kategori tertentu)"
    fi
done

# Check Antigravity CLI
if command -v agy &> /dev/null || [ -f "$HOME/.local/bin/agy" ]; then
    echo "  [✓] agy (Antigravity CLI): Siap untuk Mode Tanpa Token (\$0 Cost)"
else
    echo "  [-] agy (Antigravity CLI): tidak terdeteksi (Mode Tanpa Token membutuhkan agy)"
fi

echo ""
echo "=========================================================="
echo "  [✓] Konfigurasi selesai! Anda dapat menjalankan:"
echo "      ./run.sh            -> Interactive CLI Wizard"
echo "      ./run.sh demo       -> Uji tantangan bawaan"
echo "      ./run.sh tokenless  -> Mode Tanpa Token"
echo "      ./run.sh fast       -> Swarm latensi rendah"
echo "=========================================================="
