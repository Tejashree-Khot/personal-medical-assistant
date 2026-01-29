import json
from contextlib import asynccontextmanager
from datetime import datetime

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres import AsyncPostgresStore
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from config.profile_schema import UserProfile
from config.settings import settings
from config.state import SessionState


def get_postgres_connection_string() -> str:
    """Build and return the PostgreSQL connection string from settings."""
    if not settings.POSTGRES_PASSWORD:
        raise ValueError("POSTGRES_PASSWORD is not set")

    return (
        f"postgresql://{settings.POSTGRES_USER}:"
        f"{settings.POSTGRES_PASSWORD.get_secret_value()}@"
        f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/"
        f"{settings.POSTGRES_DB}"
    )


def _create_pool(application_name: str) -> AsyncConnectionPool:
    return AsyncConnectionPool(
        get_postgres_connection_string(),
        min_size=settings.POSTGRES_MIN_CONNECTIONS_PER_POOL,
        max_size=settings.POSTGRES_MAX_CONNECTIONS_PER_POOL,
        kwargs={"autocommit": True, "row_factory": dict_row, "application_name": application_name},
        check=AsyncConnectionPool.check_connection,
    )


@asynccontextmanager
async def get_postgres_saver():
    """Initialize and yield a PostgreSQL saver using a connection pool."""
    pool = _create_pool(f"{settings.POSTGRES_APPLICATION_NAME}-saver")
    async with pool:
        async with pool.connection() as conn:
            saver = AsyncPostgresSaver(conn)  # type: ignore
            await saver.setup()
            yield saver


@asynccontextmanager
async def get_postgres_store():
    """Initialize and yield a PostgreSQL store using a connection pool."""
    pool = _create_pool(f"{settings.POSTGRES_APPLICATION_NAME}-store")
    async with pool:
        async with pool.connection() as conn:
            store = AsyncPostgresStore(conn)  # type: ignore
            await store.setup()
            yield store


async def save_message(conn, session_id: str, role: str, content: str):
    """Save a message to the chat_history table."""
    await conn.execute(
        """
        INSERT INTO chat_history (session_id, role, content, timestamp)
        VALUES ($1, $2, $3, $4)
        """,
        session_id,
        role,
        content,
        datetime.utcnow(),
    )


class PostgresClient:
    def __init__(self):
        self.connection_string = get_postgres_connection_string()
        self.pool: AsyncConnectionPool | None = None

    async def ensure_pool(self):
        if not self.pool:
            self.pool = _create_pool(settings.POSTGRES_APPLICATION_NAME)
            await self.pool.open()

    async def create_tables(self):
        """Create necessary tables in PostgreSQL."""
        await self.ensure_pool()
        async with self.pool.connection() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS session_state (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    user_input TEXT,
                    allopathy_response TEXT,
                    ayurveda_response TEXT,
                    conversation_history JSONB,
                    gathered_ancient_knowledge BOOLEAN,
                    has_sufficient_details BOOLEAN,
                    is_emergency BOOLEAN,
                    is_medical BOOLEAN,
                    lifestyle_response TEXT,
                    response TEXT,
                    safety_warnings JSONB,
                    tcm_response TEXT,
                    user_profile JSONB,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_profile (
                    user_id TEXT PRIMARY KEY,
                    name TEXT,
                    allergies JSONB,
                    ayurveda JSONB,
                    biometrics JSONB,
                    demographics JSONB,
                    diet JSONB,
                    health_goals JSONB,
                    lifestyle JSONB,
                    medical_history JSONB,
                    other_habbits_and_preferences JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    async def add_state(self, state: SessionState):
        await self.ensure_pool()
        async with self.pool.connection() as conn:
            await conn.execute(
                """
                INSERT INTO session_state (
                    session_id, user_id, user_input, allopathy_response, ayurveda_response,
                    conversation_history, gathered_ancient_knowledge, has_sufficient_details,
                    is_emergency, is_medical, lifestyle_response, response, safety_warnings,
                    tcm_response, user_profile
                )
                VALUES (
                    %(session_id)s, %(user_id)s, %(user_input)s, %(allopathy_response)s,
                    %(ayurveda_response)s, %(conversation_history)s,
                    %(gathered_ancient_knowledge)s, %(has_sufficient_details)s,
                    %(is_emergency)s, %(is_medical)s, %(lifestyle_response)s,
                    %(response)s, %(safety_warnings)s, %(tcm_response)s, %(user_profile)s
                )
                ON CONFLICT (session_id) DO UPDATE SET
                    user_id = EXCLUDED.user_id,
                    user_input = EXCLUDED.user_input,
                    allopathy_response = EXCLUDED.allopathy_response,
                    ayurveda_response = EXCLUDED.ayurveda_response,
                    conversation_history = EXCLUDED.conversation_history,
                    gathered_ancient_knowledge = EXCLUDED.gathered_ancient_knowledge,
                    has_sufficient_details = EXCLUDED.has_sufficient_details,
                    is_emergency = EXCLUDED.is_emergency,
                    is_medical = EXCLUDED.is_medical,
                    lifestyle_response = EXCLUDED.lifestyle_response,
                    response = EXCLUDED.response,
                    safety_warnings = EXCLUDED.safety_warnings,
                    tcm_response = EXCLUDED.tcm_response,
                    user_profile = EXCLUDED.user_profile,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                {
                    "session_id": state.session_id,
                    "user_id": state.user_id,
                    "user_input": state.user_input,
                    "allopathy_response": state.allopathy_response,
                    "ayurveda_response": state.ayurveda_response,
                    "conversation_history": json.dumps(state.conversation_history),
                    "gathered_ancient_knowledge": state.gathered_ancient_knowledge,
                    "has_sufficient_details": state.has_sufficient_details,
                    "is_emergency": state.is_emergency,
                    "is_medical": state.is_medical,
                    "lifestyle_response": state.lifestyle_response,
                    "response": state.response,
                    "safety_warnings": json.dumps(state.safety_warnings),
                    "tcm_response": state.tcm_response,
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
                return SessionState(**row) if row else None

    async def save_user_profile(self, user_profile: UserProfile):
        await self.ensure_pool()
        async with self.pool.connection() as conn:
            await conn.execute(
                """
                INSERT INTO user_profile (
                    user_id, name, allergies, ayurveda, biometrics, demographics, diet,
                    health_goals, lifestyle, medical_history, other_habbits_and_preferences, updated_at
                )
                VALUES (
                    %(user_id)s, %(name)s, %(allergies)s::jsonb, %(ayurveda)s::jsonb,
                    %(biometrics)s::jsonb, %(demographics)s::jsonb, %(diet)s::jsonb,
                    %(health_goals)s::jsonb, %(lifestyle)s::jsonb,
                    %(medical_history)s::jsonb, %(other_habbits_and_preferences)s::jsonb, CURRENT_TIMESTAMP
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
                    other_habbits_and_preferences = COALESCE(EXCLUDED.other_habbits_and_preferences, user_profile.other_habbits_and_preferences),
                    updated_at = CURRENT_TIMESTAMP;
                """,
                {
                    "user_id": user_profile.user_id,
                    "name": user_profile.name,
                    "allergies": user_profile.allergies.model_dump_json()
                    if user_profile.allergies
                    else None,
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
                    "other_habbits_and_preferences": user_profile.other_habbits_and_preferences.model_dump_json()
                    if user_profile.other_habbits_and_preferences
                    else None,
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
                return UserProfile(**row) if row else None

    async def close(self):
        if self.pool:
            await self.pool.close()
