"""Writer agent for full-file generation and incremental patching.

Documentation:
- LangChain messages: https://docs.langchain.com/oss/python/langchain/messages
- pathlib: https://docs.python.org/3/library/pathlib.html
- Rich Syntax: https://rich.readthedocs.io/en/latest/syntax.html

Why:
Writing files and applying incremental changes are separate responsibilities
from planning and command execution.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Dict

from langchain_core.messages import HumanMessage, SystemMessage
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax

from .llm import patch_llm, write_llm
from .models import AgentState
from .patching import apply_patch, render_diff
from .ui import console, print_agent_header, stream_text


WRITER_SYSTEM = """You are a senior software engineer.
Generate complete, working, production-quality code.
Rules:
- Full file content, no placeholders.
- All imports included.
- Proper error handling.
- No hardcoded secrets.
"""

PATCH_SYSTEM = """You are a senior software engineer performing incremental code edits.
Given the current file content, the change instruction, and the expected outcome,
produce a minimal search-and-replace patch.
- search_block: exact verbatim substring currently in the file.
- replace_block: replacement (can be empty to delete).
- reason: one-sentence explanation.
Do NOT rewrite the whole file.
"""


def _safe_write(file_path: Path, content: str) -> Path:
    """Write content, falling back to cwd or tempdir on permission errors."""
    for candidate in [
        file_path,
        Path.cwd() / file_path.name,
        Path(tempfile.gettempdir()) / file_path.name,
    ]:
        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)
            candidate.write_text(content, encoding="utf-8")
            return candidate
        except PermissionError:
            continue
    raise PermissionError(f"Cannot write {file_path} – no writable location found.")


def writer(state: AgentState) -> dict:
    plan = state["plan"]
    idx = state["current_step_idx"]
    step = plan.steps[idx]

    print_agent_header("Writer", idx + 1)

    file_path = Path(step.file_name)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    history_entry: Dict = {
        "event": "write",
        "step": idx + 1,
        "file": step.file_name,
        "incremental": step.is_incremental,
    }

    if step.is_incremental and file_path.exists():
        console.print(f"[agent.writer]✂️  Incremental edit → {file_path}[/]")
        existing_content = file_path.read_text(encoding="utf-8")

        with Progress(SpinnerColumn(), TextColumn("[agent.writer]Generating patch…"), console=console, transient=True) as progress:
            progress.add_task("patch")
            patch = patch_llm.invoke(
                [
                    SystemMessage(content=PATCH_SYSTEM),
                    HumanMessage(
                        content=(
                            f"File: {step.file_name}\n"
                            f"Current content:\n```\n{existing_content}\n```\n\n"
                            f"Instruction: {step.description}\n"
                            f"Expected outcome: {step.expected_outcome}"
                        )
                    ),
                ]
            )

        success, diff_text = apply_patch(file_path, patch)
        if success:
            render_diff(diff_text)
            stream_text("  [agent.writer]Patch reasoning:[/]", patch.reason, style="agent.info")
            console.print(f"[agent.success]✅  Patched {file_path}[/]")
            history_entry["status"] = "patch_ok"
        else:
            console.print(
                f"[agent.error]Patch failed: {diff_text}\nFalling back to full rewrite.[/]"
            )
            step.is_incremental = False
            history_entry["status"] = "patch_fallback"

    if not step.is_incremental or not file_path.exists():
        console.print(f"[agent.writer]✍️  Writing → {file_path}[/]")

        with Progress(SpinnerColumn(), TextColumn("[agent.writer]Generating code…"), console=console, transient=True) as progress:
            progress.add_task("write")
            generated = write_llm.invoke(
                [
                    SystemMessage(content=WRITER_SYSTEM),
                    HumanMessage(
                        content=(
                            f"Description: {step.description}\n"
                            f"file_name: {step.file_name}\n"
                            f"expected_output: {step.expected_outcome}"
                        )
                    ),
                ]
            )

        content = generated.content
        resolved_path = _safe_write(file_path, content)
        lang = resolved_path.suffix.lstrip(".") or "text"
        preview = content if len(content) < 1200 else content[:1200] + "\n# … (truncated)"
        console.print(Syntax(preview, lang, theme="monokai", line_numbers=True))
        console.print(f"[agent.success]✅  Written {resolved_path}[/]")

        history_entry["status"] = "full_write_ok"
        return {
            "generated_code": [{str(resolved_path): content}],
            "current_step_idx": idx + 1,
            "execution_history": [history_entry],
        }

    return {
        "generated_code": [{str(file_path): file_path.read_text(encoding="utf-8")}],
        "current_step_idx": idx + 1,
        "execution_history": [history_entry],
    }
