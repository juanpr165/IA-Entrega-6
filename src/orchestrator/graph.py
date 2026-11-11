"""Construcción del grafo jerárquico LangGraph."""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from .agents import analyst_node, final_node, research_node, supervisor_node
from .state import OrchestratorState


def route_from_supervisor(state: OrchestratorState) -> str:
    return state["next_agent"]


def build_graph(with_memory: bool = True):
    graph = StateGraph(OrchestratorState)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("research", research_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("final", final_node)
    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges("supervisor", route_from_supervisor, {"research": "research", "analyst": "analyst", "final": "final"})
    graph.add_edge("research", "supervisor")
    graph.add_edge("analyst", "supervisor")
    graph.add_edge("final", END)
    return graph.compile(checkpointer=MemorySaver() if with_memory else None)
