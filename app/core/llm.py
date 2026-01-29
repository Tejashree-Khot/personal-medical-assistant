import json
from typing import Type, TypeVar

from langchain_groq import ChatGroq
from pydantic import BaseModel

from config.settings import settings

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    def __init__(self):
        self.model = ChatGroq(
            model=settings.LLM_MODEL_NAME, api_key=settings.GROQ_API_KEY, temperature=0.0
        )

    async def ainvoke(self, messages: list[dict[str, str]]) -> str:
        """Invoke the LLM with messages."""
        return await self.model.ainvoke(messages)

    async def ainvoke_structured(
        self, system_prompt: str, user_prompt: str, response_model: Type[T]
    ) -> T:
        """Invoke the LLM with messages and return a structured response."""
        schema = response_model.model_json_schema()

        messages = [
            {
                "role": "system",
                "content": (
                    f"{system_prompt}\n\n"
                    "You MUST return valid JSON only.\n"
                    "Do not add explanations or extra text.\n\n"
                    f"JSON Schema:\n{json.dumps(schema, indent=2)}"
                ),
            },
            {"role": "user", "content": user_prompt},
        ]

        response = await self.model.ainvoke(messages)

        try:
            parsed = json.loads(response.content)
            return response_model.model_validate(parsed)
        except Exception as e:
            raise ValueError(
                f"Invalid structured response from LLM.\nRaw output:\n{response.content}"
            ) from e
