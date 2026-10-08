"""Command execution and Human-in-the-Loop gate.

Documentation:
- subprocess.run: https://docs.python.org/3/library/subprocess.html#subprocess.run
- Rich Confirm/Prompt: https://rich.readthedocs.io/en/latest/prompt.html
- LangGraph state: https://docs.langchain.com/oss/python/langgraph/graph-api

Why:
Executing shell commands is a security-sensitive boundary. This module keeps
approval, execution, timeout, stdout/stderr handling, and audit history together.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess

from rich.panel import Panel
from rich.prompt import Confirm

from .config import MAX_RETRIES
from .models import AgentState, ExecutionResult
from .ui import console, print_agent_header


def hitl_gate(state: AgentState) -> dict:
    """Ask a human to approve a sensitive command."""
    plan = state["plan"]
    idx = state["current_step_idx"]
    step = plan.steps[idx]
    cmd = (step.tool_args.command or "").strip()

    print_agent_header("HITL")
    console.print(
        Panel(
            f"[bold]Command:[/bold] [yellow]{cmd}[/yellow]\n"
            f"[bold]Reason:[/bold]  {step.description}\n"
            f"[bold]Expected:[/bold] {step.expected_outcome}",
            title="⚠️  Sensitive Command – Approval Required",
            border_style="magenta",
        )
    )

    approved = Confirm.ask("[agent.hitl]Approve this command?[/]", default=False)
    console.print(
        f"[agent.hitl]Decision: {'✅ APPROVED' if approved else '❌ REJECTED'}[/]"
    )

    return {
        "hitl_approved": approved,
        "execution_history": [
            {"event": "hitl", "step": idx + 1, "command": cmd, "approved": approved}
        ],
    }


def executor(state: AgentState) -> dict:
    plan = state["plan"]
    idx = state["current_step_idx"]
    step = plan.steps[idx]
    cmd = (step.tool_args.command or "").strip()
    retry = state.get("retry_count", 0)

    if state.get("hitl_approved") is False:
        console.print(f"[agent.warning]⏭  Skipping rejected command: {cmd}[/]")
        return {
            "execution_result": ExecutionResult(
                status="failure",
                stderr="Rejected by user (HITL)",
                retry_count=retry,
            ),
            "current_step_idx": idx + 1,
            "retry_count": 0,
            "hitl_approved": None,
            "current_step_error": "User rejected command via HITL.",
            "execution_history": [{"event": "exec_skipped", "step": idx + 1, "command": cmd}],
        }

    print_agent_header("Executor", idx + 1)

    if not cmd:
        raise ValueError(f"Step {idx + 1}: no command provided for executor.")

    if cmd.startswith("cd "):
        dir_name = cmd.split(" ", 1)[1].strip()
        try:
            os.chdir(dir_name)
            console.print(f"[agent.executor]📂  cd → {Path.cwd()}[/]")
            return {
                "execution_result": ExecutionResult(status="success", stdout=f"cd {dir_name}"),
                "current_step_idx": idx + 1,
                "retry_count": 0,
                "hitl_approved": None,
                "execution_history": [{"event": "exec_cd", "step": idx + 1, "dir": dir_name}],
            }
        except FileNotFoundError as exc:
            console.print(f"[agent.error]Directory not found: {exc}[/]")
            return {
                "execution_result": ExecutionResult(status="failure", stderr=str(exc)),
                "current_step_idx": idx + 1,
                "retry_count": 0,
                "current_step_error": str(exc),
                "execution_history": [{"event": "exec_cd_fail", "step": idx + 1, "error": str(exc)}],
            }

    console.print(f"[agent.executor]⚡  Running:[/] [bold]{cmd}[/bold]")

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired:
        console.print("[agent.error]⏰  Command timed out.[/]")
        return {
            "execution_result": ExecutionResult(
                status="failure", stderr="Timeout after 120s", retry_count=retry
            ),
            "current_step_idx": idx + 1,
            "retry_count": retry + 1,
            "current_step_error": "Timeout",
            "execution_history": [{"event": "exec_timeout", "step": idx + 1}],
        }

    if result.stdout.strip():
        console.print(Panel(result.stdout.strip(), title="stdout", border_style="green"))
    if result.stderr.strip():
        console.print(Panel(result.stderr.strip(), title="stderr", border_style="red"))

    if result.returncode == 0:
        console.print("[agent.success]✅  Exit 0[/]")
        return {
            "execution_result": ExecutionResult(status="success", stdout=result.stdout, retry_count=retry),
            "current_step_idx": idx + 1,
            "retry_count": 0,
            "current_step_error": None,
            "hitl_approved": None,
            "execution_history": [{"event": "exec_ok", "step": idx + 1, "command": cmd}],
        }

    console.print(f"[agent.error]❌  Exit {result.returncode}[/]")
    return {
        "execution_result": ExecutionResult(
            status="failure",
            stdout=result.stdout,
            stderr=result.stderr,
            retry_count=retry,
        ),
        "current_step_idx": idx,
        "retry_count": retry + 1,
        "current_step_error": result.stderr,
        "execution_history": [
            {"event": "exec_fail", "step": idx + 1, "command": cmd, "stderr": result.stderr[:300]}
        ],
    }
