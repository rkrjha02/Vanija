from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
    )

    # Database
    database_url: str
    test_database_url: str = ""

    # Groq
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = ""

    # Agent loop
    max_rounds: int = 5

    # Memory
    recent_messages_count: int = 10
    max_shown_products: int = 10

    # Orders
    pending_expiry_minutes: int = 15

    # Search
    default_search_limit: int = 5


settings = Settings()
