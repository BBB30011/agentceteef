import tempfile
from pathlib import Path

from backend.state import StateManager


def test_state_manager_workflow():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test_state.sqlite3")
        mgr = StateManager(db_path)

        # Record discovery
        mgr.record_discovered("crypto_warmup", "crypto", 50)
        mgr.record_discovered("pwn_baby", "pwn", 100)

        # Mark in progress
        mgr.mark_in_progress("crypto_warmup")

        # Record submissions
        mgr.record_submission("crypto_warmup", "flag{wrong}", "incorrect", "Try again", "model-a")
        mgr.record_submission("crypto_warmup", "flag{correct}", "correct", "Solved!", "model-b")

        # Mark solved
        mgr.mark_solved("crypto_warmup", "flag{correct}", "model-b", solve_time=12.5)

        solved = mgr.get_solved_names()
        assert "crypto_warmup" in solved
        assert "pwn_baby" not in solved

        summary = mgr.export_summary()
        assert summary["solved_challenges"] == 1
        assert summary["total_points"] == 50

        report = mgr.generate_markdown_report()
        assert "crypto_warmup" in report
        assert "flag{correct}" in report
