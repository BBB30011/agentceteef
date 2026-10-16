"""Report exporter — Generate Markdown and standalone Dark Mode HTML reports."""

from __future__ import annotations

import html
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.state import StateManager


def generate_html_report(state: StateManager) -> str:
    """Generate a responsive, standalone Dark Mode HTML competition report."""
    solved = state.get_solved()
    stats = state.export_summary()
    submissions = state.get_recent_submissions(limit=50)

    rows_solved = ""
    for s in solved:
        name = html.escape(s.get("name") or "")
        cat = html.escape(s.get("category") or "misc")
        val = s.get("points") or s.get("value") or 0
        flag = html.escape(s.get("flag") or "")
        model = html.escape(s.get("winner_model") or "unknown")
        dur = s.get("solve_time") or s.get("solve_time_s") or 0.0
        dur_str = f"{dur:.1f}s" if dur else "-"

        rows_solved += f"""
        <tr>
            <td class="bold">{name}</td>
            <td><span class="badge badge-{cat.lower()}">{cat.upper()}</span></td>
            <td class="center text-green">+{val}</td>
            <td class="mono">{flag}</td>
            <td class="text-cyan">{model}</td>
            <td class="center">{dur_str}</td>
        </tr>
        """

    if not rows_solved:
        rows_solved = "<tr><td colspan='6' class='center text-muted'>Belum ada tantangan yang terselesaikan</td></tr>"

    rows_subs = ""
    for sub in submissions:
        ch = html.escape(sub.get("challenge_name") or "")
        flag_val = html.escape(sub.get("flag") or "")
        st = sub.get("status") or ""
        st_badge = "<span class='badge badge-success'>CORRECT</span>" if st == "correct" else "<span class='badge badge-danger'>INCORRECT</span>"
        model_sub = html.escape(sub.get("model_spec") or "")
        ts = time.strftime("%H:%M:%S", time.localtime(sub.get("timestamp") or sub.get("submitted_at") or 0))

        rows_subs += f"""
        <tr>
            <td>{ts}</td>
            <td class="bold">{ch}</td>
            <td class="mono">{flag_val}</td>
            <td class="center">{st_badge}</td>
            <td class="text-cyan">{model_sub}</td>
        </tr>
        """

    if not rows_subs:
        rows_subs = "<tr><td colspan='5' class='center text-muted'>Belum ada rekaman submisi flag</td></tr>"

    return f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CTF Agent — Laporan Kompetisi</title>
    <style>
        :root {{
            --bg-dark: #0d1117;
            --card-bg: #161b22;
            --border-color: #30363d;
            --text-main: #c9d1d9;
            --text-muted: #8b949e;
            --accent-green: #2ea043;
            --accent-cyan: #58a6ff;
            --accent-yellow: #f0883e;
            --accent-red: #f85149;
            --accent-purple: #bc8cff;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-main);
            margin: 0;
            padding: 2rem;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        header {{
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 1.5rem;
            margin-bottom: 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        h1 {{
            margin: 0;
            color: #fff;
            font-size: 1.8rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.2rem;
            margin-bottom: 2rem;
        }}
        .metric-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.2rem;
            text-align: center;
        }}
        .metric-value {{
            font-size: 2.2rem;
            font-weight: bold;
            color: #fff;
            margin: 0.4rem 0;
        }}
        .metric-label {{
            color: var(--text-muted);
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }}
        .card-title {{
            margin-top: 0;
            font-size: 1.25rem;
            color: #fff;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.75rem;
            margin-bottom: 1rem;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.95rem;
        }}
        th, td {{
            padding: 10px 14px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}
        th {{
            color: var(--text-muted);
            font-weight: 600;
        }}
        .center {{ text-align: center; }}
        .mono {{ font-family: ui-monospace, SFMono-Regular, Consolas, monospace; color: var(--accent-yellow); }}
        .bold {{ font-weight: 600; color: #fff; }}
        .text-green {{ color: var(--accent-green); font-weight: bold; }}
        .text-cyan {{ color: var(--accent-cyan); }}
        .text-muted {{ color: var(--text-muted); }}
        .badge {{
            display: inline-block;
            padding: 2px 8px;
            font-size: 0.75rem;
            font-weight: bold;
            border-radius: 12px;
            text-transform: uppercase;
        }}
        .badge-pwn {{ background: #da3633; color: #fff; }}
        .badge-rev {{ background: #8957e5; color: #fff; }}
        .badge-crypto {{ background: #d29922; color: #000; }}
        .badge-web {{ background: #1f6feb; color: #fff; }}
        .badge-misc {{ background: #238636; color: #fff; }}
        .badge-success {{ background: var(--accent-green); color: #fff; }}
        .badge-danger {{ background: var(--accent-red); color: #fff; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>🏆 CTF Agent — Laporan Kompetisi</h1>
                <p style="color: var(--text-muted); margin: 5px 0 0 0;">Autonomous Security Solver Swarm Report</p>
            </div>
            <div style="color: var(--text-muted); font-size: 0.9rem;">
                Digenerate: {time.strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </header>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Total Solved</div>
                <div class="metric-value text-green">{stats.get('solved_challenges', 0)} / {stats.get('total_challenges', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total Points</div>
                <div class="metric-value text-cyan">{stats.get('total_points', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Flag Submissions</div>
                <div class="metric-value">{stats.get('total_submissions', 0)}</div>
            </div>
        </div>

        <div class="card">
            <h2 class="card-title">🚩 Tantangan Berhasil Terpecahkan (Solved)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Tantangan</th>
                        <th>Kategori</th>
                        <th class="center">Poin</th>
                        <th>Flag Ditemukan</th>
                        <th>Model Pemenang</th>
                        <th class="center">Durasi</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_solved}
                </tbody>
            </table>
        </div>

        <div class="card">
            <h2 class="card-title">📜 Riwayat Submisi Flag Terakhir</h2>
            <table>
                <thead>
                    <tr>
                        <th>Waktu</th>
                        <th>Tantangan</th>
                        <th>Flag yang Dicoba</th>
                        <th class="center">Status</th>
                        <th>Model Pengirim</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_subs}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""


def export_report_to_file(state: StateManager, output_path: str = "ctf_report.html") -> str:
    """Export the HTML report to disk and return path."""
    html_content = generate_html_report(state)
    Path(output_path).write_text(html_content, encoding="utf-8")
    return str(Path(output_path).resolve())
