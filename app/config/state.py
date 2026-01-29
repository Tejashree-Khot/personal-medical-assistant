from typing import Any, List

from pydantic import BaseModel, Field

from config.profile_schema import UserProfile


class SessionState(BaseModel):
    """The state of the graph."""

    session_id: str
    user_id: str | None = None

    user_input: str | None = None

    is_emergency: bool = Field(default=False)
    is_medical: bool = Field(default=False)

    has_sufficient_details: bool = Field(default=False)
    requested_details: str = Field(default="")

    gathered_ancient_knowledge: bool = Field(default=False)

    allopathy_response: str = Field(default="")
    ayurveda_response: str = Field(default="")
    lifestyle_response: str = Field(default="")
    tcm_response: str = Field(default="")

    safety_warnings: List[str] = Field(default_factory=list)

    response: str = Field(default="")
    conversation_history: list[dict[str, Any]] = Field(default_factory=list)

    user_profile: UserProfile | None = None

    def apply_updates(self, updates: dict[str, Any]) -> None:
        """Apply updates to the state."""
        for key, value in updates.items():
            if not hasattr(self, key):
                continue
            if value in (None, "", [], {}):
                continue
            setattr(self, key, value)
