"""Contrato de información que todos los nodos comparten."""

from __future__ import annotations

from typing import Literal, TypedDict

from langgraph.graph import MessagesState

Route = Literal["research", "analyst", "final"]


class OrchestratorState(MessagesState):
    """Estado serializable: MessagesState + trazabilidad del orquestador."""

    user_request: str
    next_agent: Route
    task_completed: bool
    iteration: int
    research_results: list[dict[str, str]]
    analysis_results: list[dict[str, str]]
    routing_history: list[dict[str, str]]
    final_answer: str
