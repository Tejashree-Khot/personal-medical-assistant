import logging
import os
import uuid
from dataclasses import dataclass

import requests
import streamlit as st
from app.config.state import SessionState

logger = logging.getLogger("agent")
logger.setLevel(logging.INFO)


@dataclass
class Config:
    """Central configuration for the chatbot."""

    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8080")
    QUERY_URL: str = f"{API_BASE_URL}/chat"
    TIMEOUT: int = 300


class AgentClient:
    """Agent client for interacting with the Agent/Orchestrator API."""

    def __init__(self, config: Config):
        self.config = config

    def send_query(self, query: str) -> str:
        """Sends a query to the Agent/Orchestrator API and returns the response."""
        payload = {
            "session_id": st.session_state["session_id"],
            "user_id": st.session_state["user_id"],
            "user_input": query,
        }
        try:
            response = requests.post(
                self.config.QUERY_URL, json=payload, timeout=self.config.TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API Request failed: {e}")
            raise


class ChatInterface:
    """Chat interface for the chatbot."""

    def __init__(self, agent_client: AgentClient):
        self.agent_client = agent_client
        self._init_state()

    def _init_state(self):  # noqa: PLR6301
        if "session_id" not in st.session_state:
            st.session_state["session_id"] = str(uuid.uuid4())
        if "user_id" not in st.session_state:
            st.session_state["user_id"] = "user-123"
        if "messages" not in st.session_state:
            st.session_state["messages"] = []
        if "session_metadata" not in st.session_state:
            st.session_state["session_metadata"] = SessionState(
                session_id=st.session_state["session_id"], user_id=st.session_state["user_id"]
            ).model_dump()

    def render(self):
        with st.sidebar:
            st.header("Chat Session")
            meta = SessionState(**st.session_state["session_metadata"])
            st.write(f"**ID:** `{meta.session_id[:8]}...`")
            if st.button("🔄 New Session"):
                st.session_state.clear()
                st.rerun()

        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("How can I help?"):
            self._process_input(prompt)

    def _process_input(self, prompt: str):
        st.session_state["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"), st.spinner("Thinking..."):
            try:
                meta = SessionState(**st.session_state["session_metadata"])
                meta.user_input = prompt
                response_data = self.agent_client.send_query(prompt)

                response_text = response_data.get("response", "")

                st.markdown(response_text)
                st.session_state["messages"].append({"role": "assistant", "content": response_text})
                st.session_state["session_metadata"].update(response_data)
            except Exception as e:
                st.error(f"Error: {e}")


def main():
    st.set_page_config(page_title="Medical AI Assistant", layout="wide")
    st.title("🤖 Medical AI Assistant")

    agent_client = AgentClient(Config())

    ChatInterface(agent_client).render()


if __name__ == "__main__":
    main()
