from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI

from config.settings import settings
from memory import initialize_database, initialize_store


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Initializes database checkpointer and store based on settings."""
    try:
        app.state.db_conn = await asyncpg.connect(
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD.get_secret_value(),
            database=settings.POSTGRES_DB,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
        )

        # Initialize saver and store
        async with initialize_database() as saver, initialize_store() as store:
            if hasattr(saver, "setup"):
                await saver.setup()
            if hasattr(store, "setup"):
                await store.setup()

            yield
    finally:
        # Cleanup on shutdown
        if hasattr(app.state, "db_conn"):
            await app.state.db_conn.close()
        print("Log:--> Application shutting down...")
