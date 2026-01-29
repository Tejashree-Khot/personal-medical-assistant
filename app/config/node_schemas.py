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


class AgentResponse(BaseModel):
    """Unified response schema for all text-based agent nodes."""

    response: str


class EnsureDetailsResult(BaseModel):
    """Result of ensure details."""

    has_sufficient_details: bool
    response: str


class AncientKnowledgeResult(BaseModel):
    """Result of ancient knowledge."""

    gathered_ancient_knowledge: bool
    response: str


class MedicalSupervisorResult(BaseModel):
    """Result of medical supervisor."""

    needs_clarification: bool
    response: str
