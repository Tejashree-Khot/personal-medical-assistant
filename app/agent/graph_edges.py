"""Agent Orchestrator logic."""

import logging
from typing import TYPE_CHECKING

from langgraph.types import Send

if TYPE_CHECKING:
    pass

from app.utils.logger import configure_logging
from config.state import SessionState

configure_logging()
LOGGER = logging.getLogger("agent_edges")
LOGGER.setLevel(logging.INFO)


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
