"""Rich Click CLI entry point for CTF Agent Swarm."""

from __future__ import annotations

import asyncio
import logging
import sys
import time
from pathlib import Path

import click
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel

from backend.config import Settings
from backend.models import auto_detect_default_models
from backend.state import StateManager
from backend.ui.dashboard import (
    print_challenge_unsolved_banner,
    print_flag_captured_banner,
    print_welcome_banner,
)
from backend.ui.exporter import export_report_to_file

console = Console()

PROFILES: dict[str, tuple[list[str], str]] = {
    "tokenless": (["agy/default"], "local"),
    "fast": (["google/gemini-2.0-flash", "groq/llama-3.3-70b-versatile"], "auto"),
    "smart": (["google/gemini-2.5-pro", "openai/gpt-4o", "anthropic/claude-3-7-sonnet-latest"], "auto"),
    "deep": (["google/gemini-2.5-pro", "openai/o3-mini", "anthropic/claude-3-7-sonnet-latest"], "auto"),
}


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("aiodocker").setLevel(logging.WARNING)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)-8s %(message)s", datefmt="%X"))
    logging.basicConfig(level=level, handlers=[handler], force=True)


@click.command()
@click.option("--profile", "-p", type=click.Choice(["tokenless", "fast", "smart", "deep", "auto"]), default=None, help="Execution preset profile")
@click.option("--interactive", "-i", is_flag=True, help="Launch interactive terminal launcher wizard")
@click.option("--ctfd-url", default=None, help="CTFd URL (overrides .env)")
@click.option("--ctfd-token", default=None, help="CTFd API token (overrides .env)")
@click.option("--image", default="ctf-sandbox", help="Docker sandbox image name")
@click.option("--sandbox-mode", default="auto", type=click.Choice(["docker", "local", "auto"]), help="Sandbox execution mode")
@click.option("--models", multiple=True, help="Model specs (default: auto-detected or configured)")
@click.option("--challenge", default=None, help="Solve a single challenge directory")
@click.option("--challenges-dir", default="challenges", help="Directory for challenge files")
@click.option("--no-submit", is_flag=True, help="Dry run — don't submit flags")
@click.option("--resume", is_flag=True, help="Skip challenges already marked as solved in state DB")
@click.option("--coordinator-model", default=None, help="Model for coordinator")
@click.option("--coordinator", default="auto", type=click.Choice(["auto", "universal", "claude", "codex"]), help="Coordinator backend")
@click.option("--max-challenges", default=10, type=int, help="Max challenges solved concurrently")
@click.option("--msg-port", default=0, type=int, help="Operator message port (0 = auto)")
@click.option("--report", is_flag=True, help="Print solve report from state DB and exit")
@click.option("--export-html", default=None, help="Export competition report to a standalone HTML file")
@click.option("-v", "--verbose", is_flag=True, help="Verbose logging")
def main(
    profile: str | None,
    interactive: bool,
    ctfd_url: str | None,
    ctfd_token: str | None,
    image: str,
    sandbox_mode: str,
    models: tuple[str, ...],
    challenge: str | None,
    challenges_dir: str,
    no_submit: bool,
    resume: bool,
    coordinator_model: str | None,
    coordinator: str,
    max_challenges: int,
    msg_port: int,
    report: bool,
    export_html: str | None,
    verbose: bool,
) -> None:
    """Agent CeTeEf — Autonomous Multi-Model Solver Swarm for CTF Competitions."""
    _setup_logging(verbose)

    settings = Settings(sandbox_image=image, sandbox_mode=sandbox_mode)
    if ctfd_url:
        settings.ctfd_url = ctfd_url
    if ctfd_token:
        settings.ctfd_token = ctfd_token
    settings.max_concurrent_challenges = max_challenges

    state_mgr = StateManager(settings.state_db_path)

    if export_html:
        out_path = export_report_to_file(state_mgr, export_html)
        console.print(f"[bold green]✓ Laporan HTML kompetisi berhasil diekspor ke:[/bold green] [underline]{out_path}[/underline]")
        return

    if report:
        console.print(Panel(state_mgr.generate_markdown_report(), title="CTF Competition Report", box=ROUNDED))
        return

    # Check interactive mode
    if interactive:
        from backend.ui.menu import run_interactive_menu
        opts = run_interactive_menu(settings)
        if "profile" in opts:
            profile = str(opts["profile"])
        if "challenge" in opts:
            challenge = str(opts["challenge"])
        if "models" in opts and opts["models"]:
            models = tuple(opts["models"])  # type: ignore[assignment]
        if "sandbox_mode" in opts:
            sandbox_mode = str(opts["sandbox_mode"])
            settings.sandbox_mode = sandbox_mode

    # Apply preset profile
    if profile and profile in PROFILES:
        prof_models, prof_sandbox = PROFILES[profile]
        if not models:
            models = tuple(prof_models)
        if sandbox_mode == "auto":
            sandbox_mode = prof_sandbox
            settings.sandbox_mode = prof_sandbox

    model_specs = list(models) if models else auto_detect_default_models(settings)

    print_welcome_banner(
        ctfd_url=settings.ctfd_url,
        models=model_specs,
        sandbox_mode=sandbox_mode,
        coordinator=coordinator,
        max_concurrency=max_challenges,
        db_path=settings.state_db_path,
        profile_name=profile,
    )

    if challenge:
        asyncio.run(_run_single(settings, challenge, model_specs, no_submit, max_challenges, resume, state_mgr))
    else:
        asyncio.run(
            _run_coordinator(
                settings,
                model_specs,
                challenges_dir,
                no_submit,
                coordinator_model,
                coordinator,
                max_challenges,
                msg_port,
                resume,
                state_mgr,
            )
        )


async def _run_single(
    settings: Settings,
    challenge_dir: str,
    model_specs: list[str],
    no_submit: bool,
    max_challenges: int,
    resume: bool,
    state_mgr: StateManager,
) -> None:
    """Run a single challenge with a solver swarm."""
    from backend.agents.swarm import ChallengeSwarm
    from backend.cost_tracker import CostTracker
    from backend.ctfd import CTFdClient
    from backend.prompts import ChallengeMeta
    from backend.sandbox import cleanup_orphan_containers, configure_semaphore

    meta_path = Path(challenge_dir) / "metadata.yml"
    meta = ChallengeMeta.from_yaml(meta_path) if meta_path.exists() else ChallengeMeta(name=Path(challenge_dir).name)

    state_mgr.record_discovered(meta.name, meta.category, meta.value)

    if resume and meta.name in state_mgr.get_solved_names():
        console.print(f"[yellow]Skipping already solved challenge '{meta.name}' (--resume)[/yellow]")
        return

    max_containers = max_challenges * len(model_specs)
    configure_semaphore(max_containers)
    await cleanup_orphan_containers()

    ctfd = CTFdClient(
        base_url=settings.ctfd_url,
        token=settings.ctfd_token,
        username=settings.ctfd_user,
        password=settings.ctfd_pass,
    )
    cost_tracker = CostTracker()

    state_mgr.mark_in_progress(meta.name)

    swarm = ChallengeSwarm(
        challenge_dir=challenge_dir,
        meta=meta,
        ctfd=ctfd,
        cost_tracker=cost_tracker,
        settings=settings,
        model_specs=model_specs,
        no_submit=no_submit,
    )

    console.print(f"[bold]Attacking {meta.name} with {len(model_specs)} models in parallel...[/bold]\n")
    start_time = time.time()
    try:
        result = await swarm.run()
        elapsed = time.time() - start_time
        console.print()
        if result and result.flag:
            winner = getattr(swarm.winner, "model_spec", "solver") if swarm.winner else "solver"
            state_mgr.mark_solved(meta.name, result.flag, winner, solve_time=elapsed)
            print_flag_captured_banner(
                challenge_name=meta.name,
                flag=result.flag,
                winner_model=winner,
                elapsed_s=elapsed,
                category=meta.category,
                points=meta.value,
            )
        else:
            print_challenge_unsolved_banner(meta.name, elapsed)

        console.print("\n[bold]Model Costs & Usage:[/bold]")
        for agent_name in cost_tracker.by_agent:
            console.print(f"  {agent_name}: {cost_tracker.format_usage(agent_name)}")
        console.print(f"  [bold]Total Swarm Cost: ${cost_tracker.total_cost_usd:.4f}[/bold]")
    finally:
        await ctfd.close()


async def _run_coordinator(
    settings: Settings,
    model_specs: list[str],
    challenges_dir: str,
    no_submit: bool,
    coordinator_model: str | None,
    coordinator_backend: str,
    max_challenges: int,
    msg_port: int,
    resume: bool,
    state_mgr: StateManager,
) -> None:
    """Run continuous coordinator until stopped by operator."""
    from backend.sandbox import cleanup_orphan_containers, configure_semaphore

    max_containers = max_challenges * len(model_specs)
    configure_semaphore(max_containers)
    await cleanup_orphan_containers()

    # Determine backend
    selected_backend = coordinator_backend
    if selected_backend == "auto":
        # Check if claude sdk is ready or fall back to universal
        if settings.gemini_api_key or settings.openai_api_key or settings.anthropic_api_key:
            selected_backend = "universal"
        else:
            selected_backend = "universal"

    console.print(f"[bold]Starting Coordinator (Backend: {selected_backend}, Ctrl+C to stop)...[/bold]\n")

    if selected_backend == "codex":
        from backend.agents.codex_coordinator import run_codex_coordinator
        results = await run_codex_coordinator(
            settings=settings,
            model_specs=model_specs,
            challenges_root=challenges_dir,
            no_submit=no_submit,
            coordinator_model=coordinator_model,
            msg_port=msg_port,
        )
    elif selected_backend == "claude":
        from backend.agents.claude_coordinator import run_claude_coordinator
        results = await run_claude_coordinator(
            settings=settings,
            model_specs=model_specs,
            challenges_root=challenges_dir,
            no_submit=no_submit,
            coordinator_model=coordinator_model,
            msg_port=msg_port,
        )
    else:
        # Universal Pydantic AI coordinator
        from backend.agents.universal_coordinator import UniversalCoordinator
        coord_model_spec = coordinator_model or (
            "google/gemini-2.5-pro" if settings.gemini_api_key
            else "openai/gpt-4o" if settings.openai_api_key
            else "anthropic/claude-3-7-sonnet-latest" if settings.anthropic_api_key
            else "google/gemini-2.0-flash"
        )
        coord = UniversalCoordinator(
            settings=settings,
            model_spec=coord_model_spec,
            model_specs=model_specs,
            challenges_root=challenges_dir,
            no_submit=no_submit,
            msg_port=msg_port,
            resume=resume,
            state_mgr=state_mgr,
        )
        results = await coord.run()

    console.print("\n[bold]Session Solves Summary:[/bold]")
    for challenge, data in results.get("results", {}).items():
        console.print(f"  {challenge}: {data.get('flag', 'no flag')}")
    console.print(f"\n[bold]Total Session Cost: ${results.get('total_cost_usd', 0):.4f}[/bold]")


@click.command()
@click.argument("message")
@click.option("--port", default=9400, type=int, help="Coordinator message port")
@click.option("--host", default="127.0.0.1", help="Coordinator host")
def msg(message: str, port: int, host: str) -> None:
    """Send an operational hint or message to the running coordinator."""
    import json
    import urllib.request

    body = json.dumps({"message": message}).encode()
    req = urllib.request.Request(
        f"http://{host}:{port}/msg",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            console.print(f"[green]Sent to coordinator:[/green] {data.get('queued', message[:200])}")
    except Exception as e:
        console.print(f"[red]Failed:[/red] {e}")
        console.print("Is the coordinator running?")
        sys.exit(1)


if __name__ == "__main__":
    main()
