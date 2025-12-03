"""Orchestrator nodes."""

import logging
from abc import ABC, abstractmethod
from typing import Any

from config.context import GraphContext
from langgraph.runtime import Runtime

from agent.utils import load_prompt, parse_json_response
from config.state import SessionState
from core.llm import LLMClient

LOGGER = logging.getLogger("nodes")
LOGGER.setLevel(logging.INFO)


class BaseNode(ABC):
    @abstractmethod
    async def run(
        self, state: SessionState, runtime: Runtime[GraphContext] | None = None
    ) -> SessionState:
        pass


class InputNode(BaseNode):
    async def run(
        self, state: SessionState, runtime: Runtime[GraphContext] | None = None
    ) -> SessionState:
        return state


class AgentNode(BaseNode):
    """Base class for nodes that interact with LLM."""

    def __init__(self, model: LLMClient) -> None:
        self.model = model

    def prepare_messages(self, state: SessionState, current_prompt: str) -> list[dict[str, Any]]:
        """Build LLM-formatted messages list from conversation history and current prompt."""
        messages = []

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

    async def run(
        self, state: SessionState, runtime: Runtime[GraphContext] | None = None
    ) -> SessionState:
        """Analyzes input for safety and emergency signals."""
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


class LoadProfileNode(BaseNode):
    async def run(
        self, state: SessionState, runtime: Runtime[GraphContext] | None = None
    ) -> SessionState:
        """Retrieves user history and health profile."""
        if runtime and runtime.context:
            state.user_profile = runtime.context.user_profile
            state.conversation_history = runtime.context.conversation_history or []
        return state


class GeneralAgentNode(AgentNode):
    prompt = load_prompt("general_agent.md")

    async def run(
        self, state: SessionState, runtime: Runtime[GraphContext] | None = None
    ) -> SessionState:
        """Handles casual/general queries."""
        messages = self.prepare_messages(state, state.user_input)
        response = await self.invoke_llm(messages)
        state.response = response
        self.update_conversation_history(state, state.user_input, state.response)
        return state


class MedicalSupervisorNode(AgentNode):
    prompt = load_prompt("medical_supervisor.md")

    async def run(
        self, state: SessionState, runtime: Runtime[GraphContext] | None = None
    ) -> SessionState:
        """Decides if more info is needed or if specialists should run."""
        prompt_text = self.prompt.format(
            user_input=state.user_input, user_profile=state.user_profile or {}
        )
        messages = self.prepare_messages(state, prompt_text)
        response = await self.invoke_llm(messages)
        parsed_response = parse_json_response(response)
        state.needs_clarification = parsed_response.get("needs_clarification", False)
        state.clarification_questions = parsed_response.get("clarification_questions", [])
        self.update_conversation_history(state, state.user_input, state.response)
        return state


class EnsureDetailsNode(AgentNode):
    prompt = load_prompt("ensure_details.md")

    async def run(
        self, state: SessionState, runtime: Runtime[GraphContext] | None = None
    ) -> SessionState:
        """Ensures user provides sufficient details."""
        prompt_text = self.prompt.format(
            user_input=state.user_input, user_profile=state.user_profile or {}
        )
        messages = self.prepare_messages(state, prompt_text)
        response = await self.invoke_llm(messages)
        parsed_response = parse_json_response(response)
        state.has_sufficient_details = parsed_response.get("has_sufficient_details", False)
        self.update_conversation_history(state, state.user_input, state.response)
        return state


class AncientKnowledgeNode(AgentNode):
    async def run(
        self, state: SessionState, runtime: Runtime[GraphContext] | None = None
    ) -> SessionState:
        """Decides if more info is needed or if specialists should run."""
        return state


class AllopathyAgentNode(AgentNode):
    prompt = load_prompt("allopathy_agent.md")

    async def run(
        self, state: SessionState, runtime: Runtime[GraphContext] | None = None
    ) -> SessionState:
        """Western medicine expert."""
        prompt_text = self.prompt.format(
            user_input=state.user_input, user_profile=state.user_profile or {}
        )
        messages = self.prepare_messages(state, prompt_text)
        response = await self.invoke_llm(messages)
        state.allopathy_response = response
        self.update_conversation_history(state, state.user_input, state.response)
        return state


class TCMKampoAgentNode(AgentNode):
    prompt = load_prompt("tcm_kampo_agent.md")

    async def run(
        self, state: SessionState, runtime: Runtime[GraphContext] | None = None
    ) -> SessionState:
        """TCM/Kampo expert."""
        prompt_text = self.prompt.format(
            user_input=state.user_input, user_profile=state.user_profile or {}
        )
        messages = self.prepare_messages(state, prompt_text)
        response = await self.invoke_llm(messages)
        state.tcm_kampo_response = response
        self.update_conversation_history(state, state.user_input, state.response)
        return state


class AyurvedaAgentNode(AgentNode):
    prompt = load_prompt("ayurveda_agent.md")

    async def run(
        self, state: SessionState, runtime: Runtime[GraphContext] | None = None
    ) -> SessionState:
        """Ayurveda expert."""
        prompt_text = self.prompt.format(
            user_input=state.user_input, user_profile=state.user_profile or {}
        )
        messages = self.prepare_messages(state, prompt_text)
        response = await self.invoke_llm(messages)
        state.ayurveda_response = response
        self.update_conversation_history(state, state.user_input, state.response)
        return state


class LifestyleAgentNode(AgentNode):
    prompt = load_prompt("lifestyle_agent.md")

    async def run(
        self, state: SessionState, runtime: Runtime[GraphContext] | None = None
    ) -> SessionState:
        """Lifestyle/Nutrition expert."""
        prompt_text = self.prompt.format(
            user_input=state.user_input, user_profile=state.user_profile or {}
        )
        messages = self.prepare_messages(state, prompt_text)
        response = await self.invoke_llm(messages)
        state.lifestyle_response = response
        self.update_conversation_history(state, state.user_input, state.response)
        return state


class SynthesisNode(AgentNode):
    prompt = load_prompt("synthesis.md")

    async def run(
        self, state: SessionState, runtime: Runtime[GraphContext] | None = None
    ) -> SessionState:
        """Combines specialist outputs into a cohesive draft."""
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
    prompt = load_prompt("contraindication_check.md")

    async def run(
        self, state: SessionState, runtime: Runtime[GraphContext] | None = None
    ) -> SessionState:
        """Checks for drug-herb-food interactions."""
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
    prompt = load_prompt("adjustment.md")

    async def run(
        self, state: SessionState, runtime: Runtime[GraphContext] | None = None
    ) -> SessionState:
        """Modifies response to resolve safety conflicts."""
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

    async def run(
        self, state: SessionState, runtime: Runtime[GraphContext] | None = None
    ) -> SessionState:
        """Formats final response for the user."""
        prompt_text = self.prompt.format(synthesized_response=state.synthesized_response or "")
        messages = self.prepare_messages(state, prompt_text)
        response = await self.invoke_llm(messages)
        state.response = response
        self.update_conversation_history(state, state.user_input, state.response)
        return state


class ProfileExtractorNode(AgentNode):
    prompt = load_prompt("profile_extractor.md")

    async def run(
        self, state: SessionState, runtime: Runtime[GraphContext] | None = None
    ) -> SessionState:
        """Updates persistent user profile."""
        prompt_text = self.prompt.format(
            user_input=state.user_input,
            response=state.response or "",
            current_profile=state.user_profile or {},
        )
        messages = self.prepare_messages(state, prompt_text)
        response = await self.invoke_llm(messages)
        parsed_response = parse_json_response(response)

        if state.user_profile is None:
            state.user_profile = {}
        state.user_profile.update(parsed_response.get("profile_updates", {}))
        self.update_conversation_history(state, state.user_input, state.response)
        return state


class ResponseNode(BaseNode):
    async def run(self, state: SessionState) -> dict[str, Any]:  # noqa: PLR6301
        return {"response": state.response}
