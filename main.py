"""Executable entry point.

Documentation:
- Python __main__ behavior: https://docs.python.org/3/library/__main__.html

Run:
    python -m autonomous_coder_agent
"""

from .cli import cli


if __name__ == "__main__":
    cli()
