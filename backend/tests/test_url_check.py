"""Tests for the DATABASE_URL validation in config.py. No database connection needed."""

import pytest

from app.config import _check_database_url


class TestCheckDatabaseUrl:
    def test_valid_direct_url_passes(self):
        _check_database_url(
            "postgresql+psycopg://u:p@ep-abc-123.us-east-2.aws.neon.tech/db?sslmode=require",
            "DATABASE_URL",
        )

    def test_wrong_scheme_raises(self):
        with pytest.raises(ValueError, match="must start with 'postgresql\\+psycopg://'"):
            _check_database_url(
                "postgresql://u:p@host.neon.tech/db?sslmode=require",
                "DATABASE_URL",
            )

    def test_pooler_host_raises(self):
        with pytest.raises(ValueError, match="contains '-pooler'"):
            _check_database_url(
                "postgresql+psycopg://u:p@ep-abc-123-pooler.us-east-2.aws.neon.tech/db",
                "DATABASE_URL",
            )

    def test_test_url_wrong_scheme(self):
        with pytest.raises(ValueError, match="TEST_DATABASE_URL"):
            _check_database_url(
                "postgresql://u:p@host.neon.tech/db",
                "TEST_DATABASE_URL",
            )

    def test_error_does_not_contain_password(self):
        secret = "my_secret_password_xyz"
        with pytest.raises(ValueError) as exc_info:
            _check_database_url(
                f"postgresql://u:{secret}@host.neon.tech/db",
                "DATABASE_URL",
            )
        assert secret not in str(exc_info.value)

    def test_pooler_error_does_not_contain_password(self):
        secret = "my_secret_password_xyz"
        with pytest.raises(ValueError) as exc_info:
            _check_database_url(
                f"postgresql+psycopg://u:{secret}@host-pooler.neon.tech/db",
                "DATABASE_URL",
            )
        assert secret not in str(exc_info.value)
