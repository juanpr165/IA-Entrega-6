"""Nodos especializados y decisiones del Supervisor."""

from __future__ import annotations

import os
import re
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from .state import OrchestratorState, Route
from .tools import safe_calculate, sentiment_analysis, web_search


class SupervisorDecision(BaseModel):
    next_agent: Literal["research", "analyst", "final"] = Field(description="Siguiente nodo")
    reason: str = Field(description="Motivo breve de la decisión")


def get_llm() -> ChatGroq:
    """Único constructor de LLM: Groq."""
    return ChatGroq(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY"),
    )


def _requires_research(request: str) -> bool:
    terms = ("investig", "busc", "fuente", "actual", "noticia", "impacto", "compar", "tendencia")
    return any(term in request.lower() for term in terms)


def _requires_analysis(request: str) -> bool:
    terms = ("calcul", "porcentaje", "sentimiento", "analiz", "valid", "promedio", "variación")
    return any(term in request.lower() for term in terms)


def deterministic_route(state: OrchestratorState, max_iterations: int) -> tuple[Route | None, str]:
    """Guardas deterministas, fáciles de probar, previas al criterio del LLM."""
    if state.get("iteration", 0) >= max_iterations:
        return "final", "Límite de iteraciones alcanzado."
    request = state["user_request"]
    if _requires_research(request) and not state.get("research_results"):
        return "research", "Faltan fuentes para la solicitud."
    if _requires_analysis(request) and not state.get("analysis_results"):
        return "analyst", "Falta el procesamiento especializado solicitado."
    if state.get("research_results") or state.get("analysis_results"):
        return "final", "Los aportes requeridos ya están presentes."
    return None, "El LLM decide el siguiente paso."


def supervisor_node(state: OrchestratorState) -> dict:
    max_iterations = int(os.getenv("MAX_ITERATIONS", "6"))
    guarded_route, reason = deterministic_route(state, max_iterations)
    if guarded_route:
        route = guarded_route
    else:
        prompt = (
            "Sos un supervisor de un equipo. Elegí research si hacen falta fuentes externas; "
            "analyst si hacen falta cálculo, sentimiento o validación; final si ya podés responder. "
            "No repitas agentes que ya aportaron."
        )
        try:
            decision = get_llm().with_structured_output(SupervisorDecision).invoke([
                SystemMessage(content=prompt),
                HumanMessage(content=f"Solicitud: {state['user_request']}\nEstado: research={bool(state.get('research_results'))}, analyst={bool(state.get('analysis_results'))}"),
            ])
            route, reason = decision.next_agent, decision.reason
        except Exception as exc:
            route, reason = "final", f"Fallback ante indisponibilidad del supervisor: {exc}"
    return {
        "next_agent": route,
        "iteration": state.get("iteration", 0) + 1,
        "routing_history": state.get("routing_history", []) + [{"route": route, "reason": reason}],
    }


def research_node(state: OrchestratorState) -> dict:
    sources = web_search(state["user_request"])
    return {
        "research_results": sources,
        "messages": [AIMessage(content=f"Investigación completada: {len(sources)} fuente(s) recopilada(s).", name="research")],
    }


def analyst_node(state: OrchestratorState) -> dict:
    request = state["user_request"]
    results: list[dict[str, str]] = []
    math_match = re.search(r"(?:calcul[áa]|resolver)?\s*([\d\s+*/().,^%-]+)", request, re.IGNORECASE)
    if math_match and any(char.isdigit() for char in math_match.group(1)):
        expression = math_match.group(1).strip().replace("^", "**")
        results.append({"tool": "safe_calculate", "input": expression, "output": safe_calculate(expression)})
    if "porcentual" in request.lower() or "variación" in request.lower():
        numbers = [float(x.replace(",", ".")) for x in re.findall(r"\d+(?:[,.]\d+)?", request)]
        if len(numbers) >= 2 and numbers[0] != 0:
            value = (numbers[1] - numbers[0]) / numbers[0] * 100
            results.append({"tool": "percentage_change", "input": f"{numbers[0]} → {numbers[1]}", "output": f"{value:.2f}%"})
    if "sentimiento" in request.lower() or "sentiment" in request.lower():
        results.append({"tool": "sentiment_analysis", "input": request, "output": str(sentiment_analysis(request))})
    if not results:
        results.append({"tool": "analysis", "input": request, "output": "No se detectó una operación específica; se revisó la consistencia de la solicitud."})
    return {"analysis_results": results, "messages": [AIMessage(content="Análisis especializado completado.", name="analyst")]}


def final_node(state: OrchestratorState) -> dict:
    evidence = f"Fuentes: {state.get('research_results', [])}\nAnálisis: {state.get('analysis_results', [])}"
    prompt = "Respondé en español de forma clara. Usá sólo la evidencia entregada; citá URLs si existen y reconocé límites."
    try:
        answer = get_llm().invoke([SystemMessage(content=prompt), HumanMessage(content=f"Solicitud: {state['user_request']}\n{evidence}")]).content
    except Exception:
        lines = [f"Respuesta para: {state['user_request']}"]
        if state.get("research_results"):
            lines.append("Fuentes consultadas:")
            lines.extend(f"- {item['title']}: {item['url']}" for item in state["research_results"])
        if state.get("analysis_results"):
            lines.append("Análisis: " + "; ".join(item["output"] for item in state["analysis_results"]))
        answer = "\n".join(lines)
    return {"final_answer": str(answer), "task_completed": True, "messages": [AIMessage(content=str(answer), name="final")]}
