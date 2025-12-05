import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic import SecretStr

load_dotenv()


class LLMClient:
    def __init__(self):
        self.model = ChatGroq(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            api_key=SecretStr(os.environ["GROQ_API_KEY"]),
            temperature=0.0,
        )

    async def ainvoke(self, messages):
        """Invoke the LLM with messages.

        Args:
            messages: Either a string prompt or a list of message dicts

        Returns:
            The response content as a string
        """
        response = await self.model.ainvoke(messages)
        return response.content


llm_client = LLMClient()
