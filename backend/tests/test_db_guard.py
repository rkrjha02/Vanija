"""Tests for the database safety guard. No database connection needed."""

import pytest

from tests.db_guard import DatabaseGuardError, validate_test_database_url


class TestValidateTestDatabaseUrl:
    def test_missing_test_url_raises(self):
        with pytest.raises(DatabaseGuardError, match="TEST_DATABASE_URL is not set"):
            validate_test_database_url(
                "postgresql+psycopg://u:p@host.neon.tech/mydb?sslmode=require",
                "",
            )

    def test_same_host_and_db_raises(self):
        with pytest.raises(DatabaseGuardError, match="same database"):
            validate_test_database_url(
                "postgresql+psycopg://u:p@ep-abc-123.us-east-2.aws.neon.tech/maindb?sslmode=require",
                "postgresql+psycopg://u:p@ep-abc-123.us-east-2.aws.neon.tech/maindb?sslmode=require",
            )

    def test_pooler_variant_treated_as_same_host(self):
        """A pooled URL and a direct URL to the same host+db must be caught."""
        with pytest.raises(DatabaseGuardError, match="same database"):
            validate_test_database_url(
                "postgresql+psycopg://u:p@ep-abc-123.us-east-2.aws.neon.tech/mydb",
                "postgresql+psycopg://u:p@ep-abc-123-pooler.us-east-2.aws.neon.tech/mydb",
            )

    def test_different_port_same_host_raises(self):
        with pytest.raises(DatabaseGuardError, match="same database"):
            validate_test_database_url(
                "postgresql+psycopg://u:p@host.neon.tech:5432/mydb",
                "postgresql+psycopg://u:p@host.neon.tech:6543/mydb",
            )

    def test_different_db_name_passes(self):
        validate_test_database_url(
            "postgresql+psycopg://u:p@host.neon.tech/production",
            "postgresql+psycopg://u:p@host.neon.tech/testdb",
        )

    def test_different_host_passes(self):
        validate_test_database_url(
            "postgresql+psycopg://u:p@ep-prod-111.neon.tech/mydb",
            "postgresql+psycopg://u:p@ep-test-222.neon.tech/mydb",
        )

    def test_case_insensitive(self):
        with pytest.raises(DatabaseGuardError, match="same database"):
            validate_test_database_url(
                "postgresql+psycopg://u:p@Host.Neon.Tech/MyDB",
                "postgresql+psycopg://u:p@host.neon.tech/mydb",
            )

    def test_error_message_does_not_contain_password(self):
        secret = "super_secret_password_123"
        with pytest.raises(DatabaseGuardError) as exc_info:
            validate_test_database_url(
                f"postgresql+psycopg://u:{secret}@host.neon.tech/db",
                f"postgresql+psycopg://u:{secret}@host.neon.tech/db",
            )
        assert secret not in str(exc_info.value)
