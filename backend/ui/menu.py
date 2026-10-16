"""Interactive terminal menu for CTF Agent — Zero learning curve launcher."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt

from backend.config import Settings
from backend.state import StateManager
from backend.ui.dashboard import print_welcome_banner
from backend.ui.exporter import export_report_to_file

console = Console()


def scan_available_challenges(challenges_dir: str = "challenges") -> list[Path]:
    """Scan directory for available challenges containing metadata.yml."""
    found: list[Path] = []
    base = Path(challenges_dir)
    if base.exists():
        for item in base.iterdir():
            if item.is_dir() and (item / "metadata.yml").exists():
                found.append(item)

    fixtures = Path("tests/fixtures")
    if fixtures.exists():
        for item in fixtures.iterdir():
            if item.is_dir() and (item / "metadata.yml").exists():
                found.append(item)

    return sorted(found, key=lambda p: p.name)


def run_interactive_menu(settings: Settings) -> dict[str, str | list[str] | bool | int]:
    """Display interactive CLI wizard and return selected arguments."""
    print_welcome_banner(
        ctfd_url=settings.ctfd_url,
        models=["[dim]Pilih lewat menu[/dim]"],
        sandbox_mode=settings.sandbox_mode,
        coordinator="Universal",
        max_concurrency=settings.max_concurrent_challenges,
        db_path=settings.state_db_path,
    )

    console.print("\n[bold cyan]Silakan pilih mode operasi yang Anda inginkan:[/bold cyan]")
    console.print("  [bold green]1.[/bold green] 🚀 [bold]Mode Tanpa Token (Antigravity CLI / Local)[/bold] — $0 token cost, offline-ready")
    console.print("  [bold green]2.[/bold green] ⚡ [bold]Swarm Cepat (Fast Swarm)[/bold] — Latensi rendah & throughput tinggi")
    console.print("  [bold green]3.[/bold green] 🧠 [bold]Swarm Cerdas (Smart / Deep Swarm)[/bold] — Gemini 2.5 Pro / GPT-4o / Claude")
    console.print("  [bold green]4.[/bold green] 🎯 [bold]Pecahkan 1 Tantangan Spesifik[/bold] — Pilih tantangan tertentu")
    console.print("  [bold green]5.[/bold green] 📊 [bold]Lihat Laporan & Ekspor HTML[/bold] — Statistik kompetisi")
    console.print("  [bold red]0.[/bold red] 🚪 Keluar\n")

    choice = IntPrompt.ask("[bold yellow]Pilihan Anda[/bold yellow]", choices=["0", "1", "2", "3", "4", "5"], default=1)

    if choice == 0:
        console.print("[dim]Keluar dari CTF Agent.[/dim]")
        raise SystemExit(0)

    if choice == 5:
        state_mgr = StateManager(settings.state_db_path)
        console.print(Panel(state_mgr.generate_markdown_report(), title="Laporan Kompetisi", border_style="cyan"))
        out = export_report_to_file(state_mgr, "ctf_report.html")
        console.print(f"[bold green]✓ Laporan HTML berhasil diekspor ke:[/bold green] [underline]{out}[/underline]\n")
        raise SystemExit(0)

    if choice == 1:
        # Tokenless agy profile
        return {
            "profile": "tokenless",
            "models": ["agy/default"],
            "sandbox_mode": "local",
            "coordinator": "universal",
            "coordinator_model": "agy/default",
        }

    if choice == 2:
        # Fast profile
        return {
            "profile": "fast",
            "models": ["google/gemini-2.0-flash", "groq/llama-3.3-70b-versatile"],
            "sandbox_mode": "auto",
            "coordinator": "universal",
            "coordinator_model": "google/gemini-2.0-flash",
        }

    if choice == 3:
        # Smart profile
        return {
            "profile": "smart",
            "models": ["google/gemini-2.5-pro", "openai/gpt-4o", "anthropic/claude-3-7-sonnet-latest"],
            "sandbox_mode": "auto",
            "coordinator": "universal",
            "coordinator_model": "google/gemini-2.5-pro",
        }

    if choice == 4:
        # Single challenge picker
        challenges = scan_available_challenges()
        selected_path = ""
        if challenges:
            console.print("\n[bold]Tantangan yang ditemukan di direktori lokal:[/bold]")
            for idx, ch in enumerate(challenges, 1):
                console.print(f"  [{idx}] {ch.name} ([dim]{ch}[/dim])")
            ch_choice = Prompt.ask(
                "\nPilih nomor tantangan atau masukkan path manual",
                default="1",
            )
            if ch_choice.isdigit() and 1 <= int(ch_choice) <= len(challenges):
                selected_path = str(challenges[int(ch_choice) - 1])
            else:
                selected_path = ch_choice
        else:
            selected_path = Prompt.ask("Masukkan path ke folder tantangan", default="challenges/demo_sanity")

        solver_mode = Prompt.ask(
            "Gunakan model apa?",
            choices=["agy/default", "auto", "gemini", "gpt-4o", "claude"],
            default="agy/default",
        )
        model_spec = [solver_mode] if solver_mode != "auto" else []
        return {
            "challenge": selected_path,
            "models": model_spec,
            "sandbox_mode": "local" if solver_mode == "agy/default" else "auto",
        }

    return {}
