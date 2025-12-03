"""Agent Orchestrator logic."""

import logging

from langchain_core.runnables import RunnableConfig
from langgraph.types import Send

from agent.graph_builder import GraphBuilder
from agent.nodes import (
    AdjustmentNode,
    AllopathyAgentNode,
    AncientKnowledgeNode,
    AyurvedaAgentNode,
    ContraindicationCheckNode,
    EnsureDetailsNode,
    GeneralAgentNode,
    InputGuardrailNode,
    LifestyleAgentNode,
    LoadProfileNode,
    MedicalSupervisorNode,
    ProfileExtractorNode,
    ResponseGeneratorNode,
    ResponseNode,
    SynthesisNode,
    TCMKampoAgentNode,
)
from config.state import SessionState
from core.llm import LLMClient
from memory.postgres import PostgresClient

LOGGER = logging.getLogger("agent")
LOGGER.setLevel(logging.INFO)


class Nodes:
    """Container for all orchestration nodes."""

    def __init__(self, llm_client: LLMClient) -> None:
        self.input_guardrail = InputGuardrailNode(llm_client).run
        self.response = ResponseNode().run
        self.general_agent = GeneralAgentNode(llm_client).run
        self.load_profile = LoadProfileNode().run
        self.ensure_details = EnsureDetailsNode(llm_client).run
        self.ancient_knowledge = AncientKnowledgeNode(llm_client).run
        self.medical_supervisor = MedicalSupervisorNode(llm_client).run
        self.allopathy_agent = AllopathyAgentNode(llm_client).run
        self.tcm_kampo_agent = TCMKampoAgentNode(llm_client).run
        self.ayurveda_agent = AyurvedaAgentNode(llm_client).run
        self.lifestyle_agent = LifestyleAgentNode(llm_client).run
        self.synthesis_node = SynthesisNode(llm_client).run
        self.contraindication_check = ContraindicationCheckNode(llm_client).run
        self.adjustment_node = AdjustmentNode(llm_client).run
        self.response_generator = ResponseGeneratorNode(llm_client).run
        self.profile_extractor = ProfileExtractorNode(llm_client).run


class Edges:
    """Container for all edge routing functions."""

    @staticmethod
    def route_input_guardrail(state: SessionState) -> str:
        """Route based on input guardrail check.

        If emergency detected, go to response_node.
        Otherwise, go to load_profile.
        """
        if state.is_emergency:
            return "response"
        elif state.is_medical:
            return "load_profile"
        else:
            return "general_agent"

    @staticmethod
    def route_ensure_details(state: SessionState) -> str:
        """Route based on ensure details classification.

        If sufficient details, go to medical_supervisor.
        Otherwise, go to response.
        """
        if state.has_sufficient_details:
            return "medical_supervisor"
        return "response"

    @staticmethod
    def route_medical_supervisor(state: SessionState) -> str | list[Send]:
        """Route based on medical supervisor decision.

        If needs clarification, go to response.
        Otherwise, trigger parallel execution of all specialist agents.
        """
        if state.needs_ancient_knowledge:
            return "ancient_knowledge"
        return "response"

    @staticmethod
    def route_contraindication_check(state: SessionState) -> str:
        """Route based on contraindication check.

        If contraindications detected, go to adjustment_node.
        Otherwise, go to response_generator.
        """
        if state.has_contraindications:
            return "adjustment_node"
        return "response_generator"


class Orchestrator:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.nodes = Nodes(llm_client)
        self.edges = Edges()

        self.graph_builder = GraphBuilder(self)
        self.graph = self.graph_builder.build()
        self.postgres_client = PostgresClient()

    async def load_state_memory(self, session_id: str) -> SessionState:
        await self.postgres_client.create_tables()
        state = await self.postgres_client.get_state(session_id)
        if state:
            return state
        return SessionState(session_id=session_id)

    async def save_state_memory(self, state: SessionState) -> None:
        await self.postgres_client.add_state(state)

    async def run(self, session_id, user_id, user_input) -> dict:
        config: RunnableConfig = {"configurable": {"thread_id": session_id}}
        state = await self.load_state_memory(session_id)
        state.user_input = user_input
        state.user_id = user_id
        try:
            LOGGER.info("Orchestrator started.")

            # graph_context = GraphContext()
            state_dict = await self.graph.ainvoke(state.model_dump(), config, stream_mode="values")
            LOGGER.info("Orchestrator completed.")

            state_from_result = SessionState(**state_dict)
            await self.save_state_memory(state_from_result)

            return state_from_result.model_dump()

        except Exception as e:
            LOGGER.exception("Orchestrator failed.")
            raise RuntimeError(f"Orchestrator failed: {e}") from e


if __name__ == "__main__":
    orchestrator = Orchestrator(LLMClient())
    graph = orchestrator.graph
    mermaid_code = graph.get_graph().draw_mermaid()
    print(mermaid_code)
