"""Request and response schemas."""

from pydantic import BaseModel


class UserInput(BaseModel):
    session_id: str
    user_id: str
    user_input: str
