"""Request and response schemas."""

from pydantic import BaseModel


class UserInput(BaseModel):
    """User input schema."""

    session_id: str
    user_id: str
    user_input: str


class GuardrailResult(BaseModel):
    """Result of input guardrail."""

    is_emergency: bool
    is_medical: bool


class EnsureDetailsResult(BaseModel):
    """Result of ensure details."""

    has_sufficient_details: bool
    response: str
    requested_details: str


class AgentResponse(BaseModel):
    """Standard response schema for agent nodes."""

    response: str
