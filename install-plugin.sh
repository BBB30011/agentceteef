#!/usr/bin/env bash
# ==============================================================================
#  ⚡ Agent CeTeEf — Antigravity Global Plugin Installer
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="$HOME/.gemini/config/plugins/agentceteef"

echo "=========================================================="
echo "  ⚡ Menginstal Agent CeTeEf sebagai Plugin Antigravity"
echo "=========================================================="

# 1. Pastikan setup lingkungan lokal siap
"$SCRIPT_DIR/setup.sh"

# 2. Pastikan direktori plugin Antigravity ada
mkdir -p "$HOME/.gemini/config/plugins"

# 3. Hubungkan (symlink) repositori ini ke folder plugin Antigravity
if [ -L "$TARGET_DIR" ] || [ -e "$TARGET_DIR" ]; then
    echo "[*] Memperbarui symlink plugin yang sudah ada di: $TARGET_DIR"
    rm -rf "$TARGET_DIR"
fi

ln -s "$SCRIPT_DIR" "$TARGET_DIR"
echo "[+] Berhasil menghubungkan plugin ke: $TARGET_DIR"

# 4. Validasi keberadaan file manifest dan skill
if [ -f "$TARGET_DIR/plugin.json" ] && [ -f "$TARGET_DIR/skills/agentceteef/SKILL.md" ]; then
    echo "[✓] Manifest plugin.json dan skill agentceteef terverifikasi aktif!"
fi

echo ""
echo "=========================================================="
echo "  🎉 Instalasi Plugin Antigravity Berhasil!"
echo "  Kini Antigravity memiliki keahlian 'agentceteef' secara global."
echo "  Anda bisa langsung meminta Antigravity di chat atau CLI:"
echo "    - 'Pecahkan tantangan di folder ... dengan agentceteef'"
echo "    - 'Lakukan cascade auto-decode pada string ini ...'"
echo "=========================================================="
