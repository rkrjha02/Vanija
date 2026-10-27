"""Tests for CORS allowed-origins configuration. No database connection needed."""

import pytest
from unittest.mock import patch

from app.main import _build_allowed_origins, LOCAL_ORIGINS


class TestBuildAllowedOrigins:
    def test_empty_allowed_origins_returns_only_localhost(self):
        with patch("app.main.settings") as mock:
            mock.allowed_origins = ""
            result = _build_allowed_origins()
        assert result == LOCAL_ORIGINS

    def test_single_origin_added(self):
        with patch("app.main.settings") as mock:
            mock.allowed_origins = "https://vanija.pages.dev"
            result = _build_allowed_origins()
        assert result == LOCAL_ORIGINS + ["https://vanija.pages.dev"]

    def test_multiple_origins_split_by_comma(self):
        with patch("app.main.settings") as mock:
            mock.allowed_origins = "https://vanija.pages.dev,https://other.example.com"
            result = _build_allowed_origins()
        assert result == LOCAL_ORIGINS + ["https://vanija.pages.dev", "https://other.example.com"]

    def test_whitespace_trimmed(self):
        with patch("app.main.settings") as mock:
            mock.allowed_origins = "  https://vanija.pages.dev , https://other.example.com  "
            result = _build_allowed_origins()
        assert result == LOCAL_ORIGINS + ["https://vanija.pages.dev", "https://other.example.com"]

    def test_empty_items_ignored(self):
        with patch("app.main.settings") as mock:
            mock.allowed_origins = "https://vanija.pages.dev,,,"
            result = _build_allowed_origins()
        assert result == LOCAL_ORIGINS + ["https://vanija.pages.dev"]

    def test_only_commas_returns_only_localhost(self):
        with patch("app.main.settings") as mock:
            mock.allowed_origins = ",,,"
            result = _build_allowed_origins()
        assert result == LOCAL_ORIGINS
