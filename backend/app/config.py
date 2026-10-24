from pathlib import Path
from urllib.parse import urlparse

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent

REQUIRED_SCHEME = "postgresql+psycopg"


def _check_database_url(url: str, setting_name: str) -> None:
    """Validate a database URL's scheme and host. Never prints the URL or password."""
    parsed = urlparse(url)
    if parsed.scheme != REQUIRED_SCHEME:
        raise ValueError(
            f"{setting_name} must start with 'postgresql+psycopg://'. "
            f"Found scheme '{parsed.scheme}://'. "
            "Change the start of the connection string."
        )
    host = (parsed.hostname or "").lower()
    if "-pooler" in host:
        raise ValueError(
            f"{setting_name} must use the DIRECT connection string, "
            "but the host contains '-pooler'. "
            "Remove '-pooler' from the host name in your .env file."
        )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
    )

    # Database
    database_url: str
    test_database_url: str = ""

    @model_validator(mode="after")
    def _validate_database_urls(self) -> "Settings":
        _check_database_url(self.database_url, "DATABASE_URL")
        if self.test_database_url:
            _check_database_url(self.test_database_url, "TEST_DATABASE_URL")
        return self

    # Groq
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = ""

    # Agent loop
    max_rounds: int = 5
    lock_wait_seconds: int = 90

    # Memory
    recent_messages_count: int = 10
    max_shown_products: int = 10

    # Orders
    pending_expiry_minutes: int = 15

    # Search
    default_search_limit: int = 5

    # Embeddings (policy search)
    gemini_api_key: str = ""
    embedding_provider: str = "gemini"
    embedding_model: str = "gemini-embedding-2"
    embedding_dimensions: int = 768
    embedding_requests_per_minute: int = 30

    # Policies
    policies_dir: Path = BACKEND_DIR.parent / "policies"
    max_chunk_chars: int = 1500
    policy_results_limit: int = 3
    policy_min_similarity: float = 0.65
    policy_question_max_length: int = 300


settings = Settings()
