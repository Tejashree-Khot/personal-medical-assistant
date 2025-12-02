"""Module for handling chat history database operations."""

import psycopg2

from config.settings import settings


def create_chat_history_table():
    """create table if not exists"""
    try:
        conn = psycopg2.connect(
            dbname=settings.POSTGRES_DB,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD.get_secret_value(),
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
        )
        cursor = conn.cursor()
        cursor.execute(create_chat_history_table_command())
        conn.commit()
        cursor.close()
        conn.close()
        print("chat_history table is ready.")
    except Exception as e:
        print(f"Error creating chat_history table: {e}")


def create_chat_history_table_command():
    """Create the chat_history table SQL statement."""
    return """
    CREATE TABLE IF NOT EXISTS chat_history (
        id SERIAL PRIMARY KEY,
        session_id VARCHAR(255) NOT NULL,
        thread_id VARCHAR(255) NOT NULL,
        role VARCHAR(50) NOT NULL,
        message TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
