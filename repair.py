"""LLM-assisted repair agent.

Documentation:
- LangChain messages: https://docs.langchain.com/oss/python/langchain/messages
- pathlib: https://docs.python.org/3/library/pathlib.html
- LangGraph graph nodes: https://docs.langchain.com/oss/python/langgraph/graph-api

Why:
Repair is deliberately isolated from normal writing so failures can be
diagnosed and corrected without mixing concerns.
"""

from __future__ import annotations

from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import MAX_RETRIES
from .llm import repair_llm
from .models import AgentState
from .ui import console, print_agent_header
from .writer import _safe_write


def repair(state: AgentState) -> dict:
    """Attempt LLM-assisted repair of the last failing file."""
    plan = state["plan"]
    idx = state["current_step_idx"]
    step = plan.steps[idx]
    error = state.get("current_step_error", "Unknown error")
    retry = state.get("retry_count", 0)

    print_agent_header("Repair")
    console.print(
        Panel(
            f"[bold red]Error:[/bold red] {error}\n"
            f"[dim]Retry attempt {retry}/{MAX_RETRIES}[/dim]",
            border_style="red",
        )
    )

    last_content = ""
    for code_dict in reversed(state.get("generated_code") or []):
        if step.file_name in code_dict:
            last_content = code_dict[step.file_name]
            break

    if not last_content:
        console.print("[agent.error]No prior content to repair – skipping step.[/]")
        return {
            "current_step_idx": idx + 1,
            "retry_count": 0,
            "current_step_error": None,
            "execution_history": [{"event": "repair_skip", "step": idx + 1}],
        }

    with Progress(SpinnerColumn(), TextColumn("[agent.error]Repairing…"), console=console, transient=True) as progress:
        progress.add_task("repair")
        repaired = repair_llm.invoke(
            [
                SystemMessage(content="You are a debugging expert. Fix the provided code based on the error."),
                HumanMessage(
                    content=(
                        f"File: {step.file_name}\n"
                        f"Error: {error}\n"
                        f"Broken code:\n```\n{last_content}\n```\n"
                        f"Return the fully corrected file."
                    )
                ),
            ]
        )

    resolved = _safe_write(Path(step.file_name), repaired.content)
    console.print(f"[agent.success]🔧  Repaired and wrote {resolved}[/]")

    return {
        "generated_code": [{str(resolved): repaired.content}],
        "current_step_error": None,
        "execution_history": [{"event": "repaired", "step": idx + 1}],
    }
