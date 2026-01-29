"""Dependency injection for singleton instances."""

from functools import lru_cache

from agent.orchestration import Orchestrator
from agent.profile_extractor import ProfileExtractor
from core.llm import LLMClient
from memory.postgres import PostgresClient


@lru_cache
def get_llm_client() -> LLMClient:
    """Get the single shared LLMClient instance."""
    return LLMClient()


@lru_cache
def get_postgres_client() -> PostgresClient:
    """Get the single shared PostgresClient instance."""
    return PostgresClient()


@lru_cache
def get_orchestrator() -> Orchestrator:
    """Get the single shared Orchestrator instance.

    This ensures that the same Orchestrator instance (with its MemorySaver checkpointer)
    is reused across requests, allowing session state to persist.
    """
    return Orchestrator(llm_client=get_llm_client(), postgres_client=get_postgres_client())


@lru_cache
def get_profile_extractor() -> ProfileExtractor:
    """Get the single shared ProfileExtractor instance."""
    return ProfileExtractor(llm_client=get_llm_client(), postgres_client=get_postgres_client())
