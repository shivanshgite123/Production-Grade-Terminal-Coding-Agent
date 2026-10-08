"""Graph routing functions.

Documentation:
- LangGraph conditional edges: https://docs.langchain.com/oss/python/langgraph/graph-api

Why:
Routing is business control flow. Keeping it independent makes the workflow
easy to inspect and test without coupling it to individual agents.
"""

from __future__ import annotations

import sys

from rich.panel import Panel
from rich.prompt import Prompt

from .config import MAX_RETRIES
from .models import AgentState
from .security import is_sensitive
from .ui import console


def router(state: AgentState) -> str:
    """Choose the next node after planning/writing."""
    plan = state["plan"]
    idx = state["current_step_idx"]

    if idx >= len(plan.steps):
        return "__end__"

    step = plan.steps[idx]
    if step.tool_name == "write_file":
        return "writer"
    if step.tool_name == "run_command":
        cmd = (step.tool_args.command or "").strip()
        return "hitl_gate" if is_sensitive(cmd) else "executor"
    return "__end__"


def post_executor_router(state: AgentState) -> str:
    """Handle failure → repair/retry or human escalation."""
    result = state.get("execution_result")
    retry = state.get("retry_count", 0)
    idx = state["current_step_idx"]
    plan = state["plan"]

    if result and result.status == "failure":
        if retry < MAX_RETRIES:
            step = plan.steps[idx]
            if step.tool_name == "write_file":
                return "repair"
            console.print(
                f"[agent.warning]↩  Retrying step {idx + 1} "
                f"(attempt {retry + 1}/{MAX_RETRIES})…[/]"
            )
            return "executor"

        console.print(
            Panel(
                f"[bold red]Step {idx + 1} failed {MAX_RETRIES} times.[/bold red]\n"
                f"Error: {state.get('current_step_error', 'unknown')}\n\n"
                "Please review and press Enter to skip or Ctrl+C to abort.",
                title="🆘  Human Escalation Required",
                border_style="red",
            )
        )
        try:
            Prompt.ask("[agent.hitl]Skip this step and continue?[/]", default="yes")
        except (EOFError, KeyboardInterrupt):
            sys.exit(1)
        state["current_step_idx"] += 1
        return router(state)

    return router(state)


def post_hitl_router(state: AgentState) -> str:
    """Approved → executor; rejected → advance to the next step."""
    if state.get("hitl_approved"):
        return "executor"
    state["current_step_idx"] += 1
    return router(state)


def post_repair_router(state: AgentState) -> str:
    """After repair, re-run the executor for the same step."""
    return "executor"
