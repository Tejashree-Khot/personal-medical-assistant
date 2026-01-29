from typing import Any, List

from pydantic import BaseModel, Field


class Ayurveda(BaseModel):
    """Ayurveda profile information."""

    dosha_type: str | None = None
    constitution: str | None = None
    imbalances: List[str] | None = None


class Biometrics(BaseModel):
    """Biometric profile information."""

    age: int | None = None
    BMI: float | None = None
    BMR: float | None = None
    gender: str | None = None
    height: float | None = None
    weight: float | None = None


class Demographics(BaseModel):
    """Demographic profile information."""

    city: str | None = None
    country: str | None = None
    region: str | None = None


class Diet(BaseModel):
    """Dietary profile information."""

    dietary_preferences: List[str] | None = None
    dietary_restrictions: List[str] | None = None


class HealthGoals(BaseModel):
    """Health goals profile information."""

    goals: List[str] | None = None
    concerns: List[str] | None = None


class Lifestyle(BaseModel):
    """Lifestyle profile information."""

    activities: List[str] | None = None
    sleep_patterns: List[str] | None = None
    stress_levels: List[str] | None = None


class MedicalHistory(BaseModel):
    """Medical history profile information."""

    medications: List[str] | None = None
    medical_conditions: List[str] | None = None
    supplements: List[str] | None = None


class UserProfile(BaseModel):
    """User profile information."""

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


class ProfileUpdate(BaseModel):
    """Profile update information."""

    name: str | None = None
    allergies: str | None = None
    ayurveda: Ayurveda | None = None
    biometrics: Biometrics | None = None
    demographics: Demographics | None = None
    diet: Diet | None = None
    health_goals: HealthGoals | None = None
    lifestyle: Lifestyle | None = None
    medical_history: MedicalHistory | None = None
    other: str | None = None


class SessionState(BaseModel):
    """The state of the graph."""

    session_id: str

    user_id: str | None = None
    user_input: str | None = None

    allopathy_response: str = Field(default="")
    ayurveda_response: str = Field(default="")
    conversation_history: list[dict[str, Any]] = Field(default_factory=list)
    gathered_ancient_knowledge: bool = Field(default=False)
    has_sufficient_details: bool = Field(default=False)
    is_emergency: bool = Field(default=False)
    is_medical: bool = Field(default=False)
    lifestyle_response: str = Field(default="")
    response: str = Field(default="")
    safety_warnings: List[str] = Field(default_factory=list)
    synthesized_response: str = Field(default="")
    tcm_response: str = Field(default="")
    user_profile: UserProfile | None = None

    def apply_updates(self, updates: dict[str, Any]) -> None:
        """Apply updates to the state."""
        for key, value in updates.items():
            if not hasattr(self, key):
                continue
            if value in (None, "", [], {}):
                continue
            setattr(self, key, value)
