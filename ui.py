"""Terminal presentation helpers built with Rich.

Documentation:
- Rich overview: https://rich.readthedocs.io/en/latest/
- Live display: https://rich.readthedocs.io/en/latest/live.html
- Progress: https://rich.readthedocs.io/en/latest/progress.html
- Panels: https://rich.readthedocs.io/en/latest/panel.html
- Syntax highlighting: https://rich.readthedocs.io/en/latest/syntax.html
- Tables: https://rich.readthedocs.io/en/latest/tables.html
- Prompt/Confirm: https://rich.readthedocs.io/en/latest/prompt.html

Why:
UI code is separated from business logic so agents can focus on planning,
writing, execution, and repair.
"""

from __future__ import annotations

from rich import box
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text
from rich.theme import Theme


THEME = Theme(
    {
        "agent.planner": "bold cyan",
        "agent.writer": "bold green",
        "agent.executor": "bold yellow",
        "agent.error": "bold red",
        "agent.success": "bold green",
        "agent.warning": "bold yellow",
        "agent.info": "dim white",
        "agent.hitl": "bold magenta",
        "agent.stream": "white",
        "agent.diff.add": "green",
        "agent.diff.remove": "red",
        "agent.diff.meta": "cyan",
    }
)

console = Console(theme=THEME)


def stream_text(label: str, text: str, style: str = "agent.stream") -> None:
    """Simulate token-level streaming output with Rich."""
    console.print(f"\n[{style}]{label}[/]")
    words = text.split()
    buf = ""
    with Live(console=console, refresh_per_second=20) as live:
        for word in words:
            buf += word + " "
            live.update(Text(buf, style=style))
    console.print()


def print_agent_header(agent: str, step: int | None = None) -> None:
    step_txt = f"  Step {step}" if step is not None else ""
    style_map = {
        "Planner": "agent.planner",
        "Writer": "agent.writer",
        "Executor": "agent.executor",
        "HITL": "agent.hitl",
        "Repair": "agent.error",
    }
    style = style_map.get(agent, "white")
    console.print(Rule(f"[{style}] {agent}{step_txt} [/{style}]", style=style))
