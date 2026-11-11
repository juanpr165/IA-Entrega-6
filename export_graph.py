"""Exporta una imagen PNG del grafo LangGraph para la documentación."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))

from orchestrator import build_graph  # noqa: E402


def main() -> None:
    output = Path(__file__).parent / "artifacts" / "orchestrator-graph.png"
    output.parent.mkdir(exist_ok=True)
    graph_png = build_graph(with_memory=False).get_graph().draw_mermaid_png()
    output.write_bytes(graph_png)
    print(f"Diagrama exportado en: {output}")


if __name__ == "__main__":
    main()
