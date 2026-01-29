"""Orchestrator nodes."""

import logging
from abc import ABC
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from config.node_schemas import AgentResponse, EnsureDetailsResult, GuardrailResult
from config.state import SessionState
from core.llm import LLMClient
from utils.helper import load_prompt
from utils.logger import configure_logging

configure_logging()
LOGGER = logging.getLogger("nodes")
LOGGER.setLevel(logging.INFO)


class BaseNode(ABC):
    async def run(self, state: SessionState) -> SessionState:
        return state


class AncientKnowledgeRouterNode(BaseNode):
    """Routes to ancient knowledge or response."""


class AncientKnowledgeNode(BaseNode):
    """Decides if more info is needed or if specialists should run."""


class MedicalRouterNode(BaseNode):
    """Routes to emergency medical agent or ensure details."""


class AgentNode(BaseNode):
    """Base class for nodes that interact with LLM."""

    system_prompt_template = load_prompt("system_prompt.md")
    output_schema: type[BaseModel] | None = None

    def __init__(self, llm_client: LLMClient) -> None:
        self.model = llm_client.model
        if self.output_schema:
            self.structured_llm = llm_client.model.with_structured_output(self.output_schema)

    def prepare_system_prompt(self, state: SessionState) -> str:
        """Prepare system prompt with user profile context."""
        user_profile_str = self.get_safe_user_profile(state)
        return self.system_prompt_template.format(user_profile=user_profile_str)

    @staticmethod
    def get_safe_user_profile(state: SessionState) -> str:
        """Get user profile as JSON string excluding sensitive fields like user_id."""
        if state.user_profile:
            return state.user_profile.model_dump_json(
                indent=2, exclude_none=True, exclude={"user_id"}
            )
        return "No user profile available yet."

    @staticmethod
    def escape_braces(text: str) -> str:
        return text.replace("{", "{{").replace("}", "}}")

    def prepare_prompt(self, state: SessionState, current_prompt: str) -> ChatPromptTemplate:
        """Prepare ChatPromptTemplate with escaped braces."""
        system_prompt = self.escape_braces(self.prepare_system_prompt(state))
        current_prompt = self.escape_braces(current_prompt)
        escaped_history = [
            (msg["role"], self.escape_braces(msg["content"])) for msg in state.conversation_history
        ]
        return ChatPromptTemplate.from_messages(
            [("system", system_prompt), *escaped_history, ("user", current_prompt)]
        )

    def update_conversation_history(
        self, state: SessionState, user_prompt: str, response: dict[str, Any]
    ) -> None:
        """Append user and assistant messages to conversation history."""
        if not response.get("response", "").strip():
            return
        state.conversation_history.append({"role": "user", "content": user_prompt})
        state.conversation_history.append({"role": "assistant", "content": response["response"]})

    async def run_structured_node(
        self,
        state: SessionState,
        *,
        prompt_kwargs: dict[str, Any],
        response_field: str | None = None,
    ) -> SessionState:
        """Invoke LLM with structured output schema and apply updates to state."""
        if not self.prompt or not self.output_schema:
            return state
        prompt_text = self.prompt.format(**prompt_kwargs)
        prompt = self.prepare_prompt(state, prompt_text)
        chain = prompt | self.structured_llm
        response: BaseModel = await chain.ainvoke(prompt_kwargs)
        updates = response.model_dump(exclude_none=True)
        if response_field and "response" in updates:
            updates[response_field] = updates.pop("response")
        state.apply_updates(updates)
        self.update_conversation_history(state, state.user_input, updates)
        return state


class InputGuardrailNode(AgentNode):
    """Analyzes input for safety and emergency signals."""

    prompt = load_prompt("input_guardrail.md")
    output_schema = GuardrailResult

    async def run(self, state: SessionState) -> SessionState:
        """Analyzes input for safety and emergency signals."""
        LOGGER.info("InputGuardrailNode: Analyzing input for safety and emergency signals")
        if state.is_emergency or state.is_medical:
            return state
        return await self.run_structured_node(state, prompt_kwargs={"user_input": state.user_input})


class EmergencyMedicalAgentNode(AgentNode):
    """Handles emergency queries."""

    prompt = load_prompt("emergency_medical_agent.md")
    output_schema = AgentResponse

    async def run(self, state: SessionState) -> SessionState:
        """Handles emergency queries."""
        LOGGER.info("EmergencyResponseNode: Handling emergency queries")
        return await self.run_structured_node(state, prompt_kwargs={"user_input": state.user_input})


class GeneralAgentNode(AgentNode):
    """Handles casual/general queries."""

    prompt = load_prompt("general_agent.md")
    output_schema = AgentResponse

    async def run(self, state: SessionState) -> SessionState:
        """Handles casual/general queries."""
        LOGGER.info("GeneralAgentNode: Handling casual/general queries")
        return await self.run_structured_node(state, prompt_kwargs={"user_input": state.user_input})


class MedicalAgentNode(AgentNode):
    """Handles medical queries."""

    prompt = load_prompt("medical_agent.md")
    output_schema = AgentResponse

    async def run(self, state: SessionState) -> SessionState:
        """Handles medical queries."""
        LOGGER.info("MedicalAgentNode: Handling medical queries")
        return await self.run_structured_node(state, prompt_kwargs={"user_input": state.user_input})


class EnsureDetailsNode(AgentNode):
    """Ensures user provides sufficient details."""

    prompt = load_prompt("ensure_details.md")
    output_schema = EnsureDetailsResult

    async def run(self, state: SessionState) -> SessionState:
        """Ensures user provides sufficient details."""
        LOGGER.info("EnsureDetailsNode: Ensuring user provides sufficient details")
        prompt_kwargs = {
            "user_input": state.user_input,
            "user_profile": self.get_safe_user_profile(state),
        }
        return await self.run_structured_node(state, prompt_kwargs=prompt_kwargs)


class SpecialistAgentNode(AgentNode):
    """Generic specialist node that stores response in a configurable state attribute."""

    output_schema = AgentResponse

    AGENT_RESPONSE_FIELDS = {
        "allopathy_agent": "allopathy_response",
        "ayurveda_agent": "ayurveda_response",
        "lifestyle_agent": "lifestyle_response",
        "tcm_kampo_agent": "tcm_response",
    }

    def __init__(self, model: LLMClient, agent_name: str) -> None:
        super().__init__(model)
        self.agent_name = agent_name
        self.prompt = load_prompt(f"{agent_name}.md")
        self.response_field = self.AGENT_RESPONSE_FIELDS.get(agent_name, "response")

    async def run(self, state: SessionState) -> SessionState:
        """Runs specialist agent and stores response in the appropriate field."""
        LOGGER.info("SpecialistAgentNode: Running specialist agent %s", self.agent_name)
        prompt_kwargs = {
            "user_input": state.user_input,
            "user_profile": self.get_safe_user_profile(state),
        }
        return await self.run_structured_node(
            state, prompt_kwargs=prompt_kwargs, response_field=self.response_field
        )


class SynthesisAndSafetyNode(AgentNode):
    """Synthesizes specialist outputs and ensures safety."""

    prompt = load_prompt("synthesis_and_safety.md")
    output_schema = AgentResponse

    async def run(self, state: SessionState) -> SessionState:
        """Combines specialist outputs, checks safety, and adjusts if needed."""
        LOGGER.info("SynthesisAndSafetyNode: Synthesizing outputs and checking safety")
        prompt_kwargs = {
            "user_input": state.user_input,
            "allopathy_response": state.allopathy_response or "",
            "tcm_kampo_response": state.tcm_response or "",
            "ayurveda_response": state.ayurveda_response or "",
            "lifestyle_response": state.lifestyle_response or "",
            "user_profile": self.get_safe_user_profile(state),
        }
        return await self.run_structured_node(state, prompt_kwargs=prompt_kwargs)


class ResponseNode(BaseNode):
    async def run(self, state: SessionState) -> dict[str, Any]:  # noqa: PLR6301
        return {"response": state.response}


class Nodes:
    """Container for all orchestration nodes."""

    def __init__(self, llm_client: LLMClient) -> None:
        self.input_guardrail = InputGuardrailNode(llm_client).run
        self.general_agent = GeneralAgentNode(llm_client).run
        self.emergency_medical_agent = EmergencyMedicalAgentNode(llm_client).run
        self.medical_router = MedicalRouterNode().run
        self.ensure_details = EnsureDetailsNode(llm_client).run
        self.medical_agent = MedicalAgentNode(llm_client).run
        self.ancient_knowledge_router = AncientKnowledgeRouterNode().run
        self.ancient_knowledge = AncientKnowledgeNode().run
        self.allopathy_agent = SpecialistAgentNode(llm_client, "allopathy_agent").run
        self.ayurveda_agent = SpecialistAgentNode(llm_client, "ayurveda_agent").run
        self.lifestyle_agent = SpecialistAgentNode(llm_client, "lifestyle_agent").run
        self.tcm_kampo_agent = SpecialistAgentNode(llm_client, "tcm_kampo_agent").run
        self.synthesis_and_safety = SynthesisAndSafetyNode(llm_client).run
        self.response = ResponseNode().run
