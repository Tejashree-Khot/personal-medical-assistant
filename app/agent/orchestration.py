"""Agent Orchestrator logic."""

import logging
from typing import TYPE_CHECKING

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime

if TYPE_CHECKING:
    from config.state import UserProfile

from agent.graph_builder import GraphBuilder
from agent.graph_edges import Edges
from app.agent.graph_nodes import Nodes
from app.utils.logger import configure_logging
from config.state import Context, SessionState, UserProfile
from core.llm import LLMClient
from memory.postgres import PostgresClient

configure_logging()
LOGGER = logging.getLogger("agent")
LOGGER.setLevel(logging.INFO)


class Orchestrator:
    def __init__(self, llm_client: LLMClient, postgres_client: PostgresClient):
        self.llm_client = llm_client
        self.postgres_client = postgres_client
        self.nodes = Nodes(llm_client)
        self.edges = Edges()

        self.graph_builder = GraphBuilder(self)
        self.graph = self.graph_builder.build()

    async def load_state_memory(self, session_id: str) -> SessionState:
        """Load state memory from Postgres."""
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
            context = Context()
            state_dict = await self.graph.ainvoke(
                state.model_dump(), config, runtime=Runtime(context=context), stream_mode="values"
            )
            LOGGER.info("Orchestrator completed.")

            state_from_result = SessionState(**state_dict)
            await self.save_state_memory(state_from_result)
            await self.save_user_profile(state.user_profile)

            return state_from_result.model_dump()

        except Exception as e:
            LOGGER.exception("Orchestrator failed.")
            raise RuntimeError(f"Orchestrator failed: {e}") from e


if __name__ == "__main__":
    orchestrator = Orchestrator(LLMClient())
    graph = orchestrator.graph
    mermaid_code = graph.get_graph().draw_mermaid()
    print(mermaid_code)
