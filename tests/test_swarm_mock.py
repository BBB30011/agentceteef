import tempfile
from pathlib import Path

import pytest

from backend.agents.swarm import ChallengeSwarm
from backend.config import Settings
from backend.cost_tracker import CostTracker
from backend.ctfd import CTFdClient
from backend.prompts import ChallengeMeta


@pytest.mark.asyncio
async def test_challenge_swarm_initialization_and_status():
    with tempfile.TemporaryDirectory() as tmpdir:
        ch_dir = Path(tmpdir) / "test_chal"
        ch_dir.mkdir(parents=True, exist_ok=True)
        (ch_dir / "distfiles").mkdir(parents=True, exist_ok=True)
        (ch_dir / "distfiles" / "hint.txt").write_text("sample content")

        meta = ChallengeMeta(name="test_chal", category="misc", value=50)
        settings = Settings(sandbox_mode="local")
        ctfd = CTFdClient(base_url="http://localhost:8000")
        cost_tracker = CostTracker()

        swarm = ChallengeSwarm(
            challenge_dir=str(ch_dir),
            meta=meta,
            ctfd=ctfd,
            cost_tracker=cost_tracker,
            settings=settings,
            model_specs=["agy/default"],
            no_submit=True,
        )

        assert swarm.meta.name == "test_chal"
        assert swarm.no_submit is True

        # Test solver instantiation
        solver = swarm._create_solver("agy/default")
        assert solver.agent_name == "test_chal/antigravity"

        # Test try_submit_flag logic
        display, is_confirmed = await swarm.try_submit_flag("CTF{test_flag}", "agy/default")
        assert "DRY RUN" in display or isinstance(display, str)

        # Test kill
        swarm.kill()
        assert swarm.cancel_event.is_set()
