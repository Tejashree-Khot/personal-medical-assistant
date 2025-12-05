import json
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
                    allopathy_advice TEXT,
                    ayurveda_advice TEXT,
                    conversation_history JSONB,
                    gathered_ancient_knowledge BOOLEAN,
                    has_sufficient_details BOOLEAN,
                    has_contraindications BOOLEAN,
                    is_emergency BOOLEAN,
                    is_medical BOOLEAN,
                    lifestyle_advice TEXT,
                    response TEXT,
                    safety_warnings JSONB,
                    tcm_advice TEXT,
                    user_profile JSONB,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_profile (
                    user_id TEXT PRIMARY KEY,
                    name TEXT,
                    allergies TEXT,
                    ayurveda JSONB,
                    biometrics JSONB,
                    demographics JSONB,
                    diet JSONB,
                    health_goals JSONB,
                    lifestyle JSONB,
                    medical_history JSONB,
                    other TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await conn.execute("""
                ALTER TABLE user_profile 
                ADD COLUMN IF NOT EXISTS name TEXT;
            """)

    async def add_state(self, state: SessionState):
        await self.ensure_pool()
        async with self.pool.connection() as conn:
            await conn.execute(
                """
                INSERT INTO session_state (
                    session_id, 
                    user_id, 
                    user_input, 
                    allopathy_advice, 
                    ayurveda_advice, 
                    conversation_history,
                    gathered_ancient_knowledge,
                    has_sufficient_details,
                    has_contraindications,
                    is_emergency,
                    is_medical,
                    lifestyle_advice,
                    response,
                    safety_warnings,
                    tcm_advice,
                    user_profile
                )
                VALUES (
                    %(session_id)s, 
                    %(user_id)s, 
                    %(user_input)s, 
                    %(allopathy_advice)s, 
                    %(ayurveda_advice)s, 
                    %(conversation_history)s, 
                    %(gathered_ancient_knowledge)s, 
                    %(has_sufficient_details)s, 
                    %(has_contraindications)s, 
                    %(is_emergency)s, 
                    %(is_medical)s, 
                    %(lifestyle_advice)s, 
                    %(response)s, 
                    %(safety_warnings)s, 
                    %(tcm_advice)s, 
                    %(user_profile)s
                )
                ON CONFLICT (session_id) DO UPDATE SET
                    user_id = EXCLUDED.user_id,
                    user_input = EXCLUDED.user_input,
                    allopathy_advice = EXCLUDED.allopathy_advice,
                    ayurveda_advice = EXCLUDED.ayurveda_advice,
                    conversation_history = EXCLUDED.conversation_history,
                    gathered_ancient_knowledge = EXCLUDED.gathered_ancient_knowledge,
                    has_sufficient_details = EXCLUDED.has_sufficient_details,
                    has_contraindications = EXCLUDED.has_contraindications,
                    is_emergency = EXCLUDED.is_emergency,
                    is_medical = EXCLUDED.is_medical,
                    lifestyle_advice = EXCLUDED.lifestyle_advice,
                    response = EXCLUDED.response,
                    safety_warnings = EXCLUDED.safety_warnings,
                    tcm_advice = EXCLUDED.tcm_advice,
                    user_profile = EXCLUDED.user_profile,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                {
                    "session_id": state.session_id,
                    "user_id": state.user_id,
                    "user_input": state.user_input,
                    "allopathy_advice": state.allopathy_advice,
                    "ayurveda_advice": state.ayurveda_advice,
                    "conversation_history": json.dumps(state.conversation_history),
                    "gathered_ancient_knowledge": state.gathered_ancient_knowledge,
                    "has_sufficient_details": state.has_sufficient_details,
                    "has_contraindications": state.has_contraindications,
                    "is_emergency": state.is_emergency,
                    "is_medical": state.is_medical,
                    "lifestyle_advice": state.lifestyle_advice,
                    "response": state.response,
                    "safety_warnings": json.dumps(state.safety_warnings),
                    "tcm_advice": state.tcm_advice,
                    "user_profile": state.user_profile.model_dump_json()
                    if state.user_profile
                    else None,
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

    async def save_user_profile(self, user_profile: UserProfile):
        await self.ensure_pool()
        async with self.pool.connection() as conn:
            await conn.execute(
                """
                INSERT INTO user_profile (
                    user_id, name, allergies, ayurveda, biometrics, demographics, diet, health_goals, lifestyle, medical_history, updated_at
                )
                VALUES (
                    %(user_id)s, %(name)s, %(allergies)s, %(ayurveda)s::jsonb, %(biometrics)s::jsonb, %(demographics)s::jsonb,
                    %(diet)s::jsonb, %(health_goals)s::jsonb, %(lifestyle)s::jsonb, %(medical_history)s::jsonb, CURRENT_TIMESTAMP
                )
                ON CONFLICT (user_id) DO UPDATE SET
                    name = COALESCE(EXCLUDED.name, user_profile.name),
                    allergies = COALESCE(EXCLUDED.allergies, user_profile.allergies),
                    ayurveda = COALESCE(EXCLUDED.ayurveda, user_profile.ayurveda),
                    biometrics = COALESCE(EXCLUDED.biometrics, user_profile.biometrics),
                    demographics = COALESCE(EXCLUDED.demographics, user_profile.demographics),
                    diet = COALESCE(EXCLUDED.diet, user_profile.diet),
                    health_goals = COALESCE(EXCLUDED.health_goals, user_profile.health_goals),
                    lifestyle = COALESCE(EXCLUDED.lifestyle, user_profile.lifestyle),
                    medical_history = COALESCE(EXCLUDED.medical_history, user_profile.medical_history),
                    updated_at = CURRENT_TIMESTAMP;
                """,
                {
                    "user_id": user_profile.user_id,
                    "name": user_profile.name,
                    "allergies": user_profile.allergies,
                    "ayurveda": user_profile.ayurveda.model_dump_json()
                    if user_profile.ayurveda
                    else None,
                    "biometrics": user_profile.biometrics.model_dump_json()
                    if user_profile.biometrics
                    else None,
                    "demographics": user_profile.demographics.model_dump_json()
                    if user_profile.demographics
                    else None,
                    "diet": user_profile.diet.model_dump_json() if user_profile.diet else None,
                    "health_goals": user_profile.health_goals.model_dump_json()
                    if user_profile.health_goals
                    else None,
                    "lifestyle": user_profile.lifestyle.model_dump_json()
                    if user_profile.lifestyle
                    else None,
                    "medical_history": user_profile.medical_history.model_dump_json()
                    if user_profile.medical_history
                    else None,
                    "other": user_profile.other,
                },
            )

    async def get_user_profile(self, user_id: str) -> UserProfile | None:
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
