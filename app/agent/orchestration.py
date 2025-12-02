"""Agent Orchestrator logic."""

import logging

from langchain_core.runnables import RunnableConfig

from agent.graph_builder import GraphBuilder
from agent.nodes import ClassifierNode, GeneralNode, MedicalNode, ResponseNode
from config.state import SessionState
from core.llm import LLMClient
from memory.postgres import PostgresClient

LOGGER = logging.getLogger("agent")
LOGGER.setLevel(logging.INFO)


class Orchestrator:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.classifier_node = ClassifierNode(llm_client)
        self.general_node = GeneralNode(llm_client)
        self.medical_node = MedicalNode(llm_client)
        self.response_node = ResponseNode()

        self.graph_builder = GraphBuilder(self)
        self.graph = self.graph_builder.build()
        self.postgres_client = PostgresClient()

    def route_input(self, state: SessionState) -> str:
        """Route input based on is_medical.

        If is_medical is True, go directly to medical_agent.
        Otherwise, go to query_classification.
        """
        if state.is_medical:
            return "medical_agent"
        return "query_classification"

    def route_classification(self, state: SessionState) -> str:
        """Route based on classification result.

        If is_medical is True, go to medical_agent.
        Otherwise, go to general_agent.
        """
        return "medical_agent" if state.is_medical else "general_agent"

    async def load_state_memory(self, session_id: str) -> SessionState:
        await self.postgres_client.create_tables()
        state = await self.postgres_client.get_state(session_id)
        if state:
            return state
        return SessionState(session_id=session_id)

    async def save_state_memory(self, state: SessionState) -> None:
        await self.postgres_client.add_state(state)

    async def run(self, user_input, session_id) -> dict:
        config: RunnableConfig = {"configurable": {"thread_id": session_id}}
        state = await self.load_state_memory(session_id)
        state.user_input = user_input
        try:
            LOGGER.info("Orchestrator started.")

            state_dict = await self.graph.ainvoke(state.model_dump(), config, stream_mode="values")
            LOGGER.info("Orchestrator completed.")

            state_from_result = SessionState(**state_dict)
            await self.save_state_memory(state_from_result)

            return state_from_result.model_dump()

        except Exception as e:
            LOGGER.exception("Orchestrator failed.")
            raise RuntimeError(f"Orchestrator failed: {e}") from e
