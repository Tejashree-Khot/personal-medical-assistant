"""LangGraph orchestration graph builder."""

from typing import TYPE_CHECKING

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from config.state import SessionState

if TYPE_CHECKING:
    from agent.orchestration import Orchestrator


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
        self._add_nodes(graph)
        self._add_edges(graph)
        self._add_conditional_edges(graph)
        return graph.compile(checkpointer=memory)

    def _add_nodes(self, graph: StateGraph) -> None:
        """Add all nodes to the graph.

        Args:
            graph: The StateGraph instance.
        """
        graph.add_node("input_guardrail", self.orchestrator.nodes.input_guardrail)
        graph.add_node("response", self.orchestrator.nodes.response)
        graph.add_node("load_profile", self.orchestrator.nodes.load_profile)
        graph.add_node("general_agent", self.orchestrator.nodes.general_agent)
        graph.add_node("medical_supervisor", self.orchestrator.nodes.medical_supervisor)
        graph.add_node("ensure_details", self.orchestrator.nodes.ensure_details)
        graph.add_node("ancient_knowledge", self.orchestrator.nodes.ancient_knowledge)
        graph.add_node("allopathy_agent", self.orchestrator.nodes.allopathy_agent)
        graph.add_node("tcm_kampo_agent", self.orchestrator.nodes.tcm_kampo_agent)
        graph.add_node("ayurveda_agent", self.orchestrator.nodes.ayurveda_agent)
        graph.add_node("lifestyle_agent", self.orchestrator.nodes.lifestyle_agent)
        graph.add_node("synthesis_node", self.orchestrator.nodes.synthesis_node)
        graph.add_node("contraindication_check", self.orchestrator.nodes.contraindication_check)
        graph.add_node("adjustment_node", self.orchestrator.nodes.adjustment_node)
        graph.add_node("response_generator", self.orchestrator.nodes.response_generator)
        graph.add_node("profile_extractor", self.orchestrator.nodes.profile_extractor)

    def _add_edges(self, graph: StateGraph) -> None:
        """Add static edges to the graph.

        Args:
            graph: The StateGraph instance.
        """
        graph.add_edge(START, "input_guardrail")
        graph.add_edge("load_profile", "ensure_details")

        graph.add_edge("ancient_knowledge", "allopathy_agent")
        graph.add_edge("ancient_knowledge", "tcm_kampo_agent")
        graph.add_edge("ancient_knowledge", "ayurveda_agent")
        graph.add_edge("ancient_knowledge", "lifestyle_agent")
        graph.add_edge("allopathy_agent", "synthesis_node")
        graph.add_edge("tcm_kampo_agent", "synthesis_node")
        graph.add_edge("ayurveda_agent", "synthesis_node")
        graph.add_edge("lifestyle_agent", "synthesis_node")
        graph.add_edge("synthesis_node", "contraindication_check")
        graph.add_edge("contraindication_check", "adjustment_node")
        graph.add_edge("adjustment_node", "response_generator")
        graph.add_edge("response_generator", "profile_extractor")
        graph.add_edge("profile_extractor", "response")
        graph.add_edge("general_agent", "response")
        graph.add_edge("response", END)

    def _add_conditional_edges(self, graph: StateGraph) -> None:
        """Add conditional edges with routing logic to the graph.

        Args:
            graph: The StateGraph instance.
        """
        graph.add_conditional_edges(
            "input_guardrail",
            self.orchestrator.edges.route_input_guardrail,
            {
                "response": "response",
                "load_profile": "load_profile",
                "general_agent": "general_agent",
            },
        )
        graph.add_conditional_edges(
            "ensure_details",
            self.orchestrator.edges.route_ensure_details,
            {"medical_supervisor": "medical_supervisor", "response": "response"},
        )

        graph.add_conditional_edges(
            "medical_supervisor",
            self.orchestrator.edges.route_medical_supervisor,
            {"response": "response", "ancient_knowledge": "ancient_knowledge"},
        )

        graph.add_conditional_edges(
            "contraindication_check",
            self.orchestrator.edges.route_contraindication_check,
            {"adjustment_node": "adjustment_node", "response_generator": "response_generator"},
        )
