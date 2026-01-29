from pydantic import BaseModel, Field


class Allergies(BaseModel):
    """Allergies profile information."""

    allergies: list[str] | None = None


class Ayurveda(BaseModel):
    """Ayurveda profile information."""

    dosha_type: str | None = None
    constitution: str | None = None
    imbalances: list[str] | None = None


class Biometrics(BaseModel):
    """Biometric profile information."""

    age: int | None = None
    bmi: float | None = None
    bmr: float | None = None
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

    dietary_preferences: list[str] | None = None
    dietary_restrictions: list[str] | None = None


class HealthGoals(BaseModel):
    """Health goals profile information."""

    goals: list[str] | None = None
    concerns: list[str] | None = None


class Lifestyle(BaseModel):
    """Lifestyle profile information."""

    activities: list[str] | None = None
    sleep_patterns: list[str] | None = None
    stress_levels: list[str] | None = None


class MedicalHistory(BaseModel):
    """Medical history profile information."""

    medications: list[str] | None = None
    medical_conditions: list[str] | None = None
    supplements: list[str] | None = None


class OtherHabbitsAndPreferences(BaseModel):
    """Habbits and preferences profile information."""

    other_habbits: list[str] | None = None
    other_preferences: list[str] | None = None


class UserProfile(BaseModel):
    """User profile information."""

    user_id: str
    name: str | None = None

    allergies: Allergies = Field(default_factory=Allergies)
    ayurveda: Ayurveda = Field(default_factory=Ayurveda)
    biometrics: Biometrics = Field(default_factory=Biometrics)
    demographics: Demographics = Field(default_factory=Demographics)
    diet: Diet = Field(default_factory=Diet)
    health_goals: HealthGoals = Field(default_factory=HealthGoals)
    lifestyle: Lifestyle = Field(default_factory=Lifestyle)
    medical_history: MedicalHistory = Field(default_factory=MedicalHistory)
    other_habbits_and_preferences: OtherHabbitsAndPreferences = Field(
        default_factory=OtherHabbitsAndPreferences
    )


class ProfileUpdate(BaseModel):
    """Profile update information."""

    name: str | None = None
    allergies: Allergies | None = None
    ayurveda: Ayurveda | None = None
    biometrics: Biometrics | None = None
    demographics: Demographics | None = None
    diet: Diet | None = None
    health_goals: HealthGoals | None = None
    lifestyle: Lifestyle | None = None
    medical_history: MedicalHistory | None = None
    other_habbits_and_preferences: OtherHabbitsAndPreferences | None = None
