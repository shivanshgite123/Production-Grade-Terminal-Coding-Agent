"""Command safety checks.

Documentation:
- re: https://docs.python.org/3/library/re.html
- subprocess security considerations: https://docs.python.org/3/library/subprocess.html

Why:
The agent can execute shell commands. The original implementation therefore
checks commands before execution and routes sensitive commands through HITL.
"""

from __future__ import annotations

import re


HARD_BLOCKED = ["rm -rf /", "shutdown", "reboot", "format", "mkfs", "dd if="]

SENSITIVE_PATTERNS = [
    r"\brm\b",
    r"\bchmod\b",
    r"\bchown\b",
    r"\bsudo\b",
    r"\bcurl\b",
    r"\bwget\b",
    r"\bnpm publish\b",
    r"\bgit push\b",
    r"\beval\b",
    r"\bexec\b",
    r">\s*/etc/",
    r"\bkill\b",
    r"\bpkill\b",
    r"\bsystemctl\b",
    r"\bservice\b",
    r"\biptables\b",
    r"\benv\b.*secret",
    r"subprocess\.call",
]

SENSITIVE_RE = re.compile("|".join(SENSITIVE_PATTERNS), re.IGNORECASE)


def is_hard_blocked(cmd: str) -> bool:
    return any(blocked in cmd.lower() for blocked in HARD_BLOCKED)


def is_sensitive(cmd: str) -> bool:
    return bool(SENSITIVE_RE.search(cmd))
