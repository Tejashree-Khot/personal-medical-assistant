"""Profile extractor node."""

import json
import logging
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from pydantic import ValidationError

from config.profile_schema import ProfileUpdate, UserProfile
from core.llm import LLMClient
from memory.postgres import PostgresClient
from utils.helper import load_prompt
from utils.logger import configure_logging

configure_logging()
LOGGER = logging.getLogger("nodes")
LOGGER.setLevel(logging.INFO)


class ProfileExtractor:
    """Extracts and updates user profile from conversation."""

    prompt_template = load_prompt("profile_extractor.md")

    def __init__(self, llm_client: LLMClient, postgres_client: PostgresClient):
        self.postgres_client = postgres_client
        self.structured_llm = llm_client.model.with_structured_output(ProfileUpdate)

    async def load_user_profile(self, user_id: str) -> UserProfile | None:
        """Load user profile from Postgres."""
        return await self.postgres_client.get_user_profile(user_id)

    async def save_user_profile(self, profile: UserProfile) -> None:
        """Save user profile to Postgres."""
        await self.postgres_client.save_user_profile(profile)

    @staticmethod
    def escape_braces(text: str) -> str:
        return text.replace("{", "{{").replace("}", "}}")

    def get_safe_user_profile(self, user_profile: UserProfile) -> str:
        """Get user profile as JSON string excluding sensitive fields like user_id."""
        profile = user_profile.model_dump_json(indent=2, exclude_none=True, exclude={"user_id"})
        profile_str = json.dumps(profile or {}, ensure_ascii=False)
        return self.escape_braces(profile_str)

    @staticmethod
    def _clean_updates(d: dict[str, Any]) -> dict[str, Any]:
        """Recursively removes empty values from a dictionary."""
        cleaned = {}
        for k, v in d.items():
            if isinstance(v, dict):
                nested = ProfileExtractor._clean_updates(v)
                if nested:
                    cleaned[k] = nested
            elif v not in [None, "", [], {}]:
                cleaned[k] = v
        return cleaned

    async def extract_updates(
        self, user_input: str, user_profile: UserProfile | None
    ) -> dict[str, Any]:
        """Run LLM extraction and return cleaned updates."""
        user_profile_str = self.get_safe_user_profile(
            user_profile or UserProfile(user_id="unknown")
        )

        prompt_kwargs = {"user_input": user_input, "user_profile": user_profile_str}

        prompt = ChatPromptTemplate.from_messages(
            [("system", "You are a profile management system."), ("user", self.prompt_template)]
        )
        # chain = prompt_template -> structured_llm
        # prompt_kwargs will be passed to prompt_template by chain
        chain = prompt | self.structured_llm
        response: ProfileUpdate = await chain.ainvoke(prompt_kwargs)

        updates = response.model_dump(exclude_none=True)
        return self._clean_updates(updates)

    async def run(self, user_id: str, user_input: str) -> None:
        """Updates persistent user profile."""
        LOGGER.info("Loading user profile from Postgres for user_id=%s", user_id)
        user_profile = await self.load_user_profile(user_id) or UserProfile(user_id=user_id)

        LOGGER.info("Loaded user profile from Postgres for user_id=%s", user_id)
        try:
            LOGGER.info("Running profile extraction for user_id=%s", user_id)

            updates = await self.extract_updates(user_input=user_input, user_profile=user_profile)

            if updates:
                await self.save_user_profile(UserProfile(user_id=user_id, **updates))
            else:
                LOGGER.info("No updates to save for user_id=%s", user_id)

            LOGGER.info("Profile extraction completed for user_id=%s", user_id)
        except Exception:
            LOGGER.exception("Profile extraction failed")
