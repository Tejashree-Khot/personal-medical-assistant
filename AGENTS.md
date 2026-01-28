# Repo description

Persionalized Medical AI Agent built on LangGraph is an advanced AI assistant designed to provide comprehensive, personalized medical advice.

## Development Rules

1. Always use `uv run` to execute Python scripts.
2. Do **not** add test cases unless explicitly requested.
3. Do **not** add comments in the code.
4. Always add single line Docstrings.
5. Do **not** over-engineer the solution.
6. Use **classes and functions** wherever appropriate.
7. Follow the **existing project structure and coding style** when adding new code.
8. **Always confirm with me before changing or introducing a design pattern.**
9. Implement **only the requested functionality** — do not add extras.
10. Add code in **logical order**; if no clear order exists, use **alphabetical order**.

## Coding practices

- **Type hints**: Use type annotations for function signatures and class attributes
- **Pydantic**: Use `BaseModel` for data validation and `BaseSettings` for configuration
- **Async/await**: Use async patterns for I/O operations (database, LLM calls)
- **Dependency injection**: Use `@lru_cache` decorated functions for singleton instances
- **Factory pattern**: Use factory classes/functions for creating instances
- **ABC pattern**: Use abstract base classes for extensible components
- **Retry with tenacity**: Use `@retry` decorator for external API calls
- **Path handling**: Use `pathlib.Path` for file path operations
- **Logging**: Use centralized logging configuration with module-level loggers
- **DRY principle**: Reuse existing functions and abstractions; avoid code duplication
- **Code style**: Write concise and optimized code

## Repo structure

```text
personal-medical-assistant/
├── app/                # Main application package
│   ├── agent/          # Langgraph agent orchestration
│   ├── config/         # Configuration and state definitions
│   ├── core/           # LLM and embedding clients
│   ├── memory/         # Milvus and PostgreSQL persistence
│   ├── prompts/        # Prompt templates
│   ├── service/        # FastAPI routes and utilities
│   └── utils/          # Logging and PDF processing
├── docs/               # Documentation
└── scripts/            # Utility scripts (Streamlit UI)
```
