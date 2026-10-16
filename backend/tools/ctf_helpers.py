"""Domain-specific CTF helper tools — Binary analysis, Crypto decoding, and Flag discovery."""

from __future__ import annotations

import base64
import binascii
import json
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


async def do_file_info(sandbox: Any, file_path: str) -> str:
    """Inspect true file type, mime-type, size, and header bytes to detect disguised formats."""
    safe_path = shlex.quote(file_path)
    cmd = (
        f"file -b {safe_path} 2>/dev/null; "
        f"file --mime-type -b {safe_path} 2>/dev/null; "
        f"ls -lh {safe_path} 2>/dev/null; "
        f"(head -c 32 {safe_path} | xxd -p 2>/dev/null || true)"
    )
    res = await sandbox.exec(cmd, timeout_s=15)
    out = res.stdout.strip()
    if not out:
        return f"Could not inspect file {file_path}. {res.stderr.strip()}"
    return f"=== File Inspection: {file_path} ===\n{out}"


async def do_strings_search(sandbox: Any, file_path: str, min_len: int = 6, filter_pattern: str = "") -> str:
    """Extract printable strings from binary/data file with optional keyword filtering."""
    safe_path = shlex.quote(file_path)
    min_len = max(3, min(min_len, 64))
    if filter_pattern:
        safe_filt = shlex.quote(filter_pattern)
        cmd = f"strings -n {min_len} {safe_path} 2>/dev/null | grep -iE {safe_filt} | head -n 40"
    else:
        cmd = f"strings -n {min_len} {safe_path} 2>/dev/null | head -n 60"
    res = await sandbox.exec(cmd, timeout_s=20)
    out = res.stdout.strip()
    if not out:
        return f"No matching strings found in {file_path} (min_length={min_len})."
    flags = extract_flag_candidates(out)
    flag_line = f"🚩 POTENTIAL FLAGS DISCOVERED: {', '.join(flags)}\n\n" if flags else ""
    return f"=== Strings Extraction ({file_path}) ===\n{flag_line}{out}"


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


def _decode_candidates(text: str) -> dict[str, str]:
    """Perform a single round of candidate decodings."""
    results: dict[str, str] = {}
    clean_text = text.strip()
    if not clean_text:
        return results

    # 1. Base64
    try:
        b64 = base64.b64decode(clean_text, validate=True).decode("utf-8", errors="replace")
        if b64 and b64.isprintable() and len(b64) >= 3 and b64 != clean_text:
            results["base64"] = b64
    except Exception:
        pass

    # 2. Hex
    try:
        clean_hex = clean_text.replace(" ", "").replace("0x", "").replace("\\x", "")
        if len(clean_hex) % 2 == 0 and len(clean_hex) >= 2 and all(c in "0123456789abcdefABCDEF" for c in clean_hex):
            hx = binascii.unhexlify(clean_hex).decode("utf-8", errors="replace")
            if hx and hx.isprintable() and hx != clean_text:
                results["hex"] = hx
    except Exception:
        pass

    # 3. Base32
    try:
        b32_clean = clean_text.upper()
        if len(b32_clean) >= 4 and all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567=" for c in b32_clean):
            b32 = base64.b32decode(b32_clean, casefold=True).decode("utf-8", errors="replace")
            if b32 and b32.isprintable() and b32 != clean_text:
                results["base32"] = b32
    except Exception:
        pass

    # 4. Rot13
    try:
        import codecs
        r13 = codecs.decode(clean_text, "rot_13")
        if r13 != clean_text:
            results["rot13"] = r13
    except Exception:
        pass

    # 5. URL
    try:
        unquoted = urllib.parse.unquote(clean_text)
        if unquoted != clean_text:
            results["url"] = unquoted
    except Exception:
        pass

    # 6. Binary
    try:
        clean_bin = "".join(clean_text.split())
        if all(c in "01" for c in clean_bin) and len(clean_bin) >= 8 and len(clean_bin) % 8 == 0:
            bin_str = "".join(chr(int(clean_bin[i : i + 8], 2)) for i in range(0, len(clean_bin), 8))
            if bin_str and bin_str.isprintable():
                results["binary"] = bin_str
    except Exception:
        pass

    return results


def do_auto_decode(text: str) -> str:
    """Automatically try single and multi-layer cascade decodings and detect flags instantly."""
    text = text.strip()
    if not text:
        return "Empty input string."

    # Direct flag check
    direct_flags = extract_flag_candidates(text)
    if direct_flags and any(f.lower().startswith(("flag{", "ctf{", "picoctf{")) for f in direct_flags):
        return f"=== Auto Decode Results ===\n🚩 FLAG(S) REVEALED DIRECTLY: {', '.join(set(direct_flags))}"

    layer1 = _decode_candidates(text)
    found_flags: list[tuple[str, str]] = []

    # Check layer 1
    for method, decoded in layer1.items():
        for fl in extract_flag_candidates(decoded):
            found_flags.append((method, fl))

    # Always evaluate layer 2 cascade (e.g. base64 -> rot13, hex -> base64)
    layer2_results: dict[str, str] = {}
    for m1, d1 in list(layer1.items())[:6]:
        sub_candidates = _decode_candidates(d1)
        for m2, d2 in sub_candidates.items():
            chain_key = f"{m1} -> {m2}"
            layer2_results[chain_key] = d2
            for fl in extract_flag_candidates(d2):
                found_flags.append((chain_key, fl))

    # Prioritize real flags (e.g. flag{...}) over ROT13 placeholders (e.g. synt{...})
    def _flag_rank(item: tuple[str, str]) -> int:
        _, fl = item
        lower = fl.lower()
        if lower.startswith(("flag{", "ctf{", "picoctf{", "sec{")):
            return 0
        if lower.startswith("synt{"):
            return 10
        return 5

    found_flags.sort(key=_flag_rank)

    # Deduplicate while preserving rank order
    seen: set[str] = set()
    deduped_flags: list[tuple[str, str]] = []
    for chain, fl in found_flags:
        if fl not in seen:
            seen.add(fl)
            deduped_flags.append((chain, fl))

    lines = ["=== Auto Decode Results ==="]
    if deduped_flags:
        for chain, fl in deduped_flags:
            lines.append(f"🚩 FLAG(S) REVEALED via [{chain}]: {fl}")
        return "\n".join(lines)

    if not layer1:
        return "No standard encodings could be automatically decoded."

    for method, decoded in layer1.items():
        lines.append(f"[{method}]: {decoded[:150]}")
    for chain, decoded in list(layer2_results.items())[:5]:
        lines.append(f"[{chain}]: {decoded[:150]}")

    return "\n".join(lines)


def do_single_byte_xor(data_input: str) -> str:
    """Brute force single-byte XOR (0..255) to detect hidden flags or plain English text."""
    raw = data_input.strip()
    if not raw:
        return "Empty input."

    # Attempt hex decoding first
    payload: bytes
    try:
        clean_hex = raw.replace(" ", "").replace("0x", "").replace("\\x", "")
        if len(clean_hex) % 2 == 0 and all(c in "0123456789abcdefABCDEF" for c in clean_hex):
            payload = binascii.unhexlify(clean_hex)
        else:
            payload = raw.encode("utf-8", errors="replace")
    except Exception:
        payload = raw.encode("utf-8", errors="replace")

    candidates: list[tuple[int, str, list[str]]] = []
    for key in range(256):
        dec = bytes([b ^ key for b in payload])
        try:
            text = dec.decode("utf-8", errors="ignore")
            if text and text.isprintable():
                flags = extract_flag_candidates(text)
                if flags or any(kw in text.lower() for kw in ["flag", "ctf{", "pass", "key="]):
                    candidates.append((key, text, flags))
        except Exception:
            continue

    if not candidates:
        return f"No readable plaintext or flags found with single-byte XOR across {len(payload)} bytes."

    lines = [f"=== Single-Byte XOR Candidates ({len(candidates)} matches) ==="]
    for key, text, flags in candidates[:8]:
        flag_str = f" 🚩 [FLAGS: {', '.join(flags)}]" if flags else ""
        lines.append(f"Key 0x{key:02x} ({key:3d}): {text[:120]}{flag_str}")

    return "\n".join(lines)


def do_identify_hash(hash_candidate: str) -> str:
    """Identify hash algorithm based on length, prefix, and character set."""
    h = hash_candidate.strip()
    if not h:
        return "Empty hash string."

    lines = [f"Hash Analysis for: '{h[:60]}'"]
    clean_h = h.lower()
    is_hex = all(c in "0123456789abcdef" for c in clean_h)

    # Prefix checks
    if h.startswith("$2a$") or h.startswith("$2b$") or h.startswith("$2y$"):
        lines.append("• Likely: bcrypt (Blowfish-based crypt)")
        lines.append("  Hashcat: -m 3200 | John: bcrypt")
        return "\n".join(lines)
    if h.startswith("$6$"):
        lines.append("• Likely: SHA-512 crypt (Linux /etc/shadow standard)")
        lines.append("  Hashcat: -m 1800 | John: sha512crypt")
        return "\n".join(lines)
    if h.startswith("$1$"):
        lines.append("• Likely: MD5 crypt (FreeBSD/Linux legacy /etc/shadow)")
        lines.append("  Hashcat: -m 500 | John: md5crypt")
        return "\n".join(lines)

    if is_hex:
        length = len(clean_h)
        if length == 32:
            lines.append("• Likely: MD5 (Message-Digest 5) OR NTLM (Windows NT LAN Manager)")
            lines.append("  Hashcat: -m 0 (MD5) / -m 1000 (NTLM)")
        elif length == 40:
            lines.append("• Likely: SHA-1 / RIPEMD-160")
            lines.append("  Hashcat: -m 100 (SHA-1)")
        elif length == 56:
            lines.append("• Likely: SHA-224 / SHA3-224")
        elif length == 64:
            lines.append("• Likely: SHA-256 (Secure Hash Algorithm 2, 256-bit)")
            lines.append("  Hashcat: -m 1400 (SHA-256)")
        elif length == 96:
            lines.append("• Likely: SHA-384")
            lines.append("  Hashcat: -m 10800")
        elif length == 128:
            lines.append("• Likely: SHA-512 / Whirlpool")
            lines.append("  Hashcat: -m 1700 (SHA-512)")
        elif length == 8:
            lines.append("• Likely: CRC32 / Adler32 checksum")
        else:
            lines.append(f"• Hex string of length {length} (uncommon standard hash length)")
    else:
        lines.append("• Non-hex format. Check Base64, bcrypt, or custom salt formatting.")

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


def do_rot_bruteforce(ciphertext: str) -> str:
    """Brute force all 25 Caesar / ROT cipher shifts (1..25) to uncover hidden flags or messages."""
    text = ciphertext.strip()
    if not text:
        return "Empty input."

    results: list[tuple[int, str, list[str]]] = []
    for shift in range(1, 26):
        rotated_chars = []
        for ch in text:
            if "a" <= ch <= "z":
                rotated_chars.append(chr((ord(ch) - ord("a") + shift) % 26 + ord("a")))
            elif "A" <= ch <= "Z":
                rotated_chars.append(chr((ord(ch) - ord("A") + shift) % 26 + ord("A")))
            else:
                rotated_chars.append(ch)
        candidate = "".join(rotated_chars)
        flags = extract_flag_candidates(candidate)
        results.append((shift, candidate, flags))

    # Check if any rotation revealed flags
    flagged = [item for item in results if item[2]]

    lines = ["=== ROT / Caesar Cipher Brute-Force (1..25) ==="]
    if flagged:
        for shift, _cand, flags in flagged:
            lines.append(f"🚩 [FLAG DETECTED at ROT-{shift}]: {', '.join(flags)}")
        lines.append("")

    for shift, candidate, flags in results:
        flag_mark = f"  🚩 [{', '.join(flags)}]" if flags else ""
        lines.append(f"ROT-{shift:02d}: {candidate[:100]}{flag_mark}")

    return "\n".join(lines)


def do_jwt_decode(token: str) -> str:
    """Decode and inspect JSON Web Tokens (JWT) for hidden claims, signature algorithms, and vulnerabilities."""
    clean = token.strip().strip('"').strip("'")
    parts = clean.split(".")
    if len(parts) < 2:
        return "Invalid JWT token: Must contain at least header and payload separated by '.'."

    def _b64_url_decode(s: str) -> bytes:
        rem = len(s) % 4
        if rem > 0:
            s += "=" * (4 - rem)
        return base64.urlsafe_b64decode(s.encode("ascii"))

    header_json: dict[str, Any] = {}
    payload_json: dict[str, Any] = {}

    try:
        header_raw = _b64_url_decode(parts[0]).decode("utf-8", errors="replace")
        header_json = json.loads(header_raw)
    except Exception as e:
        header_raw = f"(error decoding header: {e})"

    try:
        payload_raw = _b64_url_decode(parts[1]).decode("utf-8", errors="replace")
        payload_json = json.loads(payload_raw)
    except Exception as e:
        payload_raw = f"(error decoding payload: {e})"

    sig_present = len(parts) >= 3 and bool(parts[2])

    lines = ["=== JWT Token Analysis ==="]

    # Flag discovery in token, header, or payload
    flags = extract_flag_candidates(clean) + extract_flag_candidates(payload_raw)
    flags = list(dict.fromkeys(flags))
    if flags:
        lines.append(f"🚩 FLAG(S) FOUND IN JWT: {', '.join(flags)}\n")

    lines.append(f"Header:\n{json.dumps(header_json, indent=2) if header_json else header_raw}")
    lines.append(f"\nPayload:\n{json.dumps(payload_json, indent=2) if payload_json else payload_raw}")
    lines.append(f"\nSignature: {'Present (' + parts[2][:20] + '...)' if sig_present else 'None / Empty'}")

    # Vulnerability & security checks
    vulns: list[str] = []
    alg = str(header_json.get("alg", "")).lower()
    if alg == "none":
        vulns.append("⚠️ CRITICAL: Token algorithm is set to 'none' — signature verification can be completely bypassed!")
    elif alg.startswith("hs"):
        vulns.append(f"ℹ️ HMAC Symmetric ({header_json.get('alg')}): Check for weak secret with hashcat -m 16500 or jwt-tool.")
        vulns.append("ℹ️ If the server expects RS256, test for Key Confusion (HMAC using the public RSA key as the HMAC secret).")
    elif alg.startswith("rs"):
        vulns.append(f"ℹ️ RSA Asymmetric ({header_json.get('alg')}): Test for algorithm switching (change to HS256 with public key), or jku/kid injection.")

    if "admin" in payload_json and not payload_json["admin"]:
        vulns.append("💡 Notice: 'admin' claim is false. Try modifying payload to {\"admin\": true} and testing unsigned or none-alg.")
    if "role" in payload_json and payload_json["role"] != "admin":
        vulns.append(f"💡 Notice: 'role' is '{payload_json['role']}'. Try elevating to 'admin' or 'root'.")

    if vulns:
        lines.append("\nSecurity Analysis:")
        for v in vulns:
            lines.append(f"  {v}")

    return "\n".join(lines)


async def do_extract_archive(sandbox: Any, archive_path: str, dest_dir: str = "") -> str:
    """Extract compressed archives (.zip, .tar, .tar.gz, .tgz, .bz2, .xz, .7z) and search for flags."""
    safe_src = shlex.quote(archive_path)
    if not dest_dir:
        dest_dir = f"{archive_path}_extracted"
    safe_dest = shlex.quote(dest_dir)

    cmd = (
        f"mkdir -p {safe_dest} && "
        f"FTYPE=$(file -b {safe_src} 2>/dev/null); "
        f"if [[ \"$FTYPE\" == *Zip* ]] || [[ \"{archive_path}\" == *.zip ]]; then "
        f"  unzip -q -o {safe_src} -d {safe_dest} 2>/dev/null || python3 -c 'import zipfile; zipfile.ZipFile(\"{archive_path}\").extractall(\"{dest_dir}\")'; "
        f"elif [[ \"$FTYPE\" == *gzip* ]] || [[ \"{archive_path}\" == *.tar.gz ]] || [[ \"{archive_path}\" == *.tgz ]]; then "
        f"  tar -xzf {safe_src} -C {safe_dest} 2>/dev/null || gzip -dc {safe_src} > {safe_dest}/extracted_file 2>/dev/null; "
        f"elif [[ \"$FTYPE\" == *bzip2* ]] || [[ \"{archive_path}\" == *.tar.bz2 ]] || [[ \"{archive_path}\" == *.tbz2 ]]; then "
        f"  tar -xjf {safe_src} -C {safe_dest} 2>/dev/null || bzip2 -dc {safe_src} > {safe_dest}/extracted_file 2>/dev/null; "
        f"elif [[ \"$FTYPE\" == *XZ* ]] || [[ \"{archive_path}\" == *.tar.xz ]] || [[ \"{archive_path}\" == *.txz ]]; then "
        f"  tar -xJf {safe_src} -C {safe_dest} 2>/dev/null || xz -dc {safe_src} > {safe_dest}/extracted_file 2>/dev/null; "
        f"elif [[ \"$FTYPE\" == *POSIX\\ tar* ]] || [[ \"{archive_path}\" == *.tar ]]; then "
        f"  tar -xf {safe_src} -C {safe_dest} 2>/dev/null; "
        f"elif [[ \"$FTYPE\" == *7-zip* ]] || [[ \"{archive_path}\" == *.7z ]]; then "
        f"  7z x -y -o{safe_dest} {safe_src} 2>/dev/null; "
        f"else "
        f"  tar -xf {safe_src} -C {safe_dest} 2>/dev/null || unzip -q -o {safe_src} -d {safe_dest} 2>/dev/null; "
        f"fi; "
        f"ls -lah {safe_dest}"
    )

    res = await sandbox.exec(cmd, timeout_s=40)
    out = (res.stdout + "\n" + res.stderr).strip()

    flags_res = await sandbox.exec(
        f"grep -rEahoI '[a-zA-Z0-9_-]+{{[^}}]{{4,100}}}}' {safe_dest} 2>/dev/null | sort -u | head -n 20",
        timeout_s=15,
    )
    flag_out = flags_res.stdout.strip()
    flag_line = f"🚩 EXTRACTED FLAGS DISCOVERED:\n{flag_out}\n\n" if flag_out else ""

    return f"=== Archive Extraction ({archive_path} -> {dest_dir}) ===\n{flag_line}{out}"


