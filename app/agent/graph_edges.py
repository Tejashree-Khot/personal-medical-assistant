"""Agent Orchestrator logic."""

import logging
from typing import TYPE_CHECKING

from langgraph.types import Send

if TYPE_CHECKING:
    pass

from config.state import SessionState
from utils.logger import configure_logging

configure_logging()
LOGGER = logging.getLogger("agent_edges")
LOGGER.setLevel(logging.INFO)


class ConditionalEdges:
    """Container for all edge routing functions."""

    @staticmethod
    def route_input_guardrail(state: SessionState) -> str:
        """Route based on medical agent check.

        If medical query, go to medical_agent.
        Otherwise, go to general_agent.
        """
        if state.is_medical:
            return "medical_agent"
        else:
            return "general_agent"

    @staticmethod
    def route_medical_agent(state: SessionState) -> str:
        """Route based on medical agent check.

        If emergency detected, go to emergency_response.
        Otherwise, go to ensure_details.
        """
        if state.is_emergency:
            return "emergency_response"
        else:
            return "ensure_details"

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
