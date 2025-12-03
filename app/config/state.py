from typing import Any, List

from pydantic import BaseModel, Field


class Allergy(BaseModel):
    allergies: List[str]


class Biometrics(BaseModel):
    age: int
    BMI: float
    BMR: float
    gender: str
    height: int
    weight: int


class Demographics(BaseModel):
    city: str
    country: str
    region: str


class Diet(BaseModel):
    dietary_preferences: List[str]
    dietary_restrictions: List[str]


class Lifestyle(BaseModel):
    activities: List[str]
    sleep_patterns: List[str]
    stress_levels: List[str]


class MedicalHistory(BaseModel):
    medications: List[str]
    medical_conditions: List[str]


class UserProfile(BaseModel):
    user_id: str

    allergies: Allergy
    biometrics: Biometrics
    demographics: Demographics
    diet: Diet
    lifestyle: Lifestyle
    medical_history: MedicalHistory


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
    is_medical: bool = Field(default=False)
    lifestyle_advice: str = Field(default="")
    user_profile: UserProfile | None = None
    response: str = Field(default="")
    safety_warnings: List[str] = Field(default_factory=list)
    tcm_advice: str = Field(default="")
    is_emergency: bool = Field(default=False)
    needs_clarification: bool = Field(default=False)
    clarification_questions: List[str] = Field(default_factory=list)
    has_contraindications: bool = Field(default=False)
