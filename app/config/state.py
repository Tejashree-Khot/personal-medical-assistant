from typing import Any

from pydantic import BaseModel, Field


class SessionState(BaseModel):
    """
    The state of the graph.

    Attributes:
        user_input: The user's most recent user_input.
        is_medical: A boolean flag indicating if the user_input is medical.
        session_id: The ID of the current user.
        tool_responses: The combined string from the medical tools.
        response: The final response from the non-medical path.
        conversation_history: The list of messages that make up the chat history.
    """

    session_id: str
    user_input: str | None = None
    is_medical: bool = Field(default=False)
    tool_responses: str = Field(default="")
    response: str = Field(default="")
    conversation_history: list[dict[str, Any]] = Field(default_factory=list)
