VALID_CATEGORIES: list[str] = []


def get_tool_definitions() -> list[dict]:
    category_desc = ", ".join(VALID_CATEGORIES) if VALID_CATEGORIES else "phone, laptop, headphone"

    return [
        {
            "type": "function",
            "function": {
                "name": "search_products",
                "description": (
                    "Search for products by category. Use when the customer asks to see, find, or browse products. "
                    "Category is required."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": VALID_CATEGORIES if VALID_CATEGORIES else ["phone", "laptop", "headphone"],
                            "description": f"Product category. Must be one of: {category_desc}.",
                        },
                        "min_price": {
                            "type": "integer",
                            "description": "Minimum price in rupees.",
                        },
                        "max_price": {
                            "type": "integer",
                            "description": "Maximum price in rupees.",
                        },
                        "brand": {
                            "type": "string",
                            "description": "Filter by brand name (case-insensitive).",
                        },
                        "keyword": {
                            "type": "string",
                            "description": "Search keyword matched against product name and description.",
                        },
                        "sort_by": {
                            "type": "string",
                            "enum": ["price_low_to_high", "price_high_to_low"],
                            "description": "Sort order. Default is price_low_to_high.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of results to return, 1 to 10. Default is 5.",
                        },
                    },
                    "required": ["category"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_product_details",
                "description": (
                    "Get full details for 1 to 3 products by their IDs. "
                    "Use when the customer wants more information about specific products. "
                    "Does not change the shown products list."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 1,
                            "maxItems": 3,
                            "description": "List of 1 to 3 product IDs.",
                        },
                    },
                    "required": ["product_ids"],
                },
            },
        },
    ]
