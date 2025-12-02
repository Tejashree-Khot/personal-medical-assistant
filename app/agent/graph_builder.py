"""LangGraph orchestration graph builder."""

from typing import TYPE_CHECKING

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from config.state import SessionState

if TYPE_CHECKING:
    from agents.orchestration import Orchestrator


class GraphBuilder:
    """Builds the LangGraph state graph structure."""

    def __init__(self, orchestrator: "Orchestrator") -> None:
        """Initialize the graph builder.

        Args:
            orchestrator: The orchestrator instance containing nodes and handlers.
        """
        self.orchestrator = orchestrator

    def build(self) -> CompiledStateGraph:
        """Build and compile the LangGraph state graph.

        Returns:
            Compiled LangGraph instance with checkpointing enabled.
        """
        memory = MemorySaver()
        graph = StateGraph(SessionState)
        self.add_nodes(graph)
        self.add_edges(graph)
        self.add_conditional_edges(graph)
        return graph.compile(checkpointer=memory)

    def add_nodes(self, graph: StateGraph) -> None:
        """Add all nodes to the graph.

        Args:
            graph: The StateGraph instance.
        """
        graph.add_node("query_classification", self.orchestrator.classifier_node.run)
        graph.add_node("medical_agent", self.orchestrator.medical_node.run)
        graph.add_node("general_agent", self.orchestrator.general_node.run)
        graph.add_node("response", self.orchestrator.response_node.run)

    def add_edges(self, graph: StateGraph) -> None:
        """Add static edges to the graph.

        Args:
            graph: The StateGraph instance.
        """
        graph.add_edge("general_agent", "response")
        graph.add_edge("medical_agent", "response")
        graph.add_edge("response", END)

    def add_conditional_edges(self, graph: StateGraph) -> None:
        """Add conditional edges with routing logic to the graph.

        Args:
            graph: The StateGraph instance.
        """
        graph.add_conditional_edges(
            START,
            self.orchestrator.route_input,
            {"query_classification": "query_classification", "medical_agent": "medical_agent"},
        )

        graph.add_conditional_edges(
            "query_classification",
            self.orchestrator.route_classification,
            {"general_agent": "general_agent", "medical_agent": "medical_agent"},
        )
