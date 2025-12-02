import numpy as np

from core.llm import model

DISCLAIMER = "/n/n Disclaimer: I am an AI language model and not a medical professional. My responses are based on patterns in data and should not be considered as professional medical advice. Always consult a qualified healthcare provider for medical concerns."


async def get_relevant_history(session_id: str, user_input: str, memory_store, top_k: int = 3):
    """
    Retrieve the most relevant pieces of conversation history based on the user's user_input.
    """
    # Fetch all conversation history for the user
    history = await memory_store.get_conversation_history(session_id, limit=50)

    if not history:
        return []

    # Create embeddings for the user_input and history entries
    question_embedding = await model.aembed(user_input)
    history_embeddings = [await model.aembed(entry["text"]) for entry in history]

    # Calculate similarity scores
    similarities = [
        np.dot(question_embedding, he) / (np.linalg.norm(question_embedding) * np.linalg.norm(he))
        for he in history_embeddings
    ]

    # Get indices of top_k most similar entries
    top_indices = np.argsort(similarities)[-top_k:][::-1]

    # Retrieve the most relevant history entries
    relevant_history = [history[i]["text"] for i in top_indices]

    return "\n".join(relevant_history)
