"""Agent Orchestrator logic."""

import logging

from langchain_core.runnables import RunnableConfig

from agent.graph_builder import GraphBuilder
from agent.graph_edges import ConditionalEdges
from agent.graph_nodes import Nodes
from config.state import SessionState, UserProfile
from core.llm import LLMClient
from memory.postgres import PostgresClient
from utils.logger import configure_logging

configure_logging()
LOGGER = logging.getLogger("agent")
LOGGER.setLevel(logging.INFO)


class Orchestrator:
    def __init__(self, llm_client: LLMClient, postgres_client: PostgresClient):
        self.llm_client = llm_client
        self.postgres_client = postgres_client
        self.nodes = Nodes(llm_client)
        self.conditional_edges = ConditionalEdges()
        self.graph_builder = GraphBuilder(self)
        self.graph = self.graph_builder.build()

    async def load_state_memory(self, session_id: str) -> SessionState:
        """Load state memory from Postgres."""
        await self.postgres_client.create_tables()
        state = await self.postgres_client.get_state(session_id)
        state = state if state else SessionState(session_id=session_id)
        return state

    async def save_state_memory(self, state: SessionState) -> None:
        """Save state memory to Postgres."""
        await self.postgres_client.add_state(state)

    async def load_user_profile(self, user_id: str) -> UserProfile | None:
        """Load user profile from Postgres."""
        return await self.postgres_client.get_user_profile(user_id)

    async def save_user_profile(self, profile: UserProfile) -> None:
        """Save user profile to Postgres."""
        await self.postgres_client.save_user_profile(profile)

    async def run(self, session_id: str, user_id: str, user_input: str) -> dict:
        """Run the orchestrator."""
        LOGGER.info("Orchestrator started.")
        config: RunnableConfig = {"configurable": {"thread_id": session_id}}
        state = await self.load_state_memory(session_id)
        LOGGER.info("Loaded state memory")
        user_profile = await self.load_user_profile(user_id)
        LOGGER.info("Loaded user profile from database")

        state.user_input = user_input
        state.user_id = user_id
        state.user_profile = user_profile or UserProfile(user_id=user_id)

        try:
            state_dict = await self.graph.ainvoke(state.model_dump(), config, stream_mode="values")
            LOGGER.info("Orchestrator completed.")

            state_from_result = SessionState(**state_dict)
            await self.save_state_memory(state_from_result)
            if state_from_result.user_profile:
                await self.save_user_profile(state_from_result.user_profile)

            return state_from_result.model_dump()

        except Exception as e:
            LOGGER.exception("Orchestrator failed.")
            raise RuntimeError(f"Orchestrator failed: {e}") from e
