"""Click CLI and terminal entry points.

Documentation:
- Click quickstart: https://click.palletsprojects.com/en/stable/quickstart/
- Click arguments/options: https://click.palletsprojects.com/en/stable/arguments/
- Click groups: https://click.palletsprojects.com/en/stable/commands-and-groups/
- LangGraph invocation/streaming: https://docs.langchain.com/oss/python/langgraph/graph-api

Why:
CLI parsing should not be mixed with graph construction or agent logic.
"""

from __future__ import annotations

import sys

import click
from rich import box
from rich.columns import Columns
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table

from .config import MAX_RETRIES
from .graph import GRAPH
from .models import AgentState
from .ui import console


def initial_state(idea: str) -> AgentState:
    return {
        "idea": idea,
        "plan": None,  # type: ignore[assignment]
        "generated_code": [],
        "execution_result": None,
        "current_step_idx": 0,
        "current_step_error": None,
        "retry_count": 0,
        "hitl_approved": None,
        "execution_history": [],
        "is_update_request": False,
    }


def print_banner() -> None:
    banner = """
╔══════════════════════════════════════════════════════════════╗
║          🤖  Autonomous Coder Agent  v2.0                    ║
║          Planner → Writer → Executor  (LangGraph)            ║
╚══════════════════════════════════════════════════════════════╝
"""
    console.print(banner, style="bold cyan")
    console.print(
        Columns(
            [
                "[cyan]✓[/] Feedback loop (auto-retry)",
                "[magenta]✓[/] Human-in-the-loop (HITL)",
                "[green]✓[/] Streaming output",
                "[yellow]✓[/] Incremental patching",
            ]
        )
    )
    console.print()


def print_summary(final_state: AgentState) -> None:
    console.print(Rule("[bold green]Execution Summary[/bold green]", style="green"))
    history = final_state.get("execution_history", [])

    table = Table(box=box.SIMPLE, show_header=True)
    table.add_column("Event", style="cyan")
    table.add_column("Step", style="yellow")
    table.add_column("Detail", style="white")

    for entry in history:
        event = entry.get("event", "")
        step = str(entry.get("step", ""))
        detail = (
            entry.get("command", "")
            or entry.get("file", "")
            or entry.get("error", "")
            or entry.get("dir", "")
            or entry.get("goal", "")
        )
        table.add_row(event, step, detail[:80])

    console.print(table)

    generated = final_state.get("generated_code") or []
    if generated:
        files = sorted({key for item in generated for key in item})
        console.print(f"\n[bold]Files written:[/bold] {', '.join(files)}")

    console.print(Rule(style="green"))


@click.group()
def cli() -> None:
    """Autonomous Coder Agent – multi-agent LangGraph coding system."""


@cli.command("run")
@click.argument("idea", required=False)
@click.option("--stream/--no-stream", default=True, help="Stream agent output (default: on)")
@click.option("--max-retries", default=MAX_RETRIES, show_default=True, help="Max executor retries per step")
def run(idea: str | None, stream: bool, max_retries: int) -> None:
    """Run the coding agent with IDEA (or prompt interactively)."""
    print_banner()

    if not idea:
        idea = Prompt.ask("[bold cyan]💡 What would you like to build or change?[/]")

    if not idea.strip():
        console.print("[red]No idea provided. Exiting.[/]")
        sys.exit(1)

    console.print(f"\n[bold]Task:[/bold] {idea}\n")

    state = initial_state(idea)

    try:
        if stream:
            final_state = GRAPH.invoke(state)
        else:
            final_state = GRAPH.invoke(state)

        print_summary(final_state)
        console.print("\n[bold green]🎉  Agent completed successfully![/bold green]")
    except KeyboardInterrupt:
        console.print("\n[yellow]⛔  Interrupted by user.[/yellow]")
        sys.exit(130)
    except Exception as exc:
        console.print_exception()
        console.print(f"\n[bold red]Fatal error: {exc}[/bold red]")
        sys.exit(1)


@cli.command("interactive")
def interactive() -> None:
    """Interactive REPL – send multiple tasks in sequence."""
    print_banner()
    console.print("[dim]Type 'exit' or 'quit' to stop.[/dim]\n")

    while True:
        try:
            idea = Prompt.ask("[bold cyan]💡 Task[/]")
        except (EOFError, KeyboardInterrupt):
            break

        if idea.strip().lower() in ("exit", "quit", "q"):
            break

        try:
            final_state = GRAPH.invoke(initial_state(idea))
            print_summary(final_state)
        except Exception as exc:
            console.print_exception()
            console.print(f"[bold red]Error: {exc}[/bold red]")

    console.print("\n[cyan]Goodbye! 👋[/cyan]")
