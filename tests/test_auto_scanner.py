"""Tests for automated security reconnaissance and vulnerability auditing engine."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.sandbox import LocalSandbox
from backend.tools.auto_scanner import SecurityAuditResult, do_auto_security_scan


def test_security_audit_result_markdown():
    res = SecurityAuditResult(
        target_path="/challenge/distfiles",
        discovered_flags=["flag{auto_audit_success_1337}"],
        file_profiles=[{
            "filename": "vuln_service",
            "file_type": "ELF 64-bit LSB pie executable",
            "size": "16 KB",
            "is_disguised": False,
            "notes": "",
        }],
        binary_audits=[{
            "filename": "vuln_service",
            "checksec": "RELRO: Partial RELRO\nStack: No canary found\nNX: NX enabled\nPIE: No PIE",
            "mitigations": {"relro": "Partial", "canary": "No", "nx": "Enabled", "pie": "No PIE"},
        }],
        recommended_vectors=["Ret2Win: No Canary + No PIE"],
    )
    md = res.to_markdown()
    assert "flag{auto_audit_success_1337}" in md
    assert "vuln_service" in md
    assert "RELRO: Partial" in md
    assert "Ret2Win" in md


@pytest.mark.asyncio
async def test_do_auto_security_scan_demo_sanity():
    sandbox = LocalSandbox(image="local", challenge_dir="challenges/demo_sanity")
    await sandbox.start()
    try:
        audit = await do_auto_security_scan(sandbox, "challenges/demo_sanity/distfiles")
        assert len(audit.discovered_flags) > 0
        assert "flag{ctf_agent_foundation_is_solid_and_verified}" in audit.discovered_flags
        assert any("readme.txt" in fp["filename"] for fp in audit.file_profiles)
    finally:
        await sandbox.stop()


@pytest.mark.asyncio
async def test_do_auto_security_scan_forensics_disguise():
    sandbox = LocalSandbox(image="local", challenge_dir="challenges/forensics_disguise")
    await sandbox.start()
    try:
        audit = await do_auto_security_scan(sandbox, "challenges/forensics_disguise/distfiles")
        assert len(audit.discovered_flags) > 0
        assert "flag{file_inspection_and_strings_reveal_all_secrets}" in audit.discovered_flags
        # Verify disguise detected
        disguised = [fp for fp in audit.file_profiles if fp.get("is_disguised")]
        assert len(disguised) > 0
        assert disguised[0]["filename"] == "avatar.png"
    finally:
        await sandbox.stop()


@pytest.mark.asyncio
async def test_do_auto_security_scan_with_mock_service():
    sandbox = MagicMock()
    # Mock find, file info, strings search, curl
    find_res = MagicMock(stdout="", stderr="", exit_code=0)
    curl_res = MagicMock(stdout="HTTP/1.1 200 OK\nX-Flag: flag{http_header_secret_leak}\n", stderr="", exit_code=0)
    sandbox.exec = AsyncMock(side_effect=[find_res, curl_res])

    audit = await do_auto_security_scan(sandbox, "/challenge/distfiles", connection_info="http://challenge.local:8080")
    assert "http://challenge.local:8080" in audit.service_status
    assert "flag{http_header_secret_leak}" in audit.discovered_flags
