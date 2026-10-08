"""Pydantic schemas and LangGraph state.

Documentation:
- Pydantic models: https://docs.pydantic.dev/latest/concepts/models/
- Pydantic Field: https://docs.pydantic.dev/latest/concepts/fields/
- Python TypedDict: https://docs.python.org/3/library/typing.html#typing.TypedDict
- Python Annotated: https://docs.python.org/3/library/typing.html#typing.Annotated
- LangGraph state concepts: https://docs.langchain.com/oss/python/langgraph/graph-api

Why:
The original script uses structured LLM output. Pydantic models make those
outputs explicit, validated, and easier to pass between agent nodes.
"""

from __future__ import annotations

from operator import add
from typing import Annotated, Dict, List, Literal, Optional, TypedDict

from pydantic import BaseModel, Field


class ToolArg(BaseModel):
    file_path: Optional[str] = Field(None, description="File path for the tool argument")
    command: Optional[str] = Field(None, description="Command to be executed")


class PlanStep(BaseModel):
    step_id: int = Field(..., description="Step id starting from 1")
    file_name: str = Field(..., description="File name of step")
    description: str = Field(..., description="Step description")
    tool_name: Literal["write_file", "run_command"] = Field(..., description="Tool to use")
    tool_args: ToolArg
    expected_outcome: str = Field(..., description="Expected outcome after step")
    is_incremental: bool = Field(
        False,
        description="True when this step modifies an existing file rather than creating a new one",
    )


class ExecutionPlan(BaseModel):
    goal: str = Field(..., description="Goal of the execution plan")
    steps: List[PlanStep] = Field(..., description="Ordered list of execution steps")


class SingleFile(BaseModel):
    file_name: str = Field(..., description="File name of generated code/content")
    content: str = Field(..., description="Full content of the file")


class IncrementalPatch(BaseModel):
    file_name: str = Field(..., description="File to patch")
    search_block: str = Field(..., description="Exact block to find and replace")
    replace_block: str = Field(..., description="Replacement block")
    reason: str = Field(..., description="Why this change is needed")


class ExecutionResult(BaseModel):
    status: Literal["success", "failure"] = Field(..., description="Execution status")
    stdout: Optional[str] = Field(None)
    stderr: Optional[str] = Field(None)
    retry_count: int = Field(0)


class AgentState(TypedDict):
    idea: str
    plan: ExecutionPlan
    generated_code: Optional[Annotated[List[Dict[str, str]], add]]
    execution_result: Optional[ExecutionResult]
    current_step_idx: int
    current_step_error: Optional[str]
    retry_count: int
    hitl_approved: Optional[bool]
    execution_history: Annotated[List[Dict], add]
    is_update_request: bool
