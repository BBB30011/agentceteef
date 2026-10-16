"""Antigravity CLI Solver — Tokenless CTF solver using the host's Antigravity CLI (agy)."""

from __future__ import annotations

import asyncio
import logging
import shutil
from pathlib import Path
from typing import Any

from backend.config import Settings
from backend.cost_tracker import CostTracker
from backend.ctfd import CTFdClient
from backend.prompts import ChallengeMeta, build_prompt, list_distfiles
from backend.sandbox import LocalSandbox, SandboxProtocol
from backend.solver_base import CANCELLED, ERROR, FLAG_FOUND, GAVE_UP, SolverResult
from backend.tools.ctf_helpers import extract_flag_candidates
from backend.tracing import SolverTracer

logger = logging.getLogger(__name__)


class AntigravitySolver:
    """Solver backend utilizing the Antigravity CLI ('agy') without requiring external API tokens."""

    def __init__(
        self,
        model_spec: str = "agy/default",
        challenge_dir: str = "",
        meta: ChallengeMeta | None = None,
        ctfd: CTFdClient | None = None,
        cost_tracker: CostTracker | None = None,
        settings: Settings | None = None,
        cancel_event: asyncio.Event | None = None,
        no_submit: bool = False,
        submit_fn: Any = None,
        message_bus: Any = None,
        notify_coordinator: Any = None,
        sandbox: SandboxProtocol | None = None,
    ) -> None:
        self.model_spec = model_spec
        self.challenge_dir = challenge_dir
        self.meta = meta or ChallengeMeta(name="unknown")
        self.ctfd = ctfd
        self.cost_tracker = cost_tracker or CostTracker()
        self.settings = settings or Settings()
        self.cancel_event = cancel_event or asyncio.Event()
        self.no_submit = no_submit
        self.submit_fn = submit_fn
        self.message_bus = message_bus
        self.notify_coordinator = notify_coordinator

        self.agent_name = f"{self.meta.name}/antigravity"
        self.tracer = SolverTracer(self.meta.name, "antigravity")

        # Use LocalSandbox by default for host CLI execution, or Docker
        self.sandbox = sandbox or LocalSandbox(
            image="local",
            challenge_dir=challenge_dir,
            memory_limit=getattr(self.settings, "container_memory_limit", "4g"),
        )

        self._bump_queue: list[str] = []
        self._step_count = 0
        self._confirmed_flag: str | None = None
        self._agy_bin = shutil.which("agy") or "/home/kali/.local/bin/agy"

    async def start(self) -> None:
        """Initialize the sandbox environment and verify agy CLI presence."""
        if not getattr(self.sandbox, "workspace_dir", None):
            await self.sandbox.start()

        if not Path(self._agy_bin).exists() and not shutil.which("agy"):
            logger.warning("Antigravity CLI ('agy') not found in PATH or standard locations.")

        logger.info("[%s] AntigravitySolver started (workspace: %s)", self.agent_name, self.sandbox.workspace_dir)

    def bump(self, insights: str) -> None:
        """Receive coordinator insights or operator hints."""
        self._bump_queue.append(insights)
        self.tracer.event("bump_received", insights=insights[:200])

    async def run_until_done_or_gave_up(self) -> SolverResult:
        """Run an automated solving turn using agy CLI."""
        if self.cancel_event.is_set():
            return SolverResult(
                flag=None,
                status=CANCELLED,
                findings_summary="Cancelled before turn started",
                step_count=self._step_count,
                cost_usd=0.0,
                log_path=self.tracer.path,
            )

        self._step_count += 1
        distfile_names = list_distfiles(self.challenge_dir)

        # Build comprehensive instructions
        base_prompt = build_prompt(self.meta, distfile_names, container_arch="host", has_named_tools=False)

        prompt_parts = [
            f"# CTF Challenge Solver — {self.meta.name}",
            f"You are operating in: {self.sandbox.workspace_dir}/workspace",
            base_prompt,
            "",
            "CRITICAL GOAL:",
            "Analyze files in distfiles/, interact with service if specified, find the flag.",
            "Once you find the flag, output: FLAG: <flag_here>",
        ]

        if self._bump_queue:
            bump_text = "\n".join(self._bump_queue)
            self._bump_queue.clear()
            prompt_parts.append(f"\n[COORDINATOR GUIDANCE]:\n{bump_text}")

        full_prompt = "\n".join(prompt_parts)
        self.tracer.event("turn_started", step=self._step_count)

        # Check if agy binary exists
        if not shutil.which("agy") and not Path(self._agy_bin).exists():
            # Fallback message
            return SolverResult(
                flag=None,
                status=ERROR,
                findings_summary="Antigravity CLI ('agy') is not installed or available in PATH.",
                step_count=self._step_count,
                cost_usd=0.0,
                log_path=self.tracer.path,
            )

        # Run agy command non-interactively
        workspace_run_dir = f"{self.sandbox.workspace_dir}/workspace"
        Path(workspace_run_dir).mkdir(parents=True, exist_ok=True)

        cmd = [
            self._agy_bin,
            "--dangerously-skip-permissions",
            "--add-dir",
            self.sandbox.workspace_dir,
            "--print",
            full_prompt,
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workspace_run_dir,
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(),
                timeout=600,  # 10 minutes turn limit
            )

            stdout_str = stdout_bytes.decode("utf-8", errors="replace")
            stderr_str = stderr_bytes.decode("utf-8", errors="replace")
            output_combined = stdout_str + "\n" + stderr_str

            self.tracer.event("model_output", output=output_combined[:2000], step=self._step_count)

            # Extract flag candidates from output
            candidates = extract_flag_candidates(output_combined)

            # If no candidates in CLI output, also inspect workspace directory
            if not candidates and getattr(self.sandbox, "workspace_dir", None):
                from backend.tools.ctf_helpers import do_find_flags_in_workspace
                found_flags_str = await do_find_flags_in_workspace(self.sandbox, self.sandbox.workspace_dir)
                candidates = extract_flag_candidates(found_flags_str)

            for cand in candidates:
                logger.info("[%s] Testing detected flag candidate: %s", self.agent_name, cand)
                if self.submit_fn:
                    res = self.submit_fn(cand)
                    if asyncio.iscoroutine(res):
                        display, is_confirmed = await res
                    else:
                        display, is_confirmed = res
                    if is_confirmed:
                        self._confirmed_flag = cand
                        self.tracer.event("flag_confirmed", flag=cand, step=self._step_count)
                        return SolverResult(
                            flag=cand,
                            status=FLAG_FOUND,
                            findings_summary=f"Flag confirmed: {cand} ({display})",
                            step_count=self._step_count,
                            cost_usd=0.0,
                            log_path=self.tracer.path,
                        )
                elif self.no_submit or not self.ctfd:
                    self._confirmed_flag = cand
                    self.tracer.event("flag_found_dry_run", flag=cand, step=self._step_count)
                    return SolverResult(
                        flag=cand,
                        status=FLAG_FOUND,
                        findings_summary=f"Flag candidate found (dry run): {cand}",
                        step_count=self._step_count,
                        cost_usd=0.0,
                        log_path=self.tracer.path,
                    )

            # If no confirmed flag yet, summarize findings
            summary = output_combined[:600].strip() or "No output from agy."
            return SolverResult(
                flag=None,
                status=GAVE_UP,
                findings_summary=summary,
                step_count=self._step_count,
                cost_usd=0.0,
                log_path=self.tracer.path,
            )

        except TimeoutError:
            return SolverResult(
                flag=None,
                status=ERROR,
                findings_summary="Turn timed out after 600s",
                step_count=self._step_count,
                cost_usd=0.0,
                log_path=self.tracer.path,
            )
        except Exception as e:
            return SolverResult(
                flag=None,
                status=ERROR,
                findings_summary=f"Error executing agy: {e}",
                step_count=self._step_count,
                cost_usd=0.0,
                log_path=self.tracer.path,
            )

    async def stop(self) -> None:
        """Clean up solver and sandbox."""
        self.tracer.close()
        if hasattr(self.sandbox, "stop"):
            await self.sandbox.stop()
        logger.info("[%s] AntigravitySolver stopped", self.agent_name)
