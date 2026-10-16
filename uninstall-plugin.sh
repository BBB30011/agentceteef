#!/usr/bin/env bash
# ==============================================================================
#  ⚡ Agent CeTeEf — Antigravity Global Plugin Uninstaller
# ==============================================================================
set -e

TARGET_DIR="$HOME/.gemini/config/plugins/agentceteef"

echo "=========================================================="
echo "  ⚡ Mencopot Plugin Agent CeTeEf dari Antigravity"
echo "=========================================================="

if [ -L "$TARGET_DIR" ] || [ -e "$TARGET_DIR" ]; then
    rm -rf "$TARGET_DIR"
    echo "[✓] Plugin agentceteef berhasil dicopot dari Antigravity."
else
    echo "[i] Plugin agentceteef tidak terpasang di $TARGET_DIR."
fi
