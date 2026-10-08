"""LangGraph workflow construction.

Documentation:
- StateGraph: https://docs.langchain.com/oss/python/langgraph/graph-api
- START/END and conditional edges: https://docs.langchain.com/oss/python/langgraph/graph-api

Why:
The graph is the orchestration layer: Planner → Writer/HITL/Executor → Repair
and retry routing.
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .executor import executor, hitl_gate
from .models import AgentState
from .planner import planner
from .repair import repair
from .routing import post_executor_router, post_hitl_router, post_repair_router, router
from .writer import writer


def build_graph() -> StateGraph:
    builder = StateGraph(AgentState)

    builder.add_node("planner", planner)
    builder.add_node("writer", writer)
    builder.add_node("hitl_gate", hitl_gate)
    builder.add_node("executor", executor)
    builder.add_node("repair", repair)

    builder.add_edge(START, "planner")

    choices = {
        "writer": "writer",
        "executor": "executor",
        "hitl_gate": "hitl_gate",
        "__end__": END,
    }

    builder.add_conditional_edges("planner", router, choices)
    builder.add_conditional_edges("writer", router, choices)
    builder.add_conditional_edges("hitl_gate", post_hitl_router, {**choices, "executor": "executor"})
    builder.add_conditional_edges(
        "executor",
        post_executor_router,
        {**choices, "repair": "repair", "executor": "executor"},
    )
    builder.add_conditional_edges("repair", post_repair_router, {"executor": "executor"})

    return builder.compile()


GRAPH = build_graph()
