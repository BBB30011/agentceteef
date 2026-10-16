from pathlib import Path

import pytest

from backend.prompts import ChallengeMeta, list_distfiles
from backend.sandbox import LocalSandbox
from backend.tools.core import do_read_file
from backend.tools.ctf_helpers import do_find_flags_in_workspace, extract_flag_candidates


@pytest.mark.asyncio
async def test_demo_sanity_challenge_structure_and_flag_discovery():
    demo_dir = Path("tests/fixtures/demo_sanity")
    if not demo_dir.exists():
        demo_dir = Path("challenges/demo_sanity")
    assert demo_dir.exists()

    meta = ChallengeMeta.from_yaml(demo_dir / "metadata.yml")
    assert meta.name == "demo_sanity"
    assert meta.category == "misc"
    assert meta.value == 50

    distfiles = list_distfiles(str(demo_dir))
    assert "readme.txt" in distfiles

    sandbox = LocalSandbox(image="local", challenge_dir=str(demo_dir))
    await sandbox.start()

    try:
        # 1. Read distfile directly through sandbox abstraction
        content = await do_read_file(sandbox, "/challenge/distfiles/readme.txt")
        assert "flag{ctf_agent_foundation_is_solid_and_verified}" in content

        # 2. Automated flag pattern discovery across sandbox
        found_flags = await do_find_flags_in_workspace(sandbox, "/challenge")
        candidates = extract_flag_candidates(found_flags)
        assert "flag{ctf_agent_foundation_is_solid_and_verified}" in candidates

    finally:
        await sandbox.stop()


@pytest.mark.asyncio
async def test_crypto_cascade_challenge():
    cascade_dir = Path("challenges/crypto_cascade")
    assert cascade_dir.exists()

    meta = ChallengeMeta.from_yaml(cascade_dir / "metadata.yml")
    assert meta.name == "crypto_cascade"
    assert meta.category == "crypto"
    assert meta.value == 100

    sandbox = LocalSandbox(image="local", challenge_dir=str(cascade_dir))
    await sandbox.start()

    try:
        content = await do_read_file(sandbox, "/challenge/distfiles/intercepted.txt")
        assert "c3ludHtwbmZwbnFyX3poeWd2X3lubHJlX3FycGJxdmF0X3puZmdyZX0=" in content

        # Run auto_decode on intercepted ciphertext
        from backend.tools.ctf_helpers import do_auto_decode
        decode_result = do_auto_decode("c3ludHtwbmZwbnFyX3poeWd2X3lubHJlX3FycGJxdmF0X3puZmdyZX0=")
        assert "flag{cascade_multi_layer_decoding_master}" in decode_result
        assert "base64 -> rot13" in decode_result
    finally:
        await sandbox.stop()


@pytest.mark.asyncio
async def test_forensics_disguise_challenge():
    disguise_dir = Path("challenges/forensics_disguise")
    assert disguise_dir.exists()

    meta = ChallengeMeta.from_yaml(disguise_dir / "metadata.yml")
    assert meta.name == "forensics_disguise"
    assert meta.category == "forensics"

    sandbox = LocalSandbox(image="local", challenge_dir=str(disguise_dir))
    await sandbox.start()

    try:
        from backend.tools.ctf_helpers import do_file_info, do_strings_search
        # 1. file_info exposes that avatar.png is actually ASCII text
        info = await do_file_info(sandbox, "/challenge/distfiles/avatar.png")
        assert "ASCII" in info or "text" in info

        # 2. strings_search extracts the hidden flag
        strings_out = await do_strings_search(sandbox, "/challenge/distfiles/avatar.png", min_len=4)
        assert "flag{file_inspection_and_strings_reveal_all_secrets}" in strings_out
    finally:
        await sandbox.stop()


@pytest.mark.asyncio
async def test_rev_vault_challenge():
    rev_dir = Path("challenges/rev_vault")
    assert rev_dir.exists()

    meta = ChallengeMeta.from_yaml(rev_dir / "metadata.yml")
    assert meta.name == "rev_vault"
    assert meta.category == "rev"

    sandbox = LocalSandbox(image="local", challenge_dir=str(rev_dir))
    await sandbox.start()

    try:
        script = await do_read_file(sandbox, "/challenge/distfiles/vault.py")
        assert "expected =" in script

        # Run script with correct key
        key = "flag{rev_vault_unlocked}"
        res = await sandbox.exec(f"python3 /challenge/distfiles/vault.py << 'EOF'\n{key}\nEOF")
        assert "Vault unlocked!" in res.stdout
        assert key in res.stdout
    finally:
        await sandbox.stop()

