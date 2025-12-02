import asyncio
import os
import sys

# Add app directory to sys.path
sys.path.append(os.path.join(os.getcwd(), "app"))

from config.state import SessionState
from memory.postgres import PostgresClient


async def main():
    print("Initializing PostgresClient...")
    try:
        client = PostgresClient()

        print("Creating tables...")
        await client.create_tables()

        session_id = "test_session_123"
        state = SessionState(
            session_id=session_id,
            user_input="Hello",
            is_medical=False,
            response="Hi there",
            conversation_history=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"},
            ],
        )

        print("Saving state...")
        await client.add_state(state)

        print("Loading state...")
        loaded_state = await client.get_state(session_id)

        if loaded_state:
            print(f"Loaded state for session {loaded_state.session_id}")
            print(f"User input: {loaded_state.user_input}")
            print(f"History: {loaded_state.conversation_history}")
            assert loaded_state.session_id == session_id
            assert loaded_state.user_input == "Hello"
            assert len(loaded_state.conversation_history) == 2
            print("Verification successful!")
        else:
            print("Failed to load state.")

        await client.close()
    except Exception as e:
        print(f"Verification failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
