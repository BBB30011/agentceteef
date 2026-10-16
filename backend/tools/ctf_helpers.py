"""Domain-specific CTF helper tools — Binary analysis, Crypto decoding, and Flag discovery."""

from __future__ import annotations

import base64
import binascii
import logging
import re
import shlex
import urllib.parse
from typing import Any

logger = logging.getLogger(__name__)

FLAG_PATTERN = re.compile(r"([a-zA-Z0-9_\-\.\+]+{[^}\n\r\t ]{3,120}})")


def extract_flag_candidates(text: str) -> list[str]:
    """Find all potential CTF flag patterns in any string."""
    if not text:
        return []
    matches = FLAG_PATTERN.findall(text)
    # Filter out obvious false positives and placeholders
    filtered = []
    for m in matches:
        m_strip = m.strip()
        lower = m_strip.lower()
        if any(bad in lower for bad in ["{placeholder}", "{flag}", "{your_flag}", "{fake_flag}", "{test}", "example{"]):
            continue
        filtered.append(m_strip)
    return list(dict.fromkeys(filtered))



async def do_checksec(sandbox: Any, binary_path: str) -> str:
    """Analyze security mitigations (RELRO, Stack Canary, NX, PIE) on an ELF binary."""
    safe_path = shlex.quote(binary_path)
    # Try checksec if installed, else fallback to readelf
    cmd = (
        f"checksec --file={safe_path} 2>/dev/null || "
        f"(readelf -l {safe_path} 2>/dev/null && readelf -d {safe_path} 2>/dev/null) || "
        f"file {safe_path}"
    )
    res = await sandbox.exec(cmd, timeout_s=15)
    out = (res.stdout + "\n" + res.stderr).strip()
    return out or f"No checksec output for {binary_path}"


async def do_decompile(sandbox: Any, binary_path: str, symbol: str = "main") -> str:
    """Disassemble or decompile a target symbol in a binary using radare2 or objdump."""
    safe_bin = shlex.quote(binary_path)
    safe_sym = shlex.quote(symbol)

    # First try radare2 pdf (print disassembled function)
    cmd = (
        f"r2 -q -c 'aaa; pdf @ {safe_sym}' {safe_bin} 2>/dev/null || "
        f"objdump -d --no-show-raw-insn -M intel {safe_bin} | grep -A 40 '<{safe_sym}>:' 2>/dev/null || "
        f"objdump -d {safe_bin} | head -n 80"
    )
    res = await sandbox.exec(cmd, timeout_s=30)
    out = res.stdout.strip()
    if not out or "Cannot find" in out:
        return f"Could not disassemble '{symbol}' in {binary_path}. Error:\n{res.stderr.strip()}"
    return out[:12000]


async def do_find_flags_in_workspace(sandbox: Any, directory: str = "/challenge") -> str:
    """Rapidly grep for flag-like strings across all files in workspace."""
    safe_dir = shlex.quote(directory)
    cmd = (
        f"grep -rEahoI '[a-zA-Z0-9_-]+{{[^}}]{{4,100}}}}' {safe_dir} 2>/dev/null | sort -u | head -n 30"
    )
    res = await sandbox.exec(cmd, timeout_s=30)
    out = res.stdout.strip()
    if not out:
        return f"No obvious flag patterns found in {directory}."
    return f"Discovered potential flag candidates:\n{out}"


def do_quick_decode(text: str, operation: str) -> str:
    """Quickly decode or convert encoded strings (base64, hex, rot13, url)."""
    text = text.strip()
    op = operation.lower().strip()
    try:
        if op == "base64" or op == "b64":
            return base64.b64decode(text).decode("utf-8", errors="replace")
        elif op == "hex":
            clean = text.replace(" ", "").replace("0x", "")
            return binascii.unhexlify(clean).decode("utf-8", errors="replace")
        elif op == "rot13":
            import codecs
            return codecs.decode(text, "rot_13")
        elif op == "url":
            return urllib.parse.unquote(text)
        elif op == "binary" or op == "bin":
            clean = "".join(text.split())
            chars = [chr(int(clean[i : i + 8], 2)) for i in range(0, len(clean), 8)]
            return "".join(chars)
        else:
            return f"Unknown operation '{operation}'. Supported: base64, hex, rot13, url, binary"
    except Exception as e:
        return f"Decoding error for '{operation}': {e}"
