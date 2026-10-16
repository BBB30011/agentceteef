"""Self-healing error diagnostic and auto-recovery engine for CTF solvers."""

from __future__ import annotations

import re


def diagnose_execution_error(output: str, exit_code: int = 0, command: str = "") -> str | None:
    """Analyze tool/bash output, stderr, and exit codes to produce immediate actionable self-healing recovery advice."""
    if not output and exit_code == 0:
        return None

    text = output.lower()
    diagnoses: list[str] = []

    # 1. Missing Python module
    mod_match = re.search(r"ModuleNotFoundError:\s+No module named\s+['\"]([^'\"]+)['\"]", output) or re.search(
        r"ImportError:\s+cannot import name\s+['\"]([^'\"]+)['\"]", output
    )
    if mod_match:
        mod_name = mod_match.group(1)
        diagnoses.append(
            f"• Python Module Missing: '{mod_name}'.\n"
            f"  FIX: Run `python3 -m pip install {mod_name}` or write a pure-python fallback implementation."
        )

    # 2. Segmentation fault (SIGSEGV / exit code 139)
    if "segmentation fault" in text or exit_code == 139 or exit_code == -11:
        diagnoses.append(
            "• Segmentation Fault (SIGSEGV / code 139) detected.\n"
            "  FIX: Memory corruption or buffer overflow. In exploitation, verify your cyclic offset to RIP/EIP.\n"
            "  Trace crash with: `gdb -q -batch -ex 'r' -ex 'bt' <binary>` or check ASLR/PIE offsets."
        )

    # 3. Stack Canary violation
    if "stack smashing detected" in text or "*** stack smashing detected ***" in text:
        diagnoses.append(
            "• Stack Canary Protection Violation (Stack Smashing Detected)!\n"
            "  FIX: The buffer overflow overwrote the stack canary. You must leak the canary value\n"
            "  (via format string `%p` or memory leak) and overwrite it with its original value."
        )

    # 4. Connection refused
    if "connection refused" in text or "errno 111" in text:
        diagnoses.append(
            "• Connection Refused (Target port closed / server inactive).\n"
            "  FIX: Verify target hostname and port. Check running processes with `ps aux` or `netstat -tlpn`.\n"
            "  If using Docker, ensure challenge container service is started."
        )

    # 5. Permission denied (exit code 126 or 'Permission denied')
    if "permission denied" in text or exit_code == 126:
        diagnoses.append(
            "• Permission Denied.\n"
            "  FIX: The file is not marked executable or lacks read permissions.\n"
            "  Run `chmod +x <target_file>` to make binaries or exploit scripts executable."
        )

    # 6. Command not found (exit code 127)
    if "command not found" in text or exit_code == 127:
        cmd_name = command.split()[0] if command else "command"
        diagnoses.append(
            f"• Command not found: '{cmd_name}'.\n"
            "  FIX: Check installed tools with `cat /tools.txt` or `which <tool>`.\n"
            "  Use alternative tools (e.g. `objdump` if `r2` missing, python scripts if specialized CLI missing)."
        )

    # 7. Python Syntax or Indentation Error
    if "syntaxerror" in text or "indentationerror" in text:
        diagnoses.append(
            "• Python Syntax or Indentation Error detected.\n"
            "  FIX: Verify Python code syntax. If running legacy code, check Python 2 vs Python 3 compatibility\n"
            "  (e.g., `print` statement vs function, `xrange` vs `range`, `bytes` vs `str`)."
        )

    # 8. Pwntools / Network EOFError
    if "eoferror" in text and ("connection reset" in text or "closed" in text or "pwntools" in text or "peer" in text):
        diagnoses.append(
            "• Service Closed Connection (EOF / Connection Reset).\n"
            "  FIX: The remote or local binary terminated prematurely. Possible causes:\n"
            "  - Payload length or null byte caused bad read/scanf.\n"
            "  - Unhandled exception or crash before flag printout.\n"
            "  - Missing interactive shell call (`p.interactive()`)."
        )

    # 9. Encoding or UTF-8 decode error
    if "unicodedecodeerror" in text or "codec can't decode byte" in text:
        diagnoses.append(
            "• Unicode / UTF-8 Decode Error.\n"
            "  FIX: The data is binary or encrypted. Read in binary mode (`'rb'`) and manipulate as `bytes`.\n"
            "  Do not attempt to decode as UTF-8 string."
        )

    # 10. Archive extraction error
    if "end-of-central-directory signature not found" in text or "not a valid tar archive" in text:
        diagnoses.append(
            "• Archive Corrupted or Format Mismatch.\n"
            "  FIX: File extension might be fake. Run `file <archive_file>` to inspect true magic bytes\n"
            "  and use `extract_archive` or `file_info` tool."
        )

    if not diagnoses:
        return None

    return "\n".join(diagnoses)
