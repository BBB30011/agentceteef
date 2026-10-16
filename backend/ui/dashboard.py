"""Rich UI dashboard and visual presentation components for CTF Agent."""

from __future__ import annotations

from typing import Any

from rich.align import Align
from rich.box import DOUBLE, HEAVY, ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

CATEGORY_STYLES = {
    "pwn": "bold white on red",
    "rev": "bold white on magenta",
    "reverse": "bold white on magenta",
    "crypto": "bold black on yellow",
    "web": "bold white on blue",
    "forensics": "bold white on cyan",
    "misc": "bold black on green",
    "osint": "bold white on dark_green",
}


def format_category_badge(category: str) -> str:
    """Format category with a high-visibility badge."""
    cat_clean = (category or "misc").lower().strip()
    style = CATEGORY_STYLES.get(cat_clean, "bold white on blue")
    return f"[{style}] {cat_clean.upper():^8} [/]"


def print_welcome_banner(
    ctfd_url: str,
    models: list[str],
    sandbox_mode: str,
    coordinator: str,
    max_concurrency: int,
    db_path: str,
    profile_name: str | None = None,
) -> None:
    """Print an eye-catching terminal header for the CTF swarm session."""
    title_text = Text()
    title_text.append("⚡ CTF AGENT SWARM — AUTONOMOUS SECURITY SOLVER ⚡\n", style="bold yellow")
    title_text.append("Autonomous Multi-Model Reasoning Engine • Real-Time Flag Extraction", style="dim italic")

    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_column("Key", style="bold cyan")
    info_table.add_column("Value", style="bold white")

    if profile_name:
        info_table.add_row("🚀 Active Profile:", f"[bold green]{profile_name.upper()}[/bold green]")
    info_table.add_row("🎯 CTFd Target:", ctfd_url or "[italic dim]Offline / Local only[/italic dim]")
    info_table.add_row("🤖 Active Solver Swarm:", ", ".join(models) if models else "[red]None (auto)[/red]")
    info_table.add_row("🛡️ Sandbox Engine:", f"{sandbox_mode.upper()} Isolation")
    info_table.add_row("🧠 Swarm Coordinator:", f"{coordinator.upper()}")
    info_table.add_row("⚡ Max Concurrency:", f"{max_concurrency} parallel challenge swarms")
    info_table.add_row("💾 Persistent State:", db_path)

    panel = Panel(
        Align.center(info_table),
        title=title_text,
        border_style="bright_blue",
        box=ROUNDED,
        padding=(1, 2),
    )
    console.print(panel)


def print_flag_captured_banner(
    challenge_name: str,
    flag: str,
    winner_model: str,
    elapsed_s: float,
    category: str = "",
    points: int = 0,
) -> None:
    """Display celebration panel when a CTF flag is confirmed."""
    grid = Table.grid(padding=(0, 1))
    grid.add_column(style="bold yellow", justify="right")
    grid.add_column(style="bold white")

    cat_badge = format_category_badge(category)
    grid.add_row("🏁 Challenge:", f"{cat_badge} [bold white]{challenge_name}[/bold white]")
    grid.add_row("🚩 Captured Flag:", f"[bold yellow on black]  {flag}  [/bold yellow on black]")
    grid.add_row("🏆 Solved By:", f"[bold cyan]{winner_model}[/bold cyan]")
    grid.add_row("⏱️ Solve Duration:", f"[bold green]{elapsed_s:.1f}s[/bold green]")
    if points > 0:
        grid.add_row("⭐ Points Earned:", f"[bold green]+{points} pts[/bold green]")

    panel = Panel(
        Align.center(grid),
        title="[bold green]🎉🎉 FLAG CAPTURED & CONFIRMED! 🎉🎉[/bold green]",
        border_style="green",
        box=DOUBLE,
        padding=(1, 2),
    )
    console.print()
    console.print(panel)
    console.print()


def print_challenge_unsolved_banner(challenge_name: str, elapsed_s: float) -> None:
    """Display unsolved challenge banner."""
    content = f"[bold red]❌ Challenge '{challenge_name}' remaining unsolved after {elapsed_s:.1f}s.[/bold red]\n[dim]Insights recorded to state DB for review and retry.[/dim]"
    panel = Panel(
        Align.center(content),
        title="[bold red]Challenge Finished (Unsolved)[/bold red]",
        border_style="red",
        box=ROUNDED,
    )
    console.print()
    console.print(panel)
    console.print()


def render_live_swarm_table(swarms_status: dict[str, Any]) -> Table:
    """Generate dynamic status table for active swarms."""
    table = Table(box=HEAVY, border_style="cyan", show_lines=True)
    table.add_column("Challenge", style="bold white", width=22)
    table.add_column("Category", justify="center", width=12)
    table.add_column("Active Agents", style="cyan", width=24)
    table.add_column("Latest Insight / Activity", style="dim", overflow="ellipsis")
    table.add_column("Status", justify="center", width=14)

    for ch_name, data in swarms_status.items():
        cat = data.get("category", "misc")
        cat_badge = format_category_badge(cat)
        agents = ", ".join(data.get("agents", {}).keys())
        latest_act = data.get("latest_activity", "Analyzing challenge...")
        status = data.get("status", "running")

        if status == "solved":
            status_text = "[bold green]SOLVED 🚩[/bold green]"
        elif status == "failed":
            status_text = "[bold red]FAILED ❌[/bold red]"
        else:
            status_text = "[bold yellow]ATTACKING ⚡[/bold yellow]"

        table.add_row(ch_name, cat_badge, agents, latest_act[:50], status_text)

    return table
