"""Orchestrator nodes."""

import logging
from abc import ABC, abstractmethod
from typing import Any

from langgraph.runtime import Runtime

from agent.utils import load_prompt, parse_json_response
from config.context import GraphContext
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


class ClassifierNode(AgentNode):
    prompt = load_prompt("query_classifier.md")

    async def run(
        self, state: SessionState, runtime: Runtime[GraphContext] | None = None
    ) -> SessionState:
        """Invoke the model to get a classification."""
        prompt_text = self.prompt.format(user_input=state.user_input)
        messages = self.prepare_messages(state, prompt_text)
        response = await self.invoke_llm(messages)
        parsed_response = parse_json_response(response)
        state.is_medical = parsed_response.get("is_medical")
        return state


class MedicalNode(AgentNode):
    prompt = load_prompt("medical_response.md")

    async def run(
        self, state: SessionState, runtime: Runtime[GraphContext] | None = None
    ) -> SessionState:
        """Invoke the model to get a medical response."""
        messages = self.prepare_messages(state, state.user_input)
        response = await self.invoke_llm(messages)
        state.response = response
        self.update_conversation_history(state, state.user_input, state.response)
        return state


class GeneralNode(AgentNode):
    prompt = load_prompt("general_response.md")

    async def run(
        self, state: SessionState, runtime: Runtime[GraphContext] | None = None
    ) -> SessionState:
        """Invoke the model to get a general response."""
        messages = self.prepare_messages(state, state.user_input)
        response = await self.invoke_llm(messages)
        state.response = response
        self.update_conversation_history(state, state.user_input, state.response)
        return state


class ToolNode(AgentNode):
    prompt = load_prompt("tool_response.md")

    async def run(
        self, state: SessionState, runtime: Runtime[GraphContext] | None = None
    ) -> SessionState:
        """Invoke the model to get a medical response."""
        messages = self.prepare_messages(state, state.user_input)
        response = await self.invoke_llm(messages)
        parsed_response = parse_json_response(response)
        state.response = parsed_response.get("response")
        self.update_conversation_history(state, state.user_input, state.response)
        return state


class ResponseNode(BaseNode):
    async def run(
        self, state: SessionState, runtime: Runtime[GraphContext] | None = None
    ) -> SessionState:
        return state
