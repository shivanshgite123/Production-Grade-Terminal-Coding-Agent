# Autonomous Coder Agent — Modular Version

This project is the separated, multi-file version of the original single-file
Autonomous Coder Agent.

## Architecture

```text
main.py
  ↓
cli.py
  ↓
graph.py
  ↓
planner.py → writer.py
      ↘ hitl_gate → executor.py
                     ↓
                  repair.py
```

Cross-cutting modules:

- `models.py` — Pydantic schemas + LangGraph state
- `config.py` — environment/model/logging configuration
- `security.py` — sensitive-command detection
- `patching.py` — incremental patches + diffs
- `ui.py` — Rich terminal presentation
- `llm.py` — ChatGroq structured-output clients
- `routing.py` — graph routing rules

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Put your Groq API key in `.env`.

## Run

```bash
python -m autonomous_coder_agent run "Build a FastAPI todo API"
python -m autonomous_coder_agent interactive
```

## Important review note

The original monolithic file's `run()` path streamed the graph and then invoked
the graph again to obtain a final merged state. The modular version avoids that
duplicate execution by using one graph invocation. This is a small behavioral
fix made during modularization and should be treated as a code-review item.

## Documentation-first learning

See `DOCUMENTATION_MAP.md`. It maps every module to the specific Python or
framework documentation concept used by that module, why the concept is used,
and what to study before modifying the code.
