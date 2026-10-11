# Autonomous Coder Agent

## Project Overview

Autonomous Coder Agent is an AI-powered software development system built with LangGraph and LangChain. It converts plain-English instructions into structured development tasks, generates code, executes commands, and attempts to fix errors automatically.

This project is the modular version of the original single-file implementation. The code is separated into individual Python modules to make the system easier to understand, test, maintain, and extend.

For example, a user can request a FastAPI application with a todo API. The agent creates an execution plan, generates the required files, runs commands, and attempts to resolve errors encountered during execution.

The system also includes human approval for sensitive commands, incremental code editing, execution history, and real-time terminal output.

## Architecture

The application uses LangGraph to coordinate the agents and manage the execution workflow.

```text
main.py
   |
   v
cli.py
   |
   v
graph.py
   |
   v
planner.py
   |
   v
routing.py
   |
   +-----------> writer.py
   |
   +-----------> hitl_gate
   |                 |
   |                 v
   |             executor.py
   |                 |
   |          +------+------+
   |          |             |
   |        Success       Failure
   |          |             |
   |          v             v
   |        Router       repair.py
   |                        |
   +------------------------+
```

The graph coordinates planning, code generation, command execution, approval checks, and error recovery. The routing logic determines which node should execute next based on the current step and execution result.

Supporting modules provide shared state models, LLM configuration, security checks, code patching, and terminal presentation.

## Project Structure

```text
autonomous-coder-agent/
|
|-- autonomous_coder_agent/
|   |-- __init__.py
|   |-- __main__.py
|   |-- main.py
|   |-- cli.py
|   |-- graph.py
|   |-- planner.py
|   |-- writer.py
|   |-- executor.py
|   |-- repair.py
|   |-- hitl_gate.py
|   |-- models.py
|   |-- config.py
|   |-- security.py
|   |-- patching.py
|   |-- ui.py
|   |-- llm.py
|   |-- routing.py
|
|-- tests/
|-- .env.example
|-- .gitignore
|-- requirements.txt
|-- DOCUMENTATION_MAP.md
|-- README.md
```

The exact directory structure should match the files in the repository. The layout above illustrates the intended modular organization.

## Module Responsibilities

### main.py

Provides the application's main entry point and connects the command-line interface to the application workflow.

### cli.py

Defines the CLI commands for running a single development task or starting an interactive session. Click is used to handle command arguments and options.

### graph.py

Builds and compiles the LangGraph state graph. It defines the nodes, edges, conditional routing, and execution flow.

### planner.py

Uses an LLM to convert the user's request into an ordered execution plan. Each step describes the action, target file or command, and expected result.

### writer.py

Generates source files and modifies existing code. It supports complete file generation and incremental changes when updating an existing project.

### executor.py

Runs approved shell commands, captures standard output and standard error, and applies execution time limits.

### repair.py

Analyzes execution failures and attempts to correct the relevant code. The workflow can retry failed operations until the configured retry limit is reached.

### hitl_gate.py

Requests user approval before executing commands classified as sensitive. Approval decisions are recorded in the execution history.

### models.py

Defines the Pydantic models used for structured LLM outputs and the TypedDict state shared by the agents.

### config.py

Loads environment variables and provides configuration for the LLM provider, model selection, logging, and execution settings.

### security.py

Classifies potentially sensitive commands and identifies operations that must be blocked or reviewed before execution.

### patching.py

Implements incremental search-and-replace patches, fallback matching, and unified diff generation.

### ui.py

Provides the terminal interface using Rich, including agent status messages, execution output, code previews, and summaries.

### llm.py

Initializes the LLM clients and configures structured-output interfaces for planning, writing, patching, and repair.

### routing.py

Contains the routing rules that determine which node should handle the current step and what should happen after execution succeeds or fails.

## Key Features

### Multi-Agent Code Generation

The planner, writer, executor, and repair components work together to automate software development tasks. LangGraph manages their execution through a shared state and conditional transitions.

### Automatic Error Recovery

When a command fails, the system captures the error details and sends them to the repair agent. The repair agent attempts to correct the relevant code, after which the workflow can retry the operation.

The maximum number of retries is configurable. If the agent cannot resolve the issue, it can escalate the failure to the user.

### Human Approval and Command Safety

Potentially sensitive commands, including operations involving elevated privileges, file deletion, external network access, and remote repository changes, can require explicit approval.

Certain dangerous operations can be blocked before they reach the approval stage.

The security module provides a foundation for command risk classification. A production deployment should additionally use isolated execution environments, strict workspace restrictions, and least-privilege permissions.

### Incremental Code Editing

For requests such as fixing an import, changing a function, or modifying a UI component, the writer attempts to update only the necessary section of a file.

The patching module applies search-and-replace changes and can use fuzzy matching when the original code block does not match exactly. A unified diff helps developers review the modifications.

### Real-Time Terminal Output

Rich provides readable terminal output for agent activity, command execution, error messages, and final summaries.

LangGraph streaming can expose node updates as the workflow progresses, helping users understand which steps have completed.

### Execution History

The shared state maintains an execution history containing events such as planning, file creation, command execution, repair attempts, and approval decisions.

This history helps developers inspect the workflow and troubleshoot failures.

## Technology Stack

Python 3.11 or later is used for the application.

LangGraph manages agent orchestration and state transitions. LangChain provides the LLM integration, while langchain-groq connects the system to supported Groq models.

Pydantic v2 handles structured data validation. Rich provides terminal formatting, Click manages the CLI, and python-dotenv loads configuration from environment variables.

Pytest can be used to test individual modules, routing decisions, command classification, patching behavior, and end-to-end workflows.

## Installation and Setup

### Prerequisites

Install Python 3.11 or later and obtain an API key from a supported Groq account.

Clone the repository and move into the project directory.

```bash
git clone https://github.com/your-username/autonomous-coder-agent.git
cd autonomous-coder-agent
```

Create a virtual environment.

```bash
python -m venv .venv
```

Activate it on Windows.

```powershell
.venv\Scripts\Activate.ps1
```

On macOS or Linux, run:

```bash
source .venv/bin/activate
```

Install the project dependencies.

```bash
pip install -r requirements.txt
```

Create a local environment file from the example.

On Windows:

```powershell
Copy-Item .env.example .env
```

On macOS or Linux:

```bash
cp .env.example .env
```

Add your configuration to the .env file.

```dotenv
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

Use a model identifier supported by your provider and account. Never commit API keys or other secrets to a public repository.

## Running the Application

Run a development task from the command line.

```bash
python -m autonomous_coder_agent run "Build a FastAPI todo API"
```

Start an interactive session.

```bash
python -m autonomous_coder_agent interactive
```

Check the available options.

```bash
python -m autonomous_coder_agent run --help
```

These commands assume that the package entry points and Click commands are implemented as shown. The actual commands should be verified against the repository.

## Documentation-First Learning

The project includes a DOCUMENTATION_MAP.md file that connects each module to the official documentation for the Python language and the frameworks used.

The purpose is to understand the underlying concepts before changing the implementation.

Developers can use this guide to study Python type annotations, Pydantic models, LangGraph state management, conditional routing, LangChain structured outputs, subprocess execution, command-line interfaces, and automated testing.

This approach makes it easier to understand why a particular design was chosen instead of simply copying code from an existing implementation.

## Important Engineering Note

The modular version changes the execution behavior of the original implementation.

In the original monolithic version, the run workflow streamed the graph and then invoked the graph again to retrieve the final merged state. The modular version is designed to obtain the execution results from a single graph invocation.

This avoids unintentionally running the same development task twice. However, the single-invocation approach must correctly accumulate the state updates produced by the graph. The final state should be verified through tests, particularly when streaming updates and reducer-based fields are involved.

## Testing and Reliability

Before using the agent on important projects, test the individual modules and their interactions.

Important test cases include successful file creation, failed command recovery, retry limits, approval rejection, blocked commands, incremental patches, and final state accumulation.

Also test timeouts, malformed LLM responses, missing environment variables, permission errors, and attempts to modify files outside the intended workspace.

Shell commands generated by an LLM should never be considered safe merely because they appear in a valid execution plan. Command validation, workspace isolation, and restricted permissions are important parts of a reliable implementation.

## Future Improvements

The project can be extended with automated unit-test generation, Docker-based sandbox execution, persistent project memory, support for additional LLM providers, and improved observability.

Other useful improvements include structured logs, resumable workflows, test-driven repair, code quality checks, and a web-based interface for reviewing proposed changes and approving sensitive operations.

## Conclusion

Autonomous Coder Agent demonstrates how multi-agent AI workflows can automate practical software development tasks.

The modular architecture separates planning, writing, execution, repair, security, and user interaction into focused components. This improves maintainability and creates a clearer foundation for testing and future development.

By combining LangGraph, LangChain, structured outputs, incremental code editing, automated recovery, and human approval, the project provides a practical learning and engineering foundation for building autonomous coding systems.
