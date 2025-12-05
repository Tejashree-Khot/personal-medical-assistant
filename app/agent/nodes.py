"""Orchestrator nodes."""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from agent.utils import configure_logging, load_prompt, parse_json_response
from config.state import SessionState, UserProfile
from core.llm import LLMClient

configure_logging()
LOGGER = logging.getLogger("nodes")
LOGGER.setLevel(logging.INFO)


class BaseNode(ABC):
    @abstractmethod
    async def run(self, state: SessionState) -> SessionState:
        pass

    @staticmethod
    def update_profile(state: SessionState, updates: dict[str, Any]) -> SessionState:
        attributes_dict = state.user_profile.model_dump()

        def clean_updates(d: dict[str, Any]) -> dict[str, Any]:
            cleaned = {}
            for k, v in d.items():
                if isinstance(v, dict):
                    nested = clean_updates(v)
                    if nested:
                        cleaned[k] = nested
                elif v not in [None, "", [], {}]:
                    cleaned[k] = v
            return cleaned

        cleaned_updates = clean_updates(updates)

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


class InputNode(BaseNode):
    async def run(self, state: SessionState) -> SessionState:
        return state


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
        self, state: SessionState, user_prompt: str, assistant_response: str
    ) -> None:
        """Append user and assistant messages to conversation history."""
        if not assistant_response or not assistant_response.strip():
            LOGGER.warning("Skipping empty assistant response from conversation history")
            return

        state.conversation_history.append({"role": "user", "content": user_prompt})
        state.conversation_history.append({"role": "assistant", "content": assistant_response})

    async def invoke_llm(self, messages: list[dict[str, Any]]) -> str:
        response = await self.model.ainvoke(messages)
        return response


class InputGuardrailNode(AgentNode):
    prompt = load_prompt("1_input_guardrail.md")

    async def run(self, state: SessionState) -> SessionState:
        """Analyzes input for safety and emergency signals."""
        LOGGER.info("InputGuardrailNode: Analyzing input for safety and emergency signals")
        if state.is_emergency:
            return state
        prompt_text = self.prompt.format(user_input=state.user_input)
        messages = self.prepare_messages(state, prompt_text)
        response = await self.invoke_llm(messages)
        parsed_response = parse_json_response(response)
        state.is_emergency = parsed_response.get("is_emergency", False)
        state.is_medical = parsed_response.get("is_medical", False)
        # Do not update conversation history if it is not medical or emergency
        if state.is_medical or state.is_emergency:
            self.update_conversation_history(state, state.user_input, state.response)
        return state


class EmergencyResponseNode(AgentNode):
    prompt = load_prompt("2_emergency_response.md")

    async def run(self, state: SessionState) -> SessionState:
        """Handles emergency queries."""
        LOGGER.info("EmergencyResponseNode: Handling emergency queries")
        messages = self.prepare_messages(state, state.user_input)
        response = await self.invoke_llm(messages)
        state.response = response
        self.update_conversation_history(state, state.user_input, state.response)
        return state


class GeneralAgentNode(AgentNode):
    prompt = load_prompt("general_agent.md")

    async def run(self, state: SessionState) -> SessionState:
        """Handles casual/general queries."""
        LOGGER.info("GeneralAgentNode: Handling casual/general queries")
        messages = self.prepare_messages(state, state.user_input)
        response = await self.invoke_llm(messages)
        state.response = response
        self.update_conversation_history(state, state.user_input, state.response)
        return state


class EnsureDetailsNode(AgentNode):
    prompt = load_prompt("2_ensure_details.md")

    async def run(self, state: SessionState) -> SessionState:
        """Ensures user provides sufficient details."""
        LOGGER.info("EnsureDetailsNode: Ensuring user provides sufficient details")
        prompt_text = self.prompt.format(
            user_input=state.user_input, user_profile=state.user_profile or {}
        )
        messages = self.prepare_messages(state, prompt_text)
        response = await self.invoke_llm(messages)
        parsed_response = parse_json_response(response)
        state.has_sufficient_details = parsed_response.get("has_sufficient_details", False)
        state.response = parsed_response.get("response", "")
        self.update_conversation_history(state, state.user_input, state.response)
        return state


class ProfileExtractorNode(AgentNode):
    prompt = load_prompt("3_profile_extractor.md")

    async def run(self, state: SessionState) -> SessionState:
        """Updates persistent user profile."""
        LOGGER.info("ProfileExtractorNode: Updating user profile")
        prompt_text = self.prompt.format(
            user_input=state.user_input,
            current_profile=json.dumps(state.user_profile.model_dump())
            if state.user_profile
            else "",
        )
        messages = self.prepare_messages(state, prompt_text)
        response = await self.invoke_llm(messages)

        try:
            parsed_response = parse_json_response(response)
            state = self.update_profile(state, parsed_response)
        except Exception as e:
            LOGGER.error(f"Error in ProfileExtractorNode: {e}", exc_info=True)
            raise e
        return state


class AncientKnowledgeNode(AgentNode):
    async def run(self, state: SessionState) -> SessionState:
        """Decides if more info is needed or if specialists should run."""
        LOGGER.info(
            "AncientKnowledgeNode: Deciding if more info is needed or if specialists should run"
        )
        return state


class AllopathyAgentNode(AgentNode):
    prompt = load_prompt("4_allopathy_agent.md")

    async def run(self, state: SessionState) -> SessionState:
        """Western medicine expert."""
        LOGGER.info("AllopathyAgentNode: Western medicine expert")
        prompt_text = self.prompt.format(
            user_input=state.user_input, user_profile=state.user_profile or {}
        )
        messages = self.prepare_messages(state, prompt_text)
        response = await self.invoke_llm(messages)
        state.allopathy_response = response
        return state


class TCMKampoAgentNode(AgentNode):
    prompt = load_prompt("4_tcm_kampo_agent.md")

    async def run(self, state: SessionState) -> SessionState:
        """TCM/Kampo expert."""
        LOGGER.info("TCMKampoAgentNode: TCM/Kampo expert")
        prompt_text = self.prompt.format(
            user_input=state.user_input, user_profile=state.user_profile or {}
        )
        messages = self.prepare_messages(state, prompt_text)
        response = await self.invoke_llm(messages)
        state.tcm_kampo_response = response
        return state


class AyurvedaAgentNode(AgentNode):
    prompt = load_prompt("4_ayurveda_agent.md")

    async def run(self, state: SessionState) -> SessionState:
        """Ayurveda expert."""
        LOGGER.info("AyurvedaAgentNode: Ayurveda expert")
        prompt_text = self.prompt.format(
            user_input=state.user_input, user_profile=state.user_profile or {}
        )
        messages = self.prepare_messages(state, prompt_text)
        response = await self.invoke_llm(messages)
        state.ayurveda_response = response
        return state


class LifestyleAgentNode(AgentNode):
    prompt = load_prompt("4_lifestyle_agent.md")

    async def run(self, state: SessionState) -> SessionState:
        """Lifestyle/Nutrition expert."""
        LOGGER.info("LifestyleAgentNode: Lifestyle/Nutrition expert")
        prompt_text = self.prompt.format(
            user_input=state.user_input, user_profile=state.user_profile or {}
        )
        messages = self.prepare_messages(state, prompt_text)
        response = await self.invoke_llm(messages)
        state.lifestyle_response = response
        return state


class SynthesisNode(AgentNode):
    prompt = load_prompt("5_synthesis.md")

    async def run(self, state: SessionState) -> SessionState:
        """Combines specialist outputs into a cohesive draft."""
        LOGGER.info("SynthesisNode: Combining specialist outputs into a cohesive draft")
        prompt_text = self.prompt.format(
            user_input=state.user_input,
            allopathy_response=state.allopathy_response or "",
            tcm_kampo_response=state.tcm_kampo_response or "",
            ayurveda_response=state.ayurveda_response or "",
            lifestyle_response=state.lifestyle_response or "",
        )
        messages = self.prepare_messages(state, prompt_text)
        response = await self.invoke_llm(messages)
        state.synthesized_response = response
        self.update_conversation_history(state, state.user_input, state.response)
        return state


class ContraindicationCheckNode(AgentNode):
    prompt = load_prompt("6_contraindication_check.md")

    async def run(self, state: SessionState) -> SessionState:
        """Checks for drug-herb-food interactions."""
        LOGGER.info("ContraindicationCheckNode: Checking for drug-herb-food interactions")
        prompt_text = self.prompt.format(
            synthesized_response=state.synthesized_response or "",
            user_profile=state.user_profile or {},
        )
        messages = self.prepare_messages(state, prompt_text)
        response = await self.invoke_llm(messages)
        parsed_response = parse_json_response(response)
        state.has_contraindications = parsed_response.get("has_contraindications", False)
        state.contraindication_details = parsed_response.get("details", "")
        self.update_conversation_history(state, state.user_input, state.response)
        return state


class AdjustmentNode(AgentNode):
    prompt = load_prompt("7_adjustment.md")

    async def run(self, state: SessionState) -> SessionState:
        """Modifies response to resolve safety conflicts."""
        LOGGER.info("AdjustmentNode: Modifying response to resolve safety conflicts")
        prompt_text = self.prompt.format(
            synthesized_response=state.synthesized_response or "",
            contraindication_details=state.contraindication_details or "",
        )
        messages = self.prepare_messages(state, prompt_text)
        response = await self.invoke_llm(messages)
        state.synthesized_response = response
        state.has_contraindications = False
        self.update_conversation_history(state, state.user_input, state.response)
        return state


class ResponseGeneratorNode(AgentNode):
    prompt = load_prompt("response_generator.md")

    async def run(self, state: SessionState) -> SessionState:
        """Formats final response for the user."""
        LOGGER.info("ResponseGeneratorNode: Formatting final response for the user")
        prompt_text = self.prompt.format(synthesized_response=state.synthesized_response or "")
        messages = self.prepare_messages(state, prompt_text)
        response = await self.invoke_llm(messages)
        state.response = response
        self.update_conversation_history(state, state.user_input, state.response)
        return state


class ResponseNode(BaseNode):
    async def run(self, state: SessionState) -> dict[str, Any]:  # noqa: PLR6301
        return {"response": state.response}
