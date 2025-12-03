from contextlib import asynccontextmanager
from datetime import datetime

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres import AsyncPostgresStore
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from config.settings import settings
from config.state import SessionState, UserProfile


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
        async with self.pool.connection() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS session_state (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    user_input TEXT,
                    is_medical BOOLEAN,
                    allopathy_advice TEXT,
                    ayurveda_advice TEXT,
                    tcm_advice TEXT,
                    lifestyle_advice TEXT,
                    response TEXT,
                    safety_warnings JSONB,
                    conversation_history JSONB,
                    profile JSONB,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_profile (
                    user_id TEXT PRIMARY KEY,
                    allergies JSONB,
                    biometrics JSONB,
                    demographics JSONB,
                    diet JSONB,
                    lifestyle JSONB,
                    medical_history JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

    async def add_state(self, state: SessionState):
        import json

        await self.ensure_pool()
        async with self.pool.connection() as conn:
            await conn.execute(
                """
                INSERT INTO session_state (
                    session_id, user_id, user_input, is_medical, allopathy_advice, ayurveda_advice, 
                    tcm_advice, lifestyle_advice, response, safety_warnings, conversation_history, profile, updated_at
                )
                VALUES (
                    %(session_id)s, %(user_id)s, %(user_input)s, %(is_medical)s, %(allopathy_advice)s, %(ayurveda_advice)s,
                    %(tcm_advice)s, %(lifestyle_advice)s, %(response)s, %(safety_warnings)s::jsonb, %(conversation_history)s::jsonb, %(profile)s::jsonb, CURRENT_TIMESTAMP
                )
                ON CONFLICT (session_id) DO UPDATE SET
                    user_id = EXCLUDED.user_id,
                    user_input = EXCLUDED.user_input,
                    is_medical = EXCLUDED.is_medical,
                    allopathy_advice = EXCLUDED.allopathy_advice,
                    ayurveda_advice = EXCLUDED.ayurveda_advice,
                    tcm_advice = EXCLUDED.tcm_advice,
                    lifestyle_advice = EXCLUDED.lifestyle_advice,
                    response = EXCLUDED.response,
                    safety_warnings = EXCLUDED.safety_warnings,
                    conversation_history = EXCLUDED.conversation_history,
                    profile = EXCLUDED.profile,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                {
                    "session_id": state.session_id,
                    "user_id": state.user_id,
                    "user_input": state.user_input,
                    "is_medical": state.is_medical,
                    "allopathy_advice": state.allopathy_advice,
                    "ayurveda_advice": state.ayurveda_advice,
                    "tcm_advice": state.tcm_advice,
                    "lifestyle_advice": state.lifestyle_advice,
                    "response": state.response,
                    "safety_warnings": json.dumps(state.safety_warnings),
                    "conversation_history": json.dumps(state.conversation_history),
                    "profile": state.user_profile.model_dump_json() if state.user_profile else None,
                },
            )

    async def get_state(self, session_id: str) -> SessionState | None:
        await self.ensure_pool()
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

    async def save_user_profile(self, profile: "UserProfile"):
        await self.ensure_pool()
        async with self.pool.connection() as conn:
            await conn.execute(
                """
                INSERT INTO user_profile (
                    user_id, allergies, biometrics, demographics, diet, lifestyle, medical_history, updated_at
                )
                VALUES (
                    %(user_id)s, %(allergies)s::jsonb, %(biometrics)s::jsonb, %(demographics)s::jsonb,
                    %(diet)s::jsonb, %(lifestyle)s::jsonb, %(medical_history)s::jsonb, CURRENT_TIMESTAMP
                )
                ON CONFLICT (user_id) DO UPDATE SET
                    allergies = EXCLUDED.allergies,
                    biometrics = EXCLUDED.biometrics,
                    demographics = EXCLUDED.demographics,
                    diet = EXCLUDED.diet,
                    lifestyle = EXCLUDED.lifestyle,
                    medical_history = EXCLUDED.medical_history,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                {
                    "user_id": profile.user_id,
                    "allergies": profile.allergies.model_dump_json(),
                    "biometrics": profile.biometrics.model_dump_json(),
                    "demographics": profile.demographics.model_dump_json(),
                    "diet": profile.diet.model_dump_json(),
                    "lifestyle": profile.lifestyle.model_dump_json(),
                    "medical_history": profile.medical_history.model_dump_json(),
                },
            )

    async def get_user_profile(self, user_id: str) -> "UserProfile | None":
        from config.state import UserProfile

        await self.ensure_pool()
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT * FROM user_profile WHERE user_id = %(user_id)s", {"user_id": user_id}
                )
                row = await cur.fetchone()
                if row:
                    return UserProfile(**row)
        return None

    async def close(self):
        if self.pool:
            await self.pool.close()
