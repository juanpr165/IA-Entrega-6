"""Demo ejecutable del orquestador."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent / "src"))
from orchestrator import build_graph  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Demo del orquestador multi-agente con Groq")
    parser.add_argument("request", help="Consulta que requiere investigación y/o análisis")
    parser.add_argument("--thread-id", default="demo", help="Identificador para persistencia en memoria")
    args = parser.parse_args()
    load_dotenv()
    app = build_graph(with_memory=True)
    initial_state = {
        "user_request": args.request, "messages": [], "iteration": 0,
        "research_results": [], "analysis_results": [], "routing_history": [], "task_completed": False,
    }
    result = app.invoke(initial_state, config={"configurable": {"thread_id": args.thread_id}})
    print("\n=== RESPUESTA FINAL ===\n")
    print(result["final_answer"])
    print("\n=== TRAZABILIDAD ===")
    for step in result["routing_history"]:
        print(f"- {step['route']}: {step['reason']}")


if __name__ == "__main__":
    main()
