from .postgres import get_postgres_saver, get_postgres_store


def initialize_database():
    """Initialize appropriate database checkpointer"""
    return get_postgres_saver()


def initialize_store():
    """Initialize appropriate database checkpointer"""
    return get_postgres_store()


__all__ = ["initialize_database", "initialize_store"]
