"""Orchestrator nodes."""

import json
import logging
from abc import ABC
from typing import Any

from config.state import SessionState, UserProfile
from core.llm import LLMClient
from utils.helper import load_prompt, parse_json_response
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


class AgentNode(BaseNode):
    """Base class for nodes that interact with LLM."""

    system_prompt_template = load_prompt("system_prompt.md")

    def __init__(self, model: LLMClient) -> None:
        self.model = model

    def prepare_system_prompt(self, state: SessionState) -> str:
        """Prepare system prompt with user profile context."""
        user_profile_str = ""
        if state.user_profile:
            user_profile_str = state.user_profile.model_dump_json(indent=2, exclude_none=True)
        else:
            user_profile_str = "No user profile available yet."
        return self.system_prompt_template.format(user_profile=user_profile_str)

    def prepare_messages(self, state: SessionState, current_prompt: str) -> list[dict[str, Any]]:
        """Build LLM-formatted messages list from system prompt, conversation history and current prompt."""
        messages = []

        system_prompt = self.prepare_system_prompt(state)
        messages.append({"role": "system", "content": system_prompt})

        if state.conversation_history:
            messages.extend(state.conversation_history)

        messages.append({"role": "user", "content": current_prompt})

        return messages

    def update_conversation_history(
        self, state: SessionState, user_prompt: str, response: dict[str, Any]
    ) -> None:
        """Append user and assistant messages to conversation history."""
        if not response.get("response", "").strip():
            return
        state.conversation_history.append({"role": "user", "content": user_prompt})
        state.conversation_history.append({"role": "assistant", "content": response})

    async def invoke_llm(self, messages: list[dict[str, Any]]) -> str:
        """Invoke the LLM with the given messages."""
        response = await self.model.ainvoke(messages)
        return response

    async def run_node(
        self, state: SessionState, *, prompt_kwargs: dict[str, Any], parse_json: bool = False
    ) -> SessionState:
        """Invoke the LLM with the given prompt -> LLM -> JSON parser -> return response."""
        if not self.prompt:
            return state
        prompt_text = self.prompt.format(**prompt_kwargs)
        messages = self.prepare_messages(state, prompt_text)
        response = await self.invoke_llm(messages)
        if parse_json:
            parsed = parse_json_response(response)
            state.apply_updates(parsed)
        else:
            state.response = response.strip()
        self.update_conversation_history(state, state.user_input, {"response": state.response})
        return state


class InputGuardrailNode(AgentNode):
    prompt = load_prompt("1_input_guardrail.md")

    async def run(self, state: SessionState) -> SessionState:
        """Analyzes input for safety and emergency signals."""
        LOGGER.info("InputGuardrailNode: Analyzing input for safety and emergency signals")
        if state.is_emergency:
            return state
        prompt_kwargs = {"user_input": state.user_input}
        return await self.run_node(state, prompt_kwargs=prompt_kwargs, parse_json=True)


class EmergencyResponseNode(AgentNode):
    prompt = load_prompt("2_emergency_response.md")

    async def run(self, state: SessionState) -> SessionState:
        """Handles emergency queries."""
        LOGGER.info("EmergencyResponseNode: Handling emergency queries")
        prompt_kwargs = {"user_input": state.user_input}
        return await self.run_node(state, prompt_kwargs=prompt_kwargs)


class GeneralAgentNode(AgentNode):
    prompt = load_prompt("2_general_agent.md")

    async def run(self, state: SessionState) -> SessionState:
        """Handles casual/general queries."""
        LOGGER.info("GeneralAgentNode: Handling casual/general queries")
        prompt_kwargs = {"user_input": state.user_input}
        return await self.run_node(state, prompt_kwargs=prompt_kwargs)


class EnsureDetailsNode(AgentNode):
    prompt = load_prompt("2_ensure_details.md")

    async def run(self, state: SessionState) -> SessionState:
        """Ensures user provides sufficient details."""
        LOGGER.info("EnsureDetailsNode: Ensuring user provides sufficient details")
        prompt_kwargs = {"user_input": state.user_input, "user_profile": state.user_profile or {}}
        return await self.run_node(state, prompt_kwargs=prompt_kwargs, parse_json=True)


class SpecialistAgentNode(AgentNode):
    """Generic specialist node that stores response in a configurable state attribute."""

    def __init__(self, model: LLMClient, agent_name: str) -> None:
        super().__init__(model)
        self.prompt = load_prompt(f"4_{agent_name}.md")

    async def run(self, state: SessionState) -> SessionState:
        LOGGER.info("SpecialistAgentNode: Running specialist agent")
        prompt_kwargs = (
            {"user_input": state.user_input, "user_profile": state.user_profile or {}},
        )
        return await self.run_node(state, prompt_kwargs=prompt_kwargs, parse_json=True)


class SynthesisAndSafetyNode(AgentNode):
    """Synthesizes specialist outputs and ensures safety."""

    prompt = load_prompt("5_synthesis_and_safety.md")

    async def run(self, state: SessionState) -> SessionState:
        """Combines specialist outputs, checks safety, and adjusts if needed."""
        LOGGER.info("SynthesisAndSafetyNode: Synthesizing outputs and checking safety")
        prompt_kwargs = {
            "user_input": state.user_input,
            "allopathy_response": state.allopathy_response or "",
            "tcm_kampo_response": state.tcm_kampo_response or "",
            "ayurveda_response": state.ayurveda_response or "",
            "lifestyle_response": state.lifestyle_response or "",
            "user_profile": state.user_profile or {},
        }
        return await self.run_node(state, prompt_kwargs=prompt_kwargs)


class ProfileExtractorNode(AgentNode):
    """Extracts and updates user profile from conversation."""

    prompt = load_prompt("profile_extractor.md")

    @staticmethod
    def _clean_updates(d: dict[str, Any]) -> dict[str, Any]:
        cleaned = {}
        for k, v in d.items():
            if isinstance(v, dict):
                nested = ProfileExtractorNode._clean_updates(v)
                if nested:
                    cleaned[k] = nested
            elif v not in [None, "", [], {}]:
                cleaned[k] = v
        return cleaned

    @staticmethod
    def update_profile(state: SessionState, updates: dict[str, Any]) -> SessionState:
        """Updates user profile with cleaned values."""
        attributes_dict = state.user_profile.model_dump()
        cleaned_updates = ProfileExtractorNode._clean_updates(updates)

        for key, value in cleaned_updates.items():
            if key in attributes_dict:
                if isinstance(attributes_dict[key], dict) and isinstance(value, dict):
                    attributes_dict[key].update(value)
                else:
                    attributes_dict[key] = value
            else:
                LOGGER.warning(f"Attempted to set invalid UserProfile field: {key}")
        state.user_profile = UserProfile(**attributes_dict)
        return state

    async def run(self, state: SessionState) -> SessionState:
        """Updates persistent user profile."""
        LOGGER.info("ProfileExtractorNode: Updating user profile")
        prompt_kwargs = {
            "user_input": state.user_input,
            "current_profile": json.dumps(state.user_profile.model_dump())
            if state.user_profile
            else "",
        }
        return await self.run_node(state, prompt_kwargs=prompt_kwargs, parse_json=True)


class ResponseNode(BaseNode):
    async def run(self, state: SessionState) -> dict[str, Any]:  # noqa: PLR6301
        return {"response": state.response}


class Nodes:
    """Container for all orchestration nodes."""

    def __init__(self, llm_client: LLMClient) -> None:
        self.input_guardrail = InputGuardrailNode(llm_client).run
        self.emergency_response = EmergencyResponseNode(llm_client).run
        self.general_agent = GeneralAgentNode(llm_client).run
        self.ensure_details = EnsureDetailsNode(llm_client).run
        self.ancient_knowledge_router = AncientKnowledgeRouterNode().run
        self.ancient_knowledge = AncientKnowledgeNode().run
        self.allopathy_agent = SpecialistAgentNode(llm_client, "allopathy_agent").run
        self.ayurveda_agent = SpecialistAgentNode(llm_client, "ayurveda_agent").run
        self.lifestyle_agent = SpecialistAgentNode(llm_client, "lifestyle_agent").run
        self.tcm_kampo_agent = SpecialistAgentNode(llm_client, "tcm_kampo_agent").run
        self.synthesis_and_safety = SynthesisAndSafetyNode(llm_client).run
        self.profile_extractor = ProfileExtractorNode(llm_client).run
        self.response = ResponseNode().run
