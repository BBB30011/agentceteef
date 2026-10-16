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

### 1. Multi-Layer Cascade Auto-Decoder
Tries single and multi-layer cascade decodings (e.g. `Base64 -> ROT13`, `Hex -> Base64`) and detects flag patterns automatically:
```python
from backend.tools.ctf_helpers import do_auto_decode

result = do_auto_decode("<encoded_text>")
print(result)
```

### 2. Single-Byte XOR Brute Force (0..255)
Brute forces all 256 byte keys on raw strings or hex values to detect hidden flags or plain English text:
```python
from backend.tools.ctf_helpers import do_single_byte_xor

result = do_single_byte_xor("<hex_or_string>")
print(result)
```

### 3. Hash Identification & Parameter Suggestion
Identifies hash types based on length, prefix, and charset, and suggests Hashcat/John modes:
```python
from backend.tools.ctf_helpers import do_identify_hash

result = do_identify_hash("<hash_candidate>")
print(result)
```

### 4. File Forensics & Magic Byte Inspection
Inspects true file types, MIME types, and header bytes to reveal disguised file formats:
```python
# In sandbox:
from backend.tools.ctf_helpers import do_file_info
info = await do_file_info(sandbox, "<path_to_file>")
```

### 5. Printable Strings Extraction with Regex Filter
Extracts printable strings from binaries and scans for flags:
```python
from backend.tools.ctf_helpers import do_strings_search
strings_out = await do_strings_search(sandbox, "<path_to_binary>", min_len=4, filter_pattern="flag|ctf")
```

---

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
