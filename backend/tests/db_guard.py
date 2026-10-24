"""Guard: refuse to run database tests against the production database."""

from urllib.parse import urlparse


def _normalize_host(host: str) -> str:
    """Lowercase, strip port, remove '-pooler' so pooled and direct hosts compare equal."""
    host = host.lower()
    # Remove port if present (e.g. "host.neon.tech:5432" -> "host.neon.tech")
    if ":" in host:
        host = host.rsplit(":", 1)[0]
    host = host.replace("-pooler", "")
    return host


def _db_name(url: str) -> str:
    """Extract the database name (path without leading slash)."""
    return urlparse(url).path.lstrip("/").lower()


class DatabaseGuardError(Exception):
    pass


def validate_test_database_url(database_url: str, test_database_url: str) -> None:
    """Raise DatabaseGuardError if the test URL is missing or points to the same database."""
    if not test_database_url:
        raise DatabaseGuardError(
            "TEST_DATABASE_URL is not set. Database tests need a separate test database."
        )

    prod_host = _normalize_host(urlparse(database_url).hostname or "")
    test_host = _normalize_host(urlparse(test_database_url).hostname or "")

    prod_db = _db_name(database_url)
    test_db = _db_name(test_database_url)

    if prod_host == test_host and prod_db == test_db:
        raise DatabaseGuardError(
            "TEST_DATABASE_URL points to the same database as DATABASE_URL "
            f"(host: {test_host}, db: {test_db}). "
            "Tests drop and recreate all tables — use a separate Neon project or branch."
        )
