"""Dependency injection for singleton instances."""

from functools import lru_cache

from agent.orchestration import Orchestrator
from core.llm import LLMClient
from memory.postgres import PostgresClient


@lru_cache
def get_llm_client() -> LLMClient:
    """Get or create the singleton LLMClient instance.

    :return: The singleton LLMClient instance.
    """
    return LLMClient()


@lru_cache
def get_postgres_client() -> PostgresClient:
    """Get or create the singleton PostgresClient instance."""
    return PostgresClient()


@lru_cache
def get_orchestrator() -> Orchestrator:
    """Get or create the singleton Orchestrator instance.

    This ensures that the same Orchestrator instance (with its MemorySaver checkpointer)
    is reused across requests, allowing session state to persist.

    :return: The singleton Orchestrator instance.
    """
    return Orchestrator(llm_client=get_llm_client(), postgres_client=get_postgres_client())
