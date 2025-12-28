from langchain_groq import ChatGroq

from config.settings import settings


class LLMClient:
    def __init__(self):
        self.model = ChatGroq(
            model=settings.LLM_MODEL_NAME, api_key=settings.GROQ_API_KEY, temperature=0.0
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
