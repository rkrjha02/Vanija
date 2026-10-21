import asyncio
import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 60
RATE_LIMIT_MAX_RETRIES = 2
RATE_LIMIT_WAIT_SECONDS = 5


class LLMTimeoutError(Exception):
    pass


class LLMRateLimitError(Exception):
    pass


class LLMResponseError(Exception):
    pass


def _parse_response(data: dict) -> dict:
    choice = data["choices"][0]
    message = choice["message"]

    reply_text = message.get("content")
    tool_calls = []

    if message.get("tool_calls"):
        for tc in message["tool_calls"]:
            try:
                arguments = json.loads(tc["function"]["arguments"])
            except (json.JSONDecodeError, KeyError):
                arguments = {}
            tool_calls.append({
                "id": tc["id"],
                "name": tc["function"]["name"],
                "arguments": arguments,
            })

    return {"reply_text": reply_text, "tool_calls": tool_calls}


async def call_llm(messages: list[dict], tools: list[dict]) -> dict:
    url = f"{settings.groq_base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": settings.groq_model,
        "messages": messages,
        "temperature": 0.3,
    }
    if tools:
        body["tools"] = tools

    last_error = None

    for attempt in range(1 + RATE_LIMIT_MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                response = await client.post(url, headers=headers, json=body)

            if response.status_code == 429:
                last_error = LLMRateLimitError("Rate limited by provider")
                if attempt < RATE_LIMIT_MAX_RETRIES:
                    logger.warning("Rate limited, waiting %ds (attempt %d)", RATE_LIMIT_WAIT_SECONDS, attempt + 1)
                    await asyncio.sleep(RATE_LIMIT_WAIT_SECONDS)
                    continue
                raise last_error

            response.raise_for_status()
            data = response.json()
            return _parse_response(data)

        except httpx.TimeoutException:
            if attempt == 0:
                logger.warning("LLM timeout, retrying once")
                continue
            raise LLMTimeoutError("LLM request timed out after retry")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                continue
            raise LLMResponseError(f"LLM returned HTTP {e.response.status_code}")

    raise last_error or LLMResponseError("LLM request failed after retries")
