"""Agent Orchestrator logic."""

import asyncio
import logging
from typing import TYPE_CHECKING

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from langgraph.types import Send

if TYPE_CHECKING:
    from config.state import UserProfile

from agent.graph_builder import GraphBuilder
from agent.nodes import (
    AdjustmentNode,
    AllopathyAgentNode,
    AncientKnowledgeNode,
    AyurvedaAgentNode,
    ContraindicationCheckNode,
    EmergencyResponseNode,
    EnsureDetailsNode,
    GeneralAgentNode,
    InputGuardrailNode,
    LifestyleAgentNode,
    ProfileExtractorNode,
    ResponseGeneratorNode,
    ResponseNode,
    SynthesisNode,
    TCMKampoAgentNode,
)
from agent.utils import configure_logging
from config.state import Context, SessionState, UserProfile
from core.llm import LLMClient
from memory.postgres import PostgresClient

configure_logging()
LOGGER = logging.getLogger("agent")
LOGGER.setLevel(logging.INFO)


class Nodes:
    """Container for all orchestration nodes."""

    def __init__(self, llm_client: LLMClient) -> None:
        self.input_guardrail = InputGuardrailNode(llm_client).run
        self.emergency_response = EmergencyResponseNode(llm_client).run
        self.response = ResponseNode().run
        self.general_agent = GeneralAgentNode(llm_client).run
        self.ensure_details = EnsureDetailsNode(llm_client).run
        self.ancient_knowledge = AncientKnowledgeNode(llm_client).run
        self.allopathy_agent = AllopathyAgentNode(llm_client).run
        self.tcm_kampo_agent = TCMKampoAgentNode(llm_client).run
        self.ayurveda_agent = AyurvedaAgentNode(llm_client).run
        self.lifestyle_agent = LifestyleAgentNode(llm_client).run
        self.synthesis_node = SynthesisNode(llm_client).run
        self.contraindication_check = ContraindicationCheckNode(llm_client).run
        self.adjustment_node = AdjustmentNode(llm_client).run
        self.response_generator = ResponseGeneratorNode(llm_client).run
        self.response_generator = ResponseGeneratorNode(llm_client).run
        self.profile_extractor = ProfileExtractorNode(llm_client).run


class Edges:
    """Container for all edge routing functions."""

    @staticmethod
    def route_input_guardrail(state: SessionState) -> str:
        """Route based on input guardrail check.

        If emergency detected, go to response_node.
        Otherwise, go to profile_extractor.
        """
        if state.is_emergency:
            return "emergency_response"
        elif state.is_medical:
            return "ensure_details"
        else:
            return "general_agent"

    @staticmethod
    def route_ensure_details(state: SessionState) -> str:
        """Route based on ensure details classification.

        If sufficient details, go to ancient_knowledge_router.
        Otherwise, go to response.
        """
        if state.has_sufficient_details:
            return "ancient_knowledge_router"
        return "response"

    @staticmethod
    def route_ancient_knowledge_router(state: SessionState) -> str | list[Send]:
        """Route based on ancient knowledge router decision.

        If needs ancient knowledge, go to ancient_knowledge.
        Otherwise, go to response.
        """
        if state.gathered_ancient_knowledge:
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
        self.postgres_client = PostgresClient()
        self.nodes = Nodes(llm_client)
        self.edges = Edges()

        self.graph_builder = GraphBuilder(self)
        self.graph = self.graph_builder.build()

    async def load_state_memory(self, session_id: str) -> SessionState:
        """Load state memory from Postgres."""
        await self.postgres_client.create_tables()
        state = await self.postgres_client.get_state(session_id)
        if state:
            return state
        return SessionState(session_id=session_id)

    async def save_state_memory(self, state: SessionState) -> None:
        """Save state memory to Postgres."""
        await self.postgres_client.add_state(state)

    async def load_user_profile(self, user_id: str) -> UserProfile | None:
        """Load user profile from Postgres."""
        return await self.postgres_client.get_user_profile(user_id)

    async def save_user_profile(self, profile: UserProfile) -> None:
        """Save user profile to Postgres."""
        await self.postgres_client.save_user_profile(profile)

    async def run_profile_extraction_background(self, state: SessionState) -> None:
        """Run profile extraction in background."""
        try:
            # Create a copy to avoid side effects and clear response for input-only extraction
            extraction_state = state.model_copy(deep=True)

            LOGGER.info("Starting background profile extraction")
            state = await self.nodes.profile_extractor(extraction_state)
            LOGGER.info("Background profile extraction completed.")

            await self.save_user_profile(state.user_profile)
            LOGGER.info("Background profile extraction completed and saved.")

        except Exception as e:
            LOGGER.error(f"Background profile extraction failed: {e}")

    async def run(self, session_id: str, user_id: str, user_input: str) -> dict:
        """Run the orchestrator."""
        LOGGER.info("Orchestrator started.")
        config: RunnableConfig = {"configurable": {"thread_id": session_id}}
        state = await self.load_state_memory(session_id)
        LOGGER.info("Loaded state memory")
        state.user_input = user_input
        state.user_id = user_id

        user_profile = await self.load_user_profile(user_id)
        state.user_profile = user_profile or UserProfile(user_id=user_id)
        LOGGER.info("Loaded user profile")

        try:
            # Start background profile extraction
            LOGGER.info("Starting background profile extraction")
            asyncio.create_task(self.run_profile_extraction_background(state))

            context = Context()
            state_dict = await self.graph.ainvoke(
                state.model_dump(), config, runtime=Runtime(context=context), stream_mode="values"
            )
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
