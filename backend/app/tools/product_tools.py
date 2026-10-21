import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.data.products import (
    get_product_details as db_get_product_details,
    search_products as db_search_products,
)
from app.tools.definitions import VALID_CATEGORIES

logger = logging.getLogger(__name__)


def validate_search_products(args: dict) -> str | None:
    category = args.get("category")
    if not category:
        return "category is required"
    if category not in VALID_CATEGORIES:
        return f"category must be one of: {', '.join(VALID_CATEGORIES)}"

    limit = args.get("limit")
    if limit is not None:
        if not isinstance(limit, int) or limit < 1 or limit > 10:
            return "limit must be between 1 and 10"

    min_price = args.get("min_price")
    if min_price is not None and (not isinstance(min_price, int) or min_price < 0):
        return "min_price must be a non-negative integer"

    max_price = args.get("max_price")
    if max_price is not None and (not isinstance(max_price, int) or max_price < 0):
        return "max_price must be a non-negative integer"

    sort_by = args.get("sort_by")
    if sort_by and sort_by not in ("price_low_to_high", "price_high_to_low"):
        return "sort_by must be price_low_to_high or price_high_to_low"

    return None


def validate_get_product_details(args: dict) -> str | None:
    product_ids = args.get("product_ids")
    if not product_ids:
        return "product_ids is required"
    if not isinstance(product_ids, list):
        return "product_ids must be a list"
    if len(product_ids) < 1 or len(product_ids) > 3:
        return "product_ids must contain 1 to 3 IDs"
    return None


async def handle_search_products(session: AsyncSession, args: dict) -> dict:
    result = await db_search_products(
        session=session,
        category=args["category"],
        min_price=args.get("min_price"),
        max_price=args.get("max_price"),
        brand=args.get("brand"),
        keyword=args.get("keyword"),
        sort_by=args.get("sort_by", "price_low_to_high"),
        limit=args.get("limit", settings.default_search_limit),
    )

    if not result["products"]:
        return {"status": "no_match", "total_matches": 0, "products": []}

    return {
        "status": "success",
        "total_matches": result["total_matches"],
        "products": result["products"],
    }


async def handle_get_product_details(session: AsyncSession, args: dict) -> dict:
    details = await db_get_product_details(session, args["product_ids"])
    return {"status": "success", "products": details}


TOOL_HANDLERS = {
    "search_products": {
        "validate": validate_search_products,
        "handle": handle_search_products,
    },
    "get_product_details": {
        "validate": validate_get_product_details,
        "handle": handle_get_product_details,
    },
}


def build_search_label(args: dict) -> str:
    parts = [f"{args['category']}s"]
    if args.get("brand"):
        parts = [f"{args['brand']} {parts[0]}"]
    if args.get("max_price") and args.get("min_price"):
        parts.append(f"₹{args['min_price']:,}–₹{args['max_price']:,}")
    elif args.get("max_price"):
        parts.append(f"under ₹{args['max_price']:,}")
    elif args.get("min_price"):
        parts.append(f"above ₹{args['min_price']:,}")
    if args.get("keyword"):
        parts.append(f'"{args["keyword"]}"')
    return " ".join(parts)
