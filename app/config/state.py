from dataclasses import dataclass
from typing import Any, List

from pydantic import BaseModel, Field


class Ayurveda(BaseModel):
    dosha_type: str | None = None
    constitution: str | None = None
    imbalances: List[str] | None = None


class Biometrics(BaseModel):
    age: int | None = None
    BMI: float | None = None
    BMR: float | None = None
    gender: str | None = None
    height: float | None = None
    weight: float | None = None


class Demographics(BaseModel):
    city: str | None = None
    country: str | None = None
    region: str | None = None


class Diet(BaseModel):
    dietary_preferences: List[str] | None = None
    dietary_restrictions: List[str] | None = None


class HealthGoals(BaseModel):
    goals: List[str] | None = None
    concerns: List[str] | None = None


class Lifestyle(BaseModel):
    activities: List[str] | None = None
    sleep_patterns: List[str] | None = None
    stress_levels: List[str] | None = None


class MedicalHistory(BaseModel):
    medications: List[str] | None = None
    medical_conditions: List[str] | None = None
    supplements: List[str] | None = None


class UserProfile(BaseModel):
    user_id: str
    name: str | None = None

    allergies: str | None = Field(default=None)
    ayurveda: Ayurveda = Field(default_factory=Ayurveda)
    biometrics: Biometrics = Field(default_factory=Biometrics)
    demographics: Demographics = Field(default_factory=Demographics)
    diet: Diet = Field(default_factory=Diet)
    health_goals: HealthGoals = Field(default_factory=HealthGoals)
    lifestyle: Lifestyle = Field(default_factory=Lifestyle)
    medical_history: MedicalHistory = Field(default_factory=MedicalHistory)
    other: str | None = None


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

    user_id: str | None = None
    user_input: str | None = None

    allopathy_advice: str = Field(default="")
    ayurveda_advice: str = Field(default="")
    conversation_history: list[dict[str, Any]] = Field(default_factory=list)
    gathered_ancient_knowledge: bool = Field(default=False)
    has_sufficient_details: bool = Field(default=False)
    has_contraindications: bool = Field(default=False)
    is_emergency: bool = Field(default=False)
    is_medical: bool = Field(default=False)
    lifestyle_advice: str = Field(default="")
    response: str = Field(default="")
    safety_warnings: List[str] = Field(default_factory=list)
    tcm_advice: str = Field(default="")
    user_profile: UserProfile | None = None


@dataclass
class Context:
    """Context schema for LangGraph execution."""

    user_profile: UserProfile | None = None
