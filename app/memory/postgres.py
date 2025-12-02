import json
from contextlib import asynccontextmanager
from datetime import datetime

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres import AsyncPostgresStore
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from config.settings import settings
from config.state import SessionState


def get_postgres_connection_string() -> str:
    """Build and return the PostgreSQL connection string from settings."""
    if settings.POSTGRES_PASSWORD is None:
        raise ValueError("POSTGRES_PASSWORD is not set")
    return (
        f"postgresql://{settings.POSTGRES_USER}:"
        f"{settings.POSTGRES_PASSWORD.get_secret_value()}@"
        f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/"
        f"{settings.POSTGRES_DB}"
    )


@asynccontextmanager
async def get_postgres_saver():
    "Initializes and return a postgreSQL saver instance using connection pool for resilent connection"

    application_name = settings.POSTGRES_APPLICATION_NAME + "-" + "saver"

    async with AsyncConnectionPool(
        get_postgres_connection_string(),
        min_size=settings.POSTGRES_MIN_CONNECTIONS_PER_POOL,
        max_size=settings.POSTGRES_MAX_CONNECTIONS_PER_POOL,
        kwargs={"autocommit": True, "row_factory": dict_row, "application_name": application_name},
        check=AsyncConnectionPool.check_connection,
    ) as pool:
        try:
            async with pool.connection() as conn:
                # Create the chat_history table if it doesn't exist
                # await conn.execute(create_chat_history_table_command())

                checkpointer = AsyncPostgresSaver(conn)  # type: ignore
                await checkpointer.setup()
                yield checkpointer

        finally:
            await pool.close()


@asynccontextmanager
async def get_postgres_store():
    "Initializes and return a postgreSQL store instance using connection pool for resilent connection"

    application_name = settings.POSTGRES_APPLICATION_NAME + "-" + "store"

    async with AsyncConnectionPool(
        get_postgres_connection_string(),
        min_size=settings.POSTGRES_MIN_CONNECTIONS_PER_POOL,
        max_size=settings.POSTGRES_MAX_CONNECTIONS_PER_POOL,
        kwargs={"autocommit": True, "row_factory": dict_row, "application_name": application_name},
        check=AsyncConnectionPool.check_connection,
    ) as pool:
        try:
            async with pool.connection() as conn:
                store = AsyncPostgresStore(conn)  # type: ignore
                await store.setup()
                yield store

        finally:
            await pool.close()


async def save_message(conn, session_id: str, role: str, content: str):
    """Save a message to the chat_history table."""
    await conn.execute(
        """ INSERT INTO chat_history (session_id, role, content, timestap) VALUES ($1, $2, $3, $4, $5)""",
        session_id,
        role,
        content,
        datetime.utcnow(),
    )


class PostgresClient:
    def __init__(self):
        self.connection_string = get_postgres_connection_string()
        self.pool = None

    async def ensure_pool(self):
        if self.pool is None:
            self.pool = AsyncConnectionPool(
                self.connection_string,
                min_size=settings.POSTGRES_MIN_CONNECTIONS_PER_POOL,
                max_size=settings.POSTGRES_MAX_CONNECTIONS_PER_POOL,
                kwargs={
                    "autocommit": True,
                    "row_factory": dict_row,
                    "application_name": settings.POSTGRES_APPLICATION_NAME,
                },
                check=AsyncConnectionPool.check_connection,
                open=False,
            )
            await self.pool.open()

    async def create_tables(self):
        await self.ensure_pool()
        if self.pool is None:
            return
        async with self.pool.connection() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS session_state (
                    session_id TEXT PRIMARY KEY,
                    user_input TEXT,
                    is_medical BOOLEAN,
                    tool_responses TEXT,
                    response TEXT,
                    conversation_history JSONB,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

    async def add_state(self, state: SessionState):
        await self.ensure_pool()
        if self.pool is None:
            return
        async with self.pool.connection() as conn:
            await conn.execute(
                """
                INSERT INTO session_state (session_id, user_input, is_medical, tool_responses, response, conversation_history, updated_at)
                VALUES (%(session_id)s, %(user_input)s, %(is_medical)s, %(tool_responses)s, %(response)s, %(conversation_history)s::jsonb, CURRENT_TIMESTAMP)
                ON CONFLICT (session_id) DO UPDATE SET
                    user_input = EXCLUDED.user_input,
                    is_medical = EXCLUDED.is_medical,
                    tool_responses = EXCLUDED.tool_responses,
                    response = EXCLUDED.response,
                    conversation_history = EXCLUDED.conversation_history,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                {
                    "session_id": state.session_id,
                    "user_input": state.user_input,
                    "is_medical": state.is_medical,
                    "tool_responses": state.tool_responses,
                    "response": state.response,
                    "conversation_history": json.dumps(state.conversation_history),
                },
            )

    async def get_state(self, session_id: str) -> SessionState | None:
        await self.ensure_pool()
        if self.pool is None:
            return None
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT * FROM session_state WHERE session_id = %(session_id)s",
                    {"session_id": session_id},
                )
                row = await cur.fetchone()
                if row:
                    return SessionState(**row)
        return None

    async def close(self):
        if self.pool:
            await self.pool.close()
