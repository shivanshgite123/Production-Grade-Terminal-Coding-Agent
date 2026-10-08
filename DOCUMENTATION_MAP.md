# Documentation Review Map

The goal is not just to split the code. The goal is to learn **how to read
official documentation first and then write code from the documented API**.

## 1. `config.py`

### Implemented
- `os.getenv(...)` reads optional configuration from environment variables.
- `load_dotenv()` loads values from `.env`.
- `logging.basicConfig(...)` establishes application logging.

### Why
Configuration and logging are cross-cutting concerns. Keeping them centralized
prevents every agent module from owning environment setup.

### Official docs
- Python `os.getenv`: https://docs.python.org/3/library/os.html#os.getenv
- python-dotenv: https://bbc2.github.io/python-dotenv/
- Python logging: https://docs.python.org/3/library/logging.html

---

## 2. `models.py`

### Implemented
- `BaseModel` and `Field` define validated structured data.
- `Literal` restricts tool names/status values.
- `TypedDict` defines graph state.
- `Annotated[..., add]` expresses reducer behavior for accumulated state.

### Why
The LLM is asked for structured output. A schema gives the model a contract
and gives Python a validation boundary.

### Official docs
- Pydantic models: https://docs.pydantic.dev/latest/concepts/models/
- Pydantic fields: https://docs.pydantic.dev/latest/concepts/fields/
- Python typing: https://docs.python.org/3/library/typing.html
- LangGraph graph/state API: https://docs.langchain.com/oss/python/langgraph/graph-api

---

## 3. `security.py`

### Implemented
- Regex compilation with `re.compile`.
- Hard-block and sensitive-command detection.

### Why
The agent can execute shell commands, so commands must be classified before
execution.

### Official docs
- `re`: https://docs.python.org/3/library/re.html
- `subprocess` security: https://docs.python.org/3/library/subprocess.html

### Review point
The original implementation defines `is_hard_blocked()` but the routing path
only checks `is_sensitive()`. That means the hard-block list is not actually
used as an execution gate. This should be fixed before production use.

---

## 4. `patching.py`

### Implemented
- `Path.exists()`, `read_text()`, `write_text()`.
- `difflib.SequenceMatcher` fuzzy fallback.
- `difflib.unified_diff` for reviewable patches.

### Why
Incremental editing is safer and easier to review than rewriting a whole file.

### Official docs
- pathlib: https://docs.python.org/3/library/pathlib.html
- difflib: https://docs.python.org/3/library/difflib.html

---

## 5. `ui.py`

### Implemented
- Rich `Console`, `Theme`, `Live`, `Panel`, `Rule`, `Text`.

### Why
Terminal rendering is presentation logic, not agent logic.

### Official docs
- Rich: https://rich.readthedocs.io/en/latest/
- Live: https://rich.readthedocs.io/en/latest/live.html
- Console: https://rich.readthedocs.io/en/latest/console.html

---

## 6. `llm.py`

### Implemented
- `ChatGroq(...)`.
- `.with_structured_output(...)`.
- Different temperature settings for planning, writing, patching, and repair.

### Why
Each agent has a distinct output contract. Structured output keeps those
contracts explicit.

### Official docs
- ChatGroq: https://docs.langchain.com/oss/python/integrations/chat/groq
- LangChain models/structured output: https://docs.langchain.com/oss/python/langchain/models

---

## 7. `planner.py`

### Implemented
- `SystemMessage` + `HumanMessage`.
- LLM invocation to produce an `ExecutionPlan`.
- Rich progress/table presentation.

### Why
The planner converts an idea into ordered, executable steps before any file
or command action occurs.

### Official docs
- Messages: https://docs.langchain.com/oss/python/langchain/messages
- LangGraph: https://docs.langchain.com/oss/python/langgraph/graph-api

---

## 8. `writer.py`

### Implemented
- Full file generation.
- Incremental patch generation.
- `Path` filesystem operations.
- Rich syntax preview.

### Why
The writer owns code creation. It can either create a complete file or apply
a minimal change.

### Official docs
- pathlib: https://docs.python.org/3/library/pathlib.html
- Rich syntax: https://rich.readthedocs.io/en/latest/syntax.html

---

## 9. `executor.py`

### Implemented
- HITL approval using `Confirm.ask`.
- `subprocess.run(...)`.
- timeout, stdout, stderr and return-code handling.
- special handling for `cd`.

### Why
Command execution is the highest-risk runtime boundary.

### Official docs
- subprocess: https://docs.python.org/3/library/subprocess.html
- subprocess.run: https://docs.python.org/3/library/subprocess.html#subprocess.run
- Rich prompts: https://rich.readthedocs.io/en/latest/prompt.html

---

## 10. `repair.py`

### Implemented
- Reads the latest generated file content.
- Sends the error + code to a repair LLM.
- Writes corrected content.

### Why
Error recovery is a separate responsibility from initial generation.

### Official docs
- LangChain messages: https://docs.langchain.com/oss/python/langchain/messages
- pathlib: https://docs.python.org/3/library/pathlib.html

---

## 11. `routing.py`

### Implemented
- Conditional routing based on tool type.
- HITL routing.
- retry/repair routing.
- escalation after maximum retries.

### Why
Control-flow decisions should be independently testable.

### Official docs
- LangGraph conditional edges: https://docs.langchain.com/oss/python/langgraph/graph-api

---

## 12. `graph.py`

### Implemented
- `StateGraph`.
- nodes.
- `START` and `END`.
- conditional edges.
- `compile()`.

### Why
This is the orchestration layer connecting the agents.

### Official docs
- LangGraph Graph API: https://docs.langchain.com/oss/python/langgraph/graph-api

---

## 13. `cli.py`

### Implemented
- `@click.group()`.
- `@cli.command()`.
- `@click.argument()`.
- `@click.option()`.
- interactive REPL.
- execution summary.

### Why
CLI parsing should remain independent from agent internals.

### Official docs
- Click quickstart: https://click.palletsprojects.com/en/stable/quickstart/
- Click arguments: https://click.palletsprojects.com/en/stable/arguments/
- Click API: https://click.palletsprojects.com/en/stable/api/

---

## 14. `main.py`

### Implemented
- package entry point.
- `if __name__ == "__main__":`.

### Why
This is the smallest possible executable boundary.

### Official docs
- Python `__main__`: https://docs.python.org/3/library/__main__.html

---

# A documentation-first workflow for a fresher

For every unfamiliar API:

1. Identify the imported class/function.
2. Open its **official documentation**.
3. Read the signature and required parameters.
4. Read the smallest relevant example.
5. Identify the return type / object shape.
6. Compare the example with the project code.
7. Ask: **What problem is this API solving here?**
8. Only then modify or write the code.
9. Run a tiny isolated test.
10. Integrate it into the agent workflow.

Example:

```python
from langgraph.graph import StateGraph, START, END
```

Before writing this yourself, read the LangGraph Graph API and answer:

- What is `StateGraph`?
- What type of state does it expect?
- What does `add_node()` register?
- Why do we need `START`?
- What does `END` represent?
- When should `add_conditional_edges()` be used?

That process is the core skill this project is designed to teach.
