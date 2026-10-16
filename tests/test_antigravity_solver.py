import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from backend.agents.antigravity_solver import AntigravitySolver
from backend.prompts import ChallengeMeta
from backend.sandbox import LocalSandbox
from backend.solver_base import FLAG_FOUND


@pytest.mark.asyncio
async def test_antigravity_solver_init_and_bump():
    with tempfile.TemporaryDirectory() as tmpdir:
        meta = ChallengeMeta(name="rev-warmup", category="rev", value=100)
        sandbox = LocalSandbox(image="local", challenge_dir=tmpdir)
        solver = AntigravitySolver(
            model_spec="agy/default",
            challenge_dir=tmpdir,
            meta=meta,
            sandbox=sandbox,
            no_submit=True,
        )
        await solver.start()
        assert solver.agent_name == "rev-warmup/antigravity"

        solver.bump("Try decompiling main with objdump")
        assert len(solver._bump_queue) == 1
        assert "objdump" in solver._bump_queue[0]

        await solver.stop()


@pytest.mark.asyncio
async def test_antigravity_solver_flag_detection():
    with tempfile.TemporaryDirectory() as tmpdir:
        meta = ChallengeMeta(name="crypto-warmup", category="crypto", value=50)
        sandbox = LocalSandbox(image="local", challenge_dir=tmpdir)
        await sandbox.start()

        fake_submit = AsyncMock(return_value=("CORRECT — flag accepted", True))

        solver = AntigravitySolver(
            model_spec="agy/default",
            challenge_dir=tmpdir,
            meta=meta,
            sandbox=sandbox,
            submit_fn=fake_submit,
        )

        # Mock asyncio.create_subprocess_exec to simulate agy finding a flag
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (
            b"Analyzing ciphertext...\nFlag found! FLAG: flag{agy_tokenless_ctf_win}\nDone.",
            b"",
        )

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            res = await solver.run_until_done_or_gave_up()

        assert res.status == FLAG_FOUND
        assert res.flag == "flag{agy_tokenless_ctf_win}"
        fake_submit.assert_awaited_once_with("flag{agy_tokenless_ctf_win}")

        await solver.stop()


@pytest.mark.asyncio
async def test_antigravity_solver_workspace_file_flag_detection():
    with tempfile.TemporaryDirectory() as tmpdir:
        meta = ChallengeMeta(name="pwn-easy", category="pwn", value=200)
        sandbox = LocalSandbox(image="local", challenge_dir=tmpdir)
        await sandbox.start()

        # Simulate exploit writing flag to /workspace/flag.txt
        workspace_dir = Path(sandbox.workspace_dir) / "workspace"
        workspace_dir.mkdir(parents=True, exist_ok=True)
        (workspace_dir / "flag.txt").write_text("CTF{buffer_overflow_pwnd_1337}\n")

        solver = AntigravitySolver(
            model_spec="agy/default",
            challenge_dir=tmpdir,
            meta=meta,
            sandbox=sandbox,
            no_submit=True,
        )

        # Mock agy CLI with generic output (not printing the flag directly)
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (
            b"Exploit finished successfully. Output written to disk.",
            b"",
        )

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            res = await solver.run_until_done_or_gave_up()

        assert res.status == FLAG_FOUND
        assert res.flag == "CTF{buffer_overflow_pwnd_1337}"

        await solver.stop()
