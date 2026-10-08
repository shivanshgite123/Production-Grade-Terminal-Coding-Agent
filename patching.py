"""Incremental patching and unified-diff rendering.

Documentation:
- difflib SequenceMatcher: https://docs.python.org/3/library/difflib.html
- pathlib Path: https://docs.python.org/3/library/pathlib.html
- Rich Panel/Text: https://rich.readthedocs.io/en/latest/
- Rich console: https://rich.readthedocs.io/en/latest/console.html

Why:
The project supports minimal search-and-replace edits rather than rewriting
an entire file. A unified diff makes the change reviewable by a human.
"""

from __future__ import annotations

import difflib
from pathlib import Path

from rich.panel import Panel
from rich.text import Text

from .ui import console
from .models import IncrementalPatch


def apply_patch(file_path: Path, patch: IncrementalPatch) -> tuple[bool, str]:
    """Apply a search-and-replace patch and return (success, diff_text)."""
    if not file_path.exists():
        return False, f"File {file_path} does not exist."

    original = file_path.read_text(encoding="utf-8")

    if patch.search_block not in original:
        lines_orig = original.splitlines()
        lines_search = patch.search_block.splitlines()
        matcher = difflib.SequenceMatcher(None, lines_orig, lines_search)
        match = matcher.find_longest_match(0, len(lines_orig), 0, len(lines_search))
        if match.size < max(1, len(lines_search) // 2):
            return False, "search_block not found in file (fuzzy match too weak)."
        matched_text = "\n".join(lines_orig[match.a : match.a + match.size])
        updated = original.replace(matched_text, patch.replace_block, 1)
    else:
        updated = original.replace(patch.search_block, patch.replace_block, 1)

    diff = list(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            updated.splitlines(keepends=True),
            fromfile=f"a/{file_path.name}",
            tofile=f"b/{file_path.name}",
        )
    )

    file_path.write_text(updated, encoding="utf-8")
    return True, "".join(diff)


def render_diff(diff_text: str) -> None:
    """Pretty-print a unified diff with Rich."""
    if not diff_text.strip():
        console.print("[agent.info]No changes in diff.[/]")
        return

    lines: list[Text] = []
    for line in diff_text.splitlines():
        if line.startswith(("+++", "---", "@@")):
            lines.append(Text(line, style="agent.diff.meta"))
        elif line.startswith("+"):
            lines.append(Text(line, style="agent.diff.add"))
        elif line.startswith("-"):
            lines.append(Text(line, style="agent.diff.remove"))
        else:
            lines.append(Text(line))

    panel_content = Text("\n").join(lines)
    console.print(Panel(panel_content, title="📝 Diff", border_style="cyan"))
