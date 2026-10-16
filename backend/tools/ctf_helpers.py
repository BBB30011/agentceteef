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


def do_auto_decode(text: str) -> str:
    """Automatically try multiple common CTF decodings and detect flags instantly."""
    text = text.strip()
    if not text:
        return "Empty input string."

    results: dict[str, str] = {}
    found_flags: list[str] = []

    # 1. Base64
    try:
        b64 = base64.b64decode(text, validate=True).decode("utf-8", errors="replace")
        if b64 and b64.isprintable():
            results["base64"] = b64
            found_flags.extend(extract_flag_candidates(b64))
    except Exception:
        pass

    # 2. Hex
    try:
        clean_hex = text.replace(" ", "").replace("0x", "").replace("\\x", "")
        if len(clean_hex) % 2 == 0 and len(clean_hex) >= 2:
            hx = binascii.unhexlify(clean_hex).decode("utf-8", errors="replace")
            if hx and hx.isprintable():
                results["hex"] = hx
                found_flags.extend(extract_flag_candidates(hx))
    except Exception:
        pass

    # 3. Base32
    try:
        b32 = base64.b32decode(text.upper(), casefold=True).decode("utf-8", errors="replace")
        if b32 and b32.isprintable():
            results["base32"] = b32
            found_flags.extend(extract_flag_candidates(b32))
    except Exception:
        pass

    # 4. Rot13
    try:
        import codecs
        r13 = codecs.decode(text, "rot_13")
        results["rot13"] = r13
        found_flags.extend(extract_flag_candidates(r13))
    except Exception:
        pass

    # 5. URL
    try:
        unquoted = urllib.parse.unquote(text)
        if unquoted != text:
            results["url"] = unquoted
            found_flags.extend(extract_flag_candidates(unquoted))
    except Exception:
        pass

    # 6. Binary
    try:
        clean_bin = "".join(text.split())
        if all(c in "01" for c in clean_bin) and len(clean_bin) >= 8 and len(clean_bin) % 8 == 0:
            bin_str = "".join(chr(int(clean_bin[i : i + 8], 2)) for i in range(0, len(clean_bin), 8))
            if bin_str and bin_str.isprintable():
                results["binary"] = bin_str
                found_flags.extend(extract_flag_candidates(bin_str))
    except Exception:
        pass

    lines = ["=== Auto Decode Results ==="]
    if found_flags:
        lines.append(f"🚩 FLAG(S) REVEALED: {', '.join(set(found_flags))}\n")

    if not results:
        return "No standard encodings could be automatically decoded."

    for method, decoded in results.items():
        lines.append(f"[{method}]: {decoded[:200]}")

    return "\n".join(lines)


def do_entropy(data: bytes | str) -> float:
    """Calculate Shannon entropy (0.0 to 8.0) of data to detect encryption/compression."""
    import math
    if isinstance(data, str):
        data = data.encode("utf-8", errors="replace")
    if not data:
        return 0.0

    entropy = 0.0
    length = len(data)
    frequencies = [0] * 256
    for byte in data:
        frequencies[byte] += 1

    for count in frequencies:
        if count > 0:
            prob = count / length
            entropy -= prob * math.log2(prob)

    return round(entropy, 4)

