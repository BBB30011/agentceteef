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
