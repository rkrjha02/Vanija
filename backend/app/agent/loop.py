import json
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.prompt import build_messages
from app.agent.state_block import format_state_block, update_state_block
from app.agent.validation import validate_tool_call
from app.config import settings
from app.data.conversations import get_or_create_conversation, update_shown_products
from app.data.messages import get_recent_messages, get_turn_messages, save_message
from app.providers.openai_compat import (
    LLMRateLimitError,
    LLMResponseError,
    LLMTimeoutError,
    call_llm,
)
from app.tools.definitions import get_tool_definitions
from app.tools.product_tools import TOOL_HANDLERS, build_search_label

logger = logging.getLogger(__name__)

FIXED_ROUND_LIMIT_MSG = "Sorry, I couldn't finish that. Please check your cart and try again."
FIXED_TIMEOUT_MSG = "Sorry, I'm having trouble right now. Please try again."
FIXED_RATE_LIMIT_MSG = "We're a bit busy right now. Please try again in a minute."
FIXED_ERROR_MSG = "Sorry, something went wrong. Please try again."


async def run_agent_loop(
    session: AsyncSession,
    customer_id: str,
    message_text: str,
) -> dict:
    conversation = await get_or_create_conversation(session, customer_id)
    conv_id = conversation["id"]
    shown_products = conversation["shown_products"]
    turn_id = str(uuid.uuid4())

    await save_message(session, conv_id, turn_id, "user", content=message_text)

    recent = await get_recent_messages(session, conv_id, settings.recent_messages_count)

    cards = []
    tools = get_tool_definitions()

    for round_num in range(settings.max_rounds):
        state_text = format_state_block(shown_products)
        turn_messages = await get_turn_messages(session, conv_id, turn_id)
        current_turn = [m for m in turn_messages if m["role"] != "user"] or []
        user_msg = {"role": "user", "content": message_text}

        llm_messages = build_messages(state_text, recent, [user_msg] + _format_for_llm(current_turn))

        try:
            llm_response = await call_llm(llm_messages, tools)
        except LLMTimeoutError:
            return await _finish_with_fixed_message(session, conv_id, turn_id, FIXED_TIMEOUT_MSG, cards)
        except LLMRateLimitError:
            return await _finish_with_fixed_message(session, conv_id, turn_id, FIXED_RATE_LIMIT_MSG, cards)
        except (LLMResponseError, Exception) as e:
            logger.error("LLM error: %s", e)
            return await _finish_with_fixed_message(session, conv_id, turn_id, FIXED_ERROR_MSG, cards)

        if not llm_response["tool_calls"]:
            reply_text = llm_response["reply_text"] or ""
            await save_message(session, conv_id, turn_id, "assistant", content=reply_text)
            return {"reply_text": reply_text, "cards": cards}

        await save_message(
            session, conv_id, turn_id, "assistant",
            content=llm_response.get("reply_text"),
            tool_calls=[
                {"id": tc["id"], "name": tc["name"], "arguments": tc["arguments"]}
                for tc in llm_response["tool_calls"]
            ],
        )

        for tc in llm_response["tool_calls"]:
            cleaned_args, error = validate_tool_call(tc["name"], tc["arguments"])

            if error:
                tool_result = {"status": "error", "message": error}
                await save_message(
                    session, conv_id, turn_id, "tool",
                    content=json.dumps(tool_result),
                    tool_call_id=tc["id"],
                )
                break

            try:
                handler = TOOL_HANDLERS[tc["name"]]["handle"]
                tool_result = await handler(session, cleaned_args)
            except Exception as e:
                logger.error("Tool error in %s: %s", tc["name"], e)
                tool_result = {"status": "error", "message": "Something went wrong. Please try again."}

            await save_message(
                session, conv_id, turn_id, "tool",
                content=json.dumps(tool_result),
                tool_call_id=tc["id"],
            )

            if tc["name"] == "search_products" and tool_result["status"] == "success":
                label = build_search_label(cleaned_args)
                shown_products = update_state_block(
                    shown_products, tool_result["products"], label
                )
                await update_shown_products(session, conv_id, shown_products)

            if tool_result.get("status") == "success":
                card = _build_card(tc["name"], tool_result)
                if card:
                    cards.append(card)

    return await _finish_with_fixed_message(session, conv_id, turn_id, FIXED_ROUND_LIMIT_MSG, cards)


def _format_for_llm(turn_messages: list[dict]) -> list[dict]:
    formatted = []
    for msg in turn_messages:
        if msg["role"] == "assistant":
            entry = {"role": "assistant", "content": msg.get("content") or ""}
            if msg.get("tool_calls"):
                entry["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["arguments"]),
                        },
                    }
                    for tc in msg["tool_calls"]
                ]
            formatted.append(entry)
        elif msg["role"] == "tool":
            formatted.append({
                "role": "tool",
                "content": msg["content"],
                "tool_call_id": msg["tool_call_id"],
            })
    return formatted


def _build_card(tool_name: str, result: dict) -> dict | None:
    if tool_name in ("search_products", "get_product_details"):
        return {"type": "products", "items": result.get("products", [])}
    return None


async def _finish_with_fixed_message(
    session: AsyncSession,
    conv_id: int,
    turn_id: str,
    message: str,
    cards: list,
) -> dict:
    await save_message(session, conv_id, turn_id, "assistant", content=message)
    return {"reply_text": message, "cards": cards}
