"""LLM client construction.

Documentation:
- ChatGroq: https://docs.langchain.com/oss/python/integrations/chat/groq
- LangChain structured output: https://docs.langchain.com/oss/python/langchain/models
- LangChain messages: https://docs.langchain.com/oss/python/langchain/messages

Why:
Keeping model construction here avoids repeating provider configuration across
the planner, writer, patcher, and repair agents.
"""

from __future__ import annotations

from langchain_groq import ChatGroq

from .config import MODEL
from .models import ExecutionPlan, IncrementalPatch, SingleFile


plan_llm = ChatGroq(model=MODEL, temperature=0.2).with_structured_output(ExecutionPlan)
write_llm = ChatGroq(model=MODEL, temperature=0).with_structured_output(SingleFile)
patch_llm = ChatGroq(model=MODEL, temperature=0).with_structured_output(IncrementalPatch)
repair_llm = ChatGroq(model=MODEL, temperature=0.3).with_structured_output(SingleFile)
