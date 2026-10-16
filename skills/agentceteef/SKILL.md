---
name: agentceteef
description: >-
  Autonomous CTF Multi-Model Solver Swarm & Security Toolchain Engine.
  Use to solve Capture The Flag (CTF) challenges across cryptography,
  reverse engineering, binary exploitation (pwn), web security, and forensics.
---

# Agent CeTeEf — Antigravity CTF Assistant Skill

This skill equips Antigravity agents with state-of-the-art CTF automated reasoning, domain-specific security tools, and multi-model solver capabilities.

---

## 🎯 When to Activate This Skill

Activate this skill when:
- The user asks to solve, analyze, or reverse engineer a CTF challenge (Pwn, Reverse Engineering, Cryptography, Web Security, Forensics, Misc).
- The user provides an encrypted, encoded, or obfuscated ciphertext string (Base64, Hex, Base32, ROT13, multi-layer cascade encoding).
- The user needs binary mitigation analysis (`checksec`), disassembly (`r2` / `objdump`), or binary symbol extraction.
- The user has an unknown file that might be disguised with a fake extension or contains hidden strings/flags.
- The user wants to run single-byte XOR brute force or identify cryptographic hash types (MD5, SHA1, SHA256, bcrypt, NTLM).
- The user is participating in a live CTFd competition and wants to automate challenge analysis, hint injection, and flag submission.

---

## 🛠️ Direct Security Toolchain Operations

Antigravity agents can invoke the built-in domain-specific Python helpers directly:

### 1. All-in-One Automated Security Recon & Vulnerability Audit
Executes end-to-end automated triage (magic bytes, checksec ELF mitigations, archive extraction, crypto detection, strings, and network probe):
```python
from backend.tools.auto_scanner import do_auto_security_scan

audit = await do_auto_security_scan(sandbox, "/challenge/distfiles", connection_info="...")
print(audit.to_markdown())
```

### 2. Multi-Layer Cascade Auto-Decoder
Tries single and multi-layer cascade decodings (e.g. `Base64 -> ROT13`, `Hex -> Base64`) and detects flag patterns automatically:
```python
from backend.tools.ctf_helpers import do_auto_decode

result = do_auto_decode("<encoded_text>")
print(result)
```

### 3. Single-Byte XOR Brute Force (0..255)
Brute forces all 256 byte keys on raw strings or hex values to detect hidden flags or plain English text:
```python
from backend.tools.ctf_helpers import do_single_byte_xor

result = do_single_byte_xor("<hex_or_string>")
print(result)
```

### 4. Hash Identification & Parameter Suggestion
Identifies hash types based on length, prefix, and charset, and suggests Hashcat/John modes:
```python
from backend.tools.ctf_helpers import do_identify_hash

result = do_identify_hash("<hash_candidate>")
print(result)
```

### 5. File Forensics & Magic Byte Inspection
Inspects true file types, MIME types, and header bytes to reveal disguised file formats:
```python
# In sandbox:
from backend.tools.ctf_helpers import do_file_info
info = await do_file_info(sandbox, "<path_to_file>")
```

### 6. Printable Strings Extraction with Regex Filter
Extracts printable strings from binaries and scans for flags:
```python
from backend.tools.ctf_helpers import do_strings_search
strings_out = await do_strings_search(sandbox, "<path_to_binary>", min_len=4, filter_pattern="flag|ctf")
```

### 7. ROT / Caesar Cipher Brute-Force (1..25)
Iterates through all 25 Caesar rotations and highlights flag matches:
```python
from backend.tools.ctf_helpers import do_rot_bruteforce
result = do_rot_bruteforce("<ciphertext>")
```

### 8. JWT Inspection & Vulnerability Analyzer
Decodes JWT headers, payloads, and claims, detects `none` algorithm or symmetric HMAC vulnerabilities:
```python
from backend.tools.ctf_helpers import do_jwt_decode
result = do_jwt_decode("<jwt_token>")
```

### 9. Multi-Format Archive Extractor & Flag Scanner
Unpacks `.zip`, `.tar.gz`, `.tar.bz2`, `.tar.xz`, `.7z` and scans contents for flags:
```python
from backend.tools.ctf_helpers import do_extract_archive
result = await do_extract_archive(sandbox, "<archive_path>", "<dest_dir>")
```

---

## 🛡️ Self-Healing Error Recovery Engine

When commands, exploits, or scripts produce runtime errors, Agent CeTeEf automatically diagnoses root causes and generates targeted recovery advice:
- **Missing Python Packages** (`ModuleNotFoundError`): Suggests auto-installation or pure-python alternatives.
- **Segmentation Faults / SIGSEGV** (`exit 139`): Identifies buffer overflow offset issues, suggesting cyclic patterns and GDB trace commands.
- **Stack Smashing Detected**: Highlights canary overwrite violations and suggests format string leaks.
- **Connection Refused / Resets**: Diagnoses target service state or crashed daemon processes.
- **Permission Denied** (`exit 126`): Suggests `chmod +x` executable remedies.
- **Command Not Found** (`exit 127`): Suggests standard tool fallbacks (`objdump`, Python scripts).
- **Format Mismatch**: Identifies fake archive extensions and checks true magic bytes.

## 🚀 Running the Solver Swarm

To launch an automated solver on a challenge:

```bash
# 1. Solve a challenge directory in dry-run mode (local sandbox, no flag submit):
./run.sh --challenge challenges/<challenge_name> --no-submit

# 2. Tokenless solver ($0 cost using host Kali Linux toolchain):
./run.sh --challenge challenges/<challenge_name> --profile tokenless --no-submit

# 3. High-throughput fast swarm:
./run.sh --challenge challenges/<challenge_name> --profile fast --no-submit

# 4. Generate visual competition report:
./run.sh report-html
```

---

## 📋 Flag Pattern Guidelines

Always look for standard CTF flag formats matching:
- `flag{...}`
- `ctf{...}`
- `picoctf{...}`
- Custom format specified in competition rules.

When confirmed, display the captured flag prominently and report solve duration and winning model.
