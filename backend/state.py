"""Persistent SQLite state store for CTF competitions — tracking challenges, solved status, flags, and costs."""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class StateManager:
    """Thread-safe SQLite state manager for competition persistence and resuming."""

    def __init__(self, db_path: str = "ctf_state.sqlite3") -> None:
        self.db_path = str(Path(db_path).resolve())
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._get_conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS challenges (
                    name TEXT PRIMARY KEY,
                    category TEXT,
                    points INTEGER,
                    status TEXT DEFAULT 'discovered',
                    flag TEXT,
                    winner_model TEXT,
                    solve_time REAL,
                    updated_at REAL
                );

                CREATE TABLE IF NOT EXISTS submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    challenge_name TEXT,
                    flag TEXT,
                    status TEXT,
                    response TEXT,
                    model_spec TEXT,
                    timestamp REAL
                );

                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT,
                    details TEXT,
                    timestamp REAL
                );
                """
            )
            conn.commit()

    def record_discovered(self, name: str, category: str = "", points: int = 0) -> None:
        """Record a discovered challenge from CTFd or directory."""
        now = time.time()
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO challenges (name, category, points, status, updated_at)
                VALUES (?, ?, ?, 'discovered', ?)
                ON CONFLICT(name) DO UPDATE SET
                    category=excluded.category,
                    points=excluded.points
                WHERE challenges.status = 'discovered';
                """,
                (name, category, points, now),
            )
            conn.commit()

    def mark_in_progress(self, name: str) -> None:
        """Mark a challenge as currently being attacked by a swarm."""
        now = time.time()
        with self._get_conn() as conn:
            conn.execute(
                """
                UPDATE challenges SET status='in_progress', updated_at=?
                WHERE name=? AND status != 'solved';
                """,
                (now, name),
            )
            conn.commit()

    def mark_solved(
        self,
        name: str,
        flag: str,
        winner_model: str,
        solve_time: float = 0.0,
    ) -> None:
        """Mark a challenge as successfully solved with its confirmed flag."""
        now = time.time()
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO challenges (name, status, flag, winner_model, solve_time, updated_at)
                VALUES (?, 'solved', ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    status='solved',
                    flag=excluded.flag,
                    winner_model=excluded.winner_model,
                    solve_time=excluded.solve_time,
                    updated_at=excluded.updated_at;
                """,
                (name, flag, winner_model, solve_time, now),
            )
            conn.commit()
        logger.info("STATE: Marked %s as SOLVED (winner: %s, flag: %s)", name, winner_model, flag)

    def record_submission(
        self,
        challenge_name: str,
        flag: str,
        status: str,
        response: str,
        model_spec: str,
    ) -> None:
        """Log a flag submission attempt."""
        now = time.time()
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO submissions (challenge_name, flag, status, response, model_spec, timestamp)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (challenge_name, flag, status, response, model_spec, now),
            )
            conn.commit()

    def get_solved_names(self) -> set[str]:
        """Return the set of challenge names recorded as solved."""
        with self._get_conn() as conn:
            rows = conn.execute("SELECT name FROM challenges WHERE status='solved'").fetchall()
            return {r["name"] for r in rows}

    def get_all_challenges(self) -> list[dict[str, Any]]:
        """Return list of all tracked challenges."""
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM challenges ORDER BY points ASC, name ASC").fetchall()
            return [dict(r) for r in rows]

    def export_summary(self) -> dict[str, Any]:
        """Export comprehensive summary statistics."""
        with self._get_conn() as conn:
            total = conn.execute("SELECT COUNT(*) as c FROM challenges").fetchone()["c"]
            solved = conn.execute("SELECT COUNT(*) as c FROM challenges WHERE status='solved'").fetchone()["c"]
            points = conn.execute("SELECT SUM(points) as s FROM challenges WHERE status='solved'").fetchone()["s"] or 0
            submissions = conn.execute("SELECT COUNT(*) as c FROM submissions").fetchone()["c"]
            solves_list = [dict(r) for r in conn.execute("SELECT * FROM challenges WHERE status='solved'").fetchall()]

        return {
            "total_challenges": total,
            "solved_challenges": solved,
            "total_points": points,
            "total_submissions": submissions,
            "solves": solves_list,
        }

    def generate_markdown_report(self) -> str:
        """Format a clean markdown report of competition achievements."""
        summary = self.export_summary()
        lines = [
            "# CTF Agent — Competition Report",
            "",
            f"**Total Solved:** {summary['solved_challenges']} / {summary['total_challenges']}",
            f"**Total Points Earned:** {summary['total_points']}",
            f"**Total Flag Submissions:** {summary['total_submissions']}",
            "",
            "## Solved Challenges",
            "| Challenge | Category | Points | Winner Model | Flag |",
            "|-----------|----------|:------:|--------------|------|",
        ]
        for s in summary["solves"]:
            lines.append(
                f"| {s['name']} | {s.get('category') or '-'} | {s.get('points') or 0} | {s.get('winner_model') or '-'} | `{s.get('flag') or ''}` |"
            )
        lines.append("")
        return "\n".join(lines)
