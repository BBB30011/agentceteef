"""Universal AI coordinator powered by Pydantic AI — works with any supported LLM (Gemini, GPT-4o, Claude, DeepSeek, Local, etc.)."""

from __future__ import annotations

import logging
from typing import Any

from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelMessage

from backend.agents.coordinator_core import (
    do_broadcast,
    do_bump_agent,
    do_check_swarm_status,
    do_fetch_challenges,
    do_get_solve_status,
    do_kill_swarm,
    do_read_solver_trace,
    do_spawn_swarm,
    do_submit_flag,
)
from backend.agents.coordinator_loop import build_deps, run_event_loop
from backend.config import Settings
from backend.cost_tracker import CostTracker
from backend.ctfd import CTFdClient
from backend.deps import CoordinatorDeps
from backend.models import resolve_model, resolve_model_settings

logger = logging.getLogger(__name__)

COORDINATOR_PROMPT = """\
You are an autonomous CTF competition coordinator running for the ENTIRE duration of a live competition.
Your mission is to maximize the total number of challenges solved and points earned.

Strategic Operating Principles:
1. Challenge Prioritization:
   - Identify easiest unsolved challenges first (high solve count, low point value, or intro tags).
   - Spawn swarms to attack multiple challenges in parallel up to max concurrency.
2. Monitoring & Oversight:
   - Regularly check swarm status and read solver traces using `read_solver_trace`.
   - Identify when solvers are stuck (e.g. repeated errors, loop warnings, fruitless brute force).
3. Strategic Guidance:
   - When a solver is stuck, use `bump_agent` to provide concrete technical direction (alternative tools, decompilation approaches, forgotten edge cases, alternative encodings).
   - When one solver finds a partial secret, cipher key, or architecture insight, use `broadcast` to share that finding with all solvers on that challenge.
4. Rules:
   - Do NOT kill swarms prematurely. Solvers will explore multiple hypothesis spaces.
   - Only consider killing or retiring when a challenge is solved or fundamentally impossible.
   - When a flag is confirmed, celebrate and move on to the next highest priority challenge.
"""


def build_universal_coordinator_agent(model_spec: str, settings: Settings) -> Agent[CoordinatorDeps, str]:
    """Create a Pydantic AI Agent equipped with all CTF coordinator tools."""
    model = resolve_model(model_spec, settings)
    agent: Agent[CoordinatorDeps, str] = Agent(
        model=model,
        deps_type=CoordinatorDeps,
        system_prompt=COORDINATOR_PROMPT,
    )

    @agent.tool
    async def fetch_challenges(ctx: RunContext[CoordinatorDeps]) -> str:
        """List all challenges with category, points, solve count, and status."""
        return await do_fetch_challenges(ctx.deps)

    @agent.tool
    async def get_solve_status(ctx: RunContext[CoordinatorDeps]) -> str:
        """Check which challenges are solved and which swarms are currently running."""
        return await do_get_solve_status(ctx.deps)

    @agent.tool
    async def spawn_swarm(ctx: RunContext[CoordinatorDeps], challenge_name: str) -> str:
        """Launch all solver models on a specific challenge."""
        return await do_spawn_swarm(ctx.deps, challenge_name)

    @agent.tool
    async def check_swarm_status(ctx: RunContext[CoordinatorDeps], challenge_name: str) -> str:
        """Get per-agent progress, attempts, and latest activity for a swarm."""
        return await do_check_swarm_status(ctx.deps, challenge_name)

    @agent.tool
    async def submit_flag(ctx: RunContext[CoordinatorDeps], challenge_name: str, flag: str) -> str:
        """Submit a flag candidate to the CTFd platform."""
        return await do_submit_flag(ctx.deps, challenge_name, flag)

    @agent.tool
    async def kill_swarm(ctx: RunContext[CoordinatorDeps], challenge_name: str) -> str:
        """Cancel and terminate all solver agents for a challenge."""
        return await do_kill_swarm(ctx.deps, challenge_name)

    @agent.tool
    async def bump_agent(
        ctx: RunContext[CoordinatorDeps], challenge_name: str, model_spec: str, insights: str
    ) -> str:
        """Inject targeted technical guidance or a hint into a specific solver agent."""
        return await do_bump_agent(ctx.deps, challenge_name, model_spec, insights)

    @agent.tool
    async def broadcast(ctx: RunContext[CoordinatorDeps], challenge_name: str, message: str) -> str:
        """Broadcast a critical clue or finding to ALL solvers working on a challenge."""
        return await do_broadcast(ctx.deps, challenge_name, message)

    @agent.tool
    async def read_solver_trace(
        ctx: RunContext[CoordinatorDeps], challenge_name: str, model_spec: str, last_n: int = 20
    ) -> str:
        """Read recent tool execution traces from a specific solver to see what it tried."""
        return await do_read_solver_trace(ctx.deps, challenge_name, model_spec, last_n)

    return agent


class UniversalCoordinator:
    """Universal LLM coordinator that can run with any provider supported by Pydantic AI."""

    def __init__(
        self,
        settings: Settings,
        model_spec: str = "google/gemini-2.5-pro",
        model_specs: list[str] | None = None,
        challenges_root: str = "challenges",
        no_submit: bool = False,
        msg_port: int = 0,
    ) -> None:
        self.settings = settings
        self.model_spec = model_spec
        self.model_specs = model_specs
        self.challenges_root = challenges_root
        self.no_submit = no_submit
        self.msg_port = msg_port
        self.agent = build_universal_coordinator_agent(model_spec, settings)
        self.model_settings = resolve_model_settings(model_spec)
        self.message_history: list[ModelMessage] = []

    async def run(self) -> dict[str, Any]:
        """Start and run the coordinator loop."""
        ctfd, cost_tracker, deps = build_deps(
            self.settings,
            self.model_specs,
            self.challenges_root,
            self.no_submit,
        )
        deps.msg_port = self.msg_port

        async def turn_fn(message: str) -> None:
            logger.info("Universal Coordinator turn triggered: %s", message[:120])
            try:
                # Keep history trimmed if it gets excessively large
                if len(self.message_history) > 60:
                    self.message_history = self.message_history[-40:]

                result = await self.agent.run(
                    message,
                    deps=deps,
                    message_history=self.message_history if self.message_history else None,
                    model_settings=self.model_settings,
                )
                self.message_history = list(result.all_messages())
                logger.info("Coordinator response: %s", (result.output or "")[:200])
            except Exception as e:
                logger.error("Coordinator turn error: %s", e, exc_info=True)

        return await run_event_loop(deps, ctfd, cost_tracker, turn_fn=turn_fn)
