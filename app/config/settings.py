from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    GROQ_API_KEY: SecretStr = SecretStr("groq_api_key")
    LLM_MODEL_NAME: str = Field(default="meta-llama/llama-4-maverick-17b-128e-instruct")

    SERVICE_HOST: str | None = Field(default="localhost")
    SERVICE_PORT: int | None = Field(default=8080)
    DEV: bool = Field(default=True)

    POSTGRES_USER: str | None = Field(default="postgres")
    POSTGRES_PASSWORD: SecretStr = SecretStr("postgres")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str | None = Field(default="postgres")
    POSTGRES_APPLICATION_NAME: str | None = Field(default="medical-agent")
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_MIN_CONNECTIONS_PER_POOL: int = Field(default=1)
    POSTGRES_MAX_CONNECTIONS_PER_POOL: int = Field(default=10)


settings = Settings()
