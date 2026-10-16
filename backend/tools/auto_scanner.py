"""Automated Security Reconnaissance, Vulnerability Auditing & Triage Engine for CTF challenges."""

from __future__ import annotations

import logging
import re
import shlex
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from backend.tools.ctf_helpers import (
    do_auto_decode,
    do_checksec,
    do_extract_archive,
    do_file_info,
    do_identify_hash,
    do_jwt_decode,
    do_rot_bruteforce,
    do_strings_search,
    extract_flag_candidates,
)

logger = logging.getLogger(__name__)


@dataclass
class SecurityAuditResult:
    target_path: str
    discovered_flags: list[str] = field(default_factory=list)
    file_profiles: list[dict[str, Any]] = field(default_factory=list)
    binary_audits: list[dict[str, Any]] = field(default_factory=list)
    crypto_findings: list[dict[str, Any]] = field(default_factory=list)
    archive_findings: list[dict[str, Any]] = field(default_factory=list)
    service_status: str | None = None
    recommended_vectors: list[str] = field(default_factory=list)
    raw_summary: str = ""

    def to_markdown(self) -> str:
        """Format the security audit result into a clean, actionable Markdown dossier."""
        lines: list[str] = [
            f"# 🛡️ Automated Security Reconnaissance Dossier — `{self.target_path}`",
            "",
        ]

        if self.discovered_flags:
            lines.append("## 🚩 DISCOVERED FLAG CANDIDATES (AUTOMATED TRIAGE)")
            for fl in self.discovered_flags:
                lines.append(f"- **`{fl}`**")
            lines.append("")

        if self.service_status:
            lines.append("## 🌐 Service Connectivity")
            lines.append(self.service_status)
            lines.append("")

        if self.file_profiles:
            lines.append("## 📁 File Inventory & Magic Byte Analysis")
            for fp in self.file_profiles:
                fname = fp.get("filename", "unknown")
                ftype = fp.get("file_type", "unknown")
                size = fp.get("size", "0 B")
                disguised = fp.get("is_disguised", False)
                disguise_tag = " ⚠️ [DISGUISED FILE]" if disguised else ""
                lines.append(f"- **`{fname}`** ({size}){disguise_tag}: `{ftype}`")
                if fp.get("notes"):
                    lines.append(f"  - Notes: {fp['notes']}")
            lines.append("")

        if self.binary_audits:
            lines.append("## ⚙️ Binary Security Mitigation Audits (checksec)")
            for b in self.binary_audits:
                lines.append(f"### Binary: `{b.get('filename')}`")
                lines.append(f"```text\n{b.get('checksec', 'N/A')}\n```")
                if b.get("mitigations"):
                    m = b["mitigations"]
                    lines.append(
                        f"- RELRO: `{m.get('relro')}`, Canary: `{m.get('canary')}`, "
                        f"NX: `{m.get('nx')}`, PIE: `{m.get('pie')}`"
                    )
            lines.append("")

        if self.crypto_findings:
            lines.append("## 🔑 Cryptographic & Token Findings")
            for c in self.crypto_findings:
                lines.append(f"### {c.get('type', 'Crypto Finding')} (`{c.get('source', '')}`)")
                lines.append(c.get("details", ""))
            lines.append("")

        if self.archive_findings:
            lines.append("## 📦 Archive Inspections")
            for a in self.archive_findings:
                lines.append(f"- Extracted `{a.get('archive')}` -> `{a.get('dest_dir')}`")
                if a.get("flags"):
                    lines.append(f"  - Discovered Flags: {', '.join(a['flags'])}")
            lines.append("")

        if self.recommended_vectors:
            lines.append("## 🎯 Recommended Attack & Solver Vectors")
            for rec in self.recommended_vectors:
                lines.append(f"- {rec}")
            lines.append("")

        return "\n".join(lines)


async def do_auto_security_scan(
    sandbox: Any,
    target_path: str = "/challenge/distfiles",
    connection_info: str = "",
) -> SecurityAuditResult:
    """Run an end-to-end automated security audit and reconnaissance scan on distfiles and targets."""
    result = SecurityAuditResult(target_path=target_path)

    # 1. Inspect directory or target path
    safe_path = shlex.quote(target_path)
    list_cmd = (
        f"if [ -d {safe_path} ]; then "
        f"  find {safe_path} -maxdepth 2 -type f; "
        f"elif [ -f {safe_path} ]; then "
        f"  echo {safe_path}; "
        f"else "
        f"  echo ''; "
        f"fi"
    )
    exec_res = await sandbox.exec(list_cmd, timeout_s=15)
    files = [f.strip() for f in exec_res.stdout.splitlines() if f.strip()]

    # If target_path was relative or container path had no files, also check distfiles
    if not files and target_path != "/challenge/distfiles":
        exec_res2 = await sandbox.exec("find /challenge/distfiles -maxdepth 2 -type f 2>/dev/null", timeout_s=10)
        files = [f.strip() for f in exec_res2.stdout.splitlines() if f.strip()]

    # 2. Network Service Audit
    if connection_info:
        conn = connection_info.strip()
        result.service_status = f"Target Connection: `{conn}`\n"
        # Test HTTP or Netcat
        if re.match(r"^https?://", conn):
            test_http = await sandbox.exec(f"curl -sI -m 5 {shlex.quote(conn)} | head -n 10", timeout_s=10)
            if test_http.stdout:
                result.service_status += f"HTTP Response:\n```text\n{test_http.stdout.strip()}\n```"
                for fl in extract_flag_candidates(test_http.stdout):
                    result.discovered_flags.append(fl)
            else:
                result.service_status += "HTTP endpoint did not respond to HEAD request."
        elif conn.startswith("nc "):
            parts = conn.split()
            if len(parts) >= 3:
                host, port = parts[1], parts[2]
                test_nc = await sandbox.exec(f"nc -zv -w 3 {shlex.quote(host)} {shlex.quote(port)} 2>&1", timeout_s=10)
                result.service_status += f"Port Probe ({host}:{port}): {test_nc.stdout.strip() or test_nc.stderr.strip()}"

    # 3. Iterate through files and perform deep automated security inspection
    for file_path in files:
        fname = Path(file_path).name
        ext = Path(file_path).suffix.lower()

        # A. File info & magic bytes
        info_str = await do_file_info(sandbox, file_path)
        lines = [line.strip() for line in info_str.splitlines() if line.strip()]
        file_desc = lines[1] if len(lines) > 1 else "Unknown"
        mime_type = lines[2] if len(lines) > 2 else ""

        # Disguise detection (e.g. extension says .png but magic says ASCII text)
        is_disguised = False
        notes = ""
        if ext in [".png", ".jpg", ".jpeg", ".gif"] and ("ASCII" in file_desc or "text" in mime_type):
            is_disguised = True
            notes = "Image extension but contents are ASCII text! Potential forensics disguise."
            result.recommended_vectors.append(f"Forensics Disguise: `{fname}` is actually ASCII text — inspect directly with `cat` or `read_file`.")
        elif ext in [".png", ".jpg", ".pdf"] and "Zip" in file_desc:
            is_disguised = True
            notes = "File contains appended ZIP archive (Polyglot / Stego)."
            result.recommended_vectors.append(f"Polyglot Archive: `{fname}` contains a ZIP archive — extract with `extract_archive` or `binwalk`.")

        result.file_profiles.append({
            "path": file_path,
            "filename": fname,
            "file_type": file_desc,
            "mime_type": mime_type,
            "is_disguised": is_disguised,
            "notes": notes,
        })

        # B. Strings extraction & Flag candidate discovery
        strings_out = await do_strings_search(sandbox, file_path, min_len=4)
        for fl in extract_flag_candidates(strings_out):
            result.discovered_flags.append(fl)

        # C. Binary Checksec & Mitigation Audit
        if "ELF" in file_desc or "executable" in file_desc or ext in [".elf", ".bin", ""]:
            # Run checksec
            cs_out = await do_checksec(sandbox, file_path)
            mitigations: dict[str, str] = {}
            for line in cs_out.splitlines():
                line_l = line.lower()
                if "relro" in line_l:
                    mitigations["relro"] = "Full" if "full" in line_l else ("Partial" if "partial" in line_l else "No")
                if "canary" in line_l:
                    mitigations["canary"] = "Yes" if "found" in line_l and "no" not in line_l else "No"
                if "nx" in line_l:
                    mitigations["nx"] = "Enabled" if "enabled" in line_l else "Disabled"
                if "pie" in line_l:
                    mitigations["pie"] = "PIE enabled" if "pie enabled" in line_l else "No PIE"

            result.binary_audits.append({
                "filename": fname,
                "checksec": cs_out[:400],
                "mitigations": mitigations,
            })

            # Derive recommended attack vectors for binary
            if mitigations.get("canary") == "No" and mitigations.get("pie") == "No":
                result.recommended_vectors.append(
                    f"Binary Pwn Vector (`{fname}`): No Stack Canary + No PIE. Prime candidate for standard Buffer Overflow / Ret2Win / ROP!"
                )
            elif mitigations.get("canary") == "No" and mitigations.get("nx") == "Disabled":
                result.recommended_vectors.append(
                    f"Binary Pwn Vector (`{fname}`): NX Disabled + No Canary. Shellcode injection on stack is executable!"
                )
            elif mitigations.get("canary") == "Yes":
                result.recommended_vectors.append(
                    f"Binary Pwn Vector (`{fname}`): Stack Canary Present. Check for Format String (%p/%x) or Out-of-Bounds read to leak canary before overwriting RIP."
                )

        # D. Automated Archive Extraction
        if ext in [".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".7z"] or "Zip" in file_desc or "gzip" in file_desc:
            dest = f"/challenge/workspace/{fname}_unpacked"
            extract_out = await do_extract_archive(sandbox, file_path, dest_dir=dest)
            arch_flags = extract_flag_candidates(extract_out)
            for fl in arch_flags:
                result.discovered_flags.append(fl)
            result.archive_findings.append({
                "archive": fname,
                "dest_dir": dest,
                "flags": arch_flags,
                "summary": extract_out[:200],
            })

        # E. Text / Crypto / Token Analysis
        if "ASCII" in file_desc or "text" in mime_type or ext in [".txt", ".enc", ".jwt", ".b64", ".hex"]:
            cat_res = await sandbox.exec(f"head -c 2000 {shlex.quote(file_path)}", timeout_s=10)
            text_sample = cat_res.stdout.strip()
            if text_sample:
                # Check for direct flags
                for fl in extract_flag_candidates(text_sample):
                    result.discovered_flags.append(fl)

                # Check JWT
                if "eyJ" in text_sample and "." in text_sample:
                    jwt_res = do_jwt_decode(text_sample)
                    for fl in extract_flag_candidates(jwt_res):
                        result.discovered_flags.append(fl)
                    result.crypto_findings.append({
                        "type": "JWT Token Detected",
                        "source": fname,
                        "details": jwt_res[:400],
                    })
                    result.recommended_vectors.append(f"Crypto/Web Vector (`{fname}`): JWT token detected. Check signature algorithm and header parameters.")

                # Check auto cascade decoding
                dec_out = do_auto_decode(text_sample)
                if "FLAG(S) REVEALED" in dec_out:
                    for fl in extract_flag_candidates(dec_out):
                        result.discovered_flags.append(fl)
                    result.crypto_findings.append({
                        "type": "Cascade Encoding Flag Decoded",
                        "source": fname,
                        "details": dec_out[:300],
                    })
                elif any(m in dec_out for m in ["[base64]", "[hex]", "[rot13]"]):
                    result.crypto_findings.append({
                        "type": "Decoded Plaintext Patterns",
                        "source": fname,
                        "details": dec_out[:300],
                    })

                # Check ROT bruteforce
                rot_res = do_rot_bruteforce(text_sample)
                if "FLAG DETECTED" in rot_res:
                    for fl in extract_flag_candidates(rot_res):
                        result.discovered_flags.append(fl)
                    result.crypto_findings.append({
                        "type": "Caesar / ROT Shift Flag Decoded",
                        "source": fname,
                        "details": rot_res[:300],
                    })

                # Check suspected hash
                if len(text_sample) in [32, 40, 64] and all(c in "0123456789abcdefABCDEF" for c in text_sample):
                    hash_id = do_identify_hash(text_sample)
                    result.crypto_findings.append({
                        "type": "Cryptographic Hash Identified",
                        "source": fname,
                        "details": hash_id,
                    })
                    result.recommended_vectors.append(f"Crypto Vector (`{fname}`): Suspected hash. Crack with hashcat or John the Ripper.")

    # Deduplicate discovered flags
    result.discovered_flags = list(dict.fromkeys(result.discovered_flags))
    result.raw_summary = result.to_markdown()
    return result
