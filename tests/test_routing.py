from orchestrator.agents import deterministic_route


def state(request: str, **extra):
    base = {"user_request": request, "iteration": 0, "research_results": [], "analysis_results": []}
    base.update(extra)
    return base


def test_research_before_analysis_when_both_are_needed():
    route, _ = deterministic_route(state("Investigá fuentes y calculá la variación porcentual"), 6)
    assert route == "research"


def test_analysis_after_research():
    route, _ = deterministic_route(state("Investigá fuentes y calculá la variación porcentual", research_results=[{}]), 6)
    assert route == "analyst"


def test_iteration_cap_finishes_flow():
    route, _ = deterministic_route(state("Investigá algo", iteration=6), 6)
    assert route == "final"
