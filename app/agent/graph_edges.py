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

        If medical query, go to medical_router.
        Otherwise, go to general_agent.
        """
        if state.is_medical:
            LOGGER.info("Route input guardrail: medical query")
            return "medical_router"
        else:
            LOGGER.info("Route input guardrail: general query")
            return "general_agent"

    @staticmethod
    def route_medical_query(state: SessionState) -> str:
        """Route based on medical agent check.

        If emergency detected, go to emergency_medical_agent.
        Otherwise, go to ensure_details.
        """
        if state.is_emergency:
            LOGGER.info("Route medical query: emergency detected")
            return "emergency_medical_agent"
        else:
            LOGGER.info("Route medical query: no emergency detected")
            return "ensure_details"

    @staticmethod
    def route_ensure_details(state: SessionState) -> str:
        """Route based on ensure details classification.

        If sufficient details, go to ancient_knowledge_router.
        Otherwise, go to response.
        """
        if state.has_sufficient_details:
            LOGGER.info("Route ensure details: sufficient details")
            return "ancient_knowledge_router"
        else:
            LOGGER.info("Route ensure details: insufficient details")
            return "response"

    @staticmethod
    def route_ancient_knowledge_router(state: SessionState) -> str | list[Send]:
        """Route based on ancient knowledge router decision.

        If needs ancient knowledge, go to ancient_knowledge.
        Otherwise, go to response.
        """
        if state.gathered_ancient_knowledge:
            LOGGER.info("Route ancient knowledge router: ancient knowledge gathered")
            return "ancient_knowledge"
        else:
            LOGGER.info("Route ancient knowledge router: ancient knowledge not gathered")
            return "medical_agent"
