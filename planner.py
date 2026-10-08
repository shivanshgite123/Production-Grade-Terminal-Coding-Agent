"""Planner agent.

Documentation:
- LangChain messages: https://docs.langchain.com/oss/python/langchain/messages
- LangGraph nodes/state: https://docs.langchain.com/oss/python/langgraph/graph-api
- Rich Progress/Table: https://rich.readthedocs.io/en/latest/

Why:
The planner converts a natural-language idea into a validated execution plan.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from .llm import plan_llm
from .models import AgentState
from .ui import console, print_agent_header


PLANNER_SYSTEM = """You are a senior software engineer creating executable plans.

## STEP 1: Analyse requirements
## STEP 2: Identify directory structure — always create a project directory
## STEP 3: Plan directory navigation
CRITICAL: After creating any directory, ALWAYS have a step to CD into it.
## STEP 4: List all required files with dependencies
## STEP 5: Determine command sequence (install, init, build, run)

INCREMENTAL REQUESTS: If the user says "change", "update", "fix", etc., set
is_incremental=true on the relevant write_file step. Do NOT rewrite unrelated files.

QUALITY CHECKLIST:
✓ No file creation before CD into project directory
✓ No imports before package installation
✓ Step IDs sequential from 1
✓ Expected outcomes are measurable
✓ is_incremental correctly set

CRITICAL RULES:
- NO 'json' tool exists.
- For file writing, ALWAYS use 'write_file'.
- DO NOT create a virtual environment unless asked.
- DO NOT initialise git unless asked.
"""


def detect_update_request(idea: str) -> bool:
    """Detect whether the request is an edit rather than a new project."""
    update_keywords = [
        "change", "update", "modify", "edit", "fix", "rename", "replace",
        "refactor", "adjust", "alter", "switch", "move", "add to", "remove from",
        "delete from", "set color", "set the", "make the",
    ]
    return any(kw in idea.lower() for kw in update_keywords)


def planner(state: AgentState) -> dict:
    idea = state["idea"]
    is_update = detect_update_request(idea)
    print_agent_header("Planner")

    with Progress(
        SpinnerColumn(),
        TextColumn("[agent.planner]Planning…"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("plan")
        plan = plan_llm.invoke(
            [
                SystemMessage(content=PLANNER_SYSTEM),
                HumanMessage(content=f"Create a plan for: {idea}"),
            ]
        )

    table = Table(title=f"🎯  {plan.goal}", box=box.ROUNDED, show_lines=True)
    table.add_column("#", style="bold cyan", width=4)
    table.add_column("Tool", style="yellow", width=12)
    table.add_column("File / Command", style="white")
    table.add_column("Expected Outcome", style="dim white")
    table.add_column("Incr?", style="magenta", width=6)

    for step in plan.steps:
        target = step.file_name if step.tool_name == "write_file" else (step.tool_args.command or "")
        table.add_row(
            str(step.step_id),
            step.tool_name,
            target[:60],
            step.expected_outcome[:60],
            "✓" if step.is_incremental else "",
        )

    console.print(table)
    console.print()

    return {
        "plan": plan,
        "is_update_request": is_update,
        "execution_history": [{"event": "plan_created", "goal": plan.goal}],
    }
