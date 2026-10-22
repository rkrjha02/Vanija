"""Tests for the provider layer: retries on timeout and rate-limit, error handling."""

import asyncio
import sys
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.providers.openai_compat import (
    LLMRateLimitError,
    LLMResponseError,
    LLMTimeoutError,
    call_llm,
)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

FAKE_MESSAGES = [{"role": "user", "content": "hi"}]
FAKE_TOOLS = []

GOOD_RESPONSE = {
    "choices": [{
        "message": {"content": "Hello!", "tool_calls": None},
    }],
}


def _make_response(status_code=200, json_data=None):
    resp = httpx.Response(
        status_code=status_code,
        json=json_data or GOOD_RESPONSE,
        request=httpx.Request("POST", "http://test/"),
    )
    return resp


# -------------------------------------------------------------------
# Timeout
# -------------------------------------------------------------------
@pytest.mark.asyncio
async def test_timeout_retries_once_then_succeeds():
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(side_effect=[
        httpx.TimeoutException("timeout"),
        _make_response(200),
    ])

    with patch("app.providers.openai_compat.httpx.AsyncClient", return_value=mock_client):
        result = await call_llm(FAKE_MESSAGES, FAKE_TOOLS)

    assert result["reply_text"] == "Hello!"
    assert mock_client.post.call_count == 2


@pytest.mark.asyncio
async def test_timeout_retries_once_then_raises():
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(side_effect=[
        httpx.TimeoutException("timeout"),
        httpx.TimeoutException("timeout again"),
    ])

    with patch("app.providers.openai_compat.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(LLMTimeoutError):
            await call_llm(FAKE_MESSAGES, FAKE_TOOLS)

    assert mock_client.post.call_count == 2


# -------------------------------------------------------------------
# Rate limit (429)
# -------------------------------------------------------------------
@pytest.mark.asyncio
async def test_rate_limit_retries_then_succeeds():
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(side_effect=[
        _make_response(429, {"error": "rate limited"}),
        _make_response(200),
    ])

    with (
        patch("app.providers.openai_compat.httpx.AsyncClient", return_value=mock_client),
        patch("app.providers.openai_compat.RATE_LIMIT_WAIT_SECONDS", 0),
    ):
        result = await call_llm(FAKE_MESSAGES, FAKE_TOOLS)

    assert result["reply_text"] == "Hello!"
    assert mock_client.post.call_count == 2


@pytest.mark.asyncio
async def test_rate_limit_exhausts_retries():
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=_make_response(429, {"error": "rate limited"}))

    with (
        patch("app.providers.openai_compat.httpx.AsyncClient", return_value=mock_client),
        patch("app.providers.openai_compat.RATE_LIMIT_WAIT_SECONDS", 0),
    ):
        with pytest.raises(LLMRateLimitError):
            await call_llm(FAKE_MESSAGES, FAKE_TOOLS)

    assert mock_client.post.call_count == 3  # 1 + 2 retries


# -------------------------------------------------------------------
# HTTP errors (non-429)
# -------------------------------------------------------------------
@pytest.mark.asyncio
async def test_http_500_raises_response_error():
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=_make_response(500, {"error": "server error"}))

    with patch("app.providers.openai_compat.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(LLMResponseError):
            await call_llm(FAKE_MESSAGES, FAKE_TOOLS)


# -------------------------------------------------------------------
# Successful response parsing
# -------------------------------------------------------------------
@pytest.mark.asyncio
async def test_successful_response_parsed():
    json_data = {
        "choices": [{
            "message": {
                "content": None,
                "tool_calls": [{
                    "id": "call_1",
                    "function": {
                        "name": "search_products",
                        "arguments": '{"category": "phone"}',
                    },
                }],
            },
        }],
    }
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=_make_response(200, json_data))

    with patch("app.providers.openai_compat.httpx.AsyncClient", return_value=mock_client):
        result = await call_llm(FAKE_MESSAGES, FAKE_TOOLS)

    assert result["reply_text"] is None
    assert len(result["tool_calls"]) == 1
    assert result["tool_calls"][0]["name"] == "search_products"
    assert result["tool_calls"][0]["arguments"] == {"category": "phone"}


@pytest.mark.asyncio
async def test_malformed_tool_args_returns_empty_dict():
    json_data = {
        "choices": [{
            "message": {
                "content": None,
                "tool_calls": [{
                    "id": "call_1",
                    "function": {
                        "name": "search_products",
                        "arguments": "not valid json{{{",
                    },
                }],
            },
        }],
    }
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=_make_response(200, json_data))

    with patch("app.providers.openai_compat.httpx.AsyncClient", return_value=mock_client):
        result = await call_llm(FAKE_MESSAGES, FAKE_TOOLS)

    assert result["tool_calls"][0]["arguments"] == {}
