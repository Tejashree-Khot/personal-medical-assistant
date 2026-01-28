import sys
from pathlib import Path

# add the app directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent / "app"))

from agent.dependencies import get_orchestrator

if __name__ == "__main__":
    orchestrator = get_orchestrator()
    graph = orchestrator.graph
    mermaid_code = graph.get_graph().draw_mermaid()
    with open("orchestration_graph.md", "w") as f:
        f.write("```mermaid\n")
        f.write(mermaid_code)
        f.write("\n```")
    print("Orchestration graph saved to orchestration_graph.md")
