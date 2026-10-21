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
        {
            "type": "function",
            "function": {
                "name": "add_to_cart",
                "description": (
                    "Add a product to the customer's cart. "
                    "Use when the customer says 'add', 'I want', 'I'll take', or similar. "
                    "If the product is already in the cart, the quantity increases."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_id": {
                            "type": "string",
                            "description": "The product ID to add.",
                        },
                        "quantity": {
                            "type": "integer",
                            "description": "How many to add, 1 to 10. Default is 1.",
                        },
                    },
                    "required": ["product_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "update_cart_item",
                "description": (
                    "Change the quantity of a product already in the cart. "
                    "The quantity is the NEW TOTAL, not an amount to add or remove. "
                    "Set quantity to 0 to remove the item entirely. "
                    "Use when the customer says 'make it 3', 'change to 2', 'remove the phone', etc."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_id": {
                            "type": "string",
                            "description": "The product ID to update.",
                        },
                        "quantity": {
                            "type": "integer",
                            "description": "New total quantity, 0 to 10. Use 0 to remove the item.",
                        },
                    },
                    "required": ["product_id", "quantity"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "view_cart",
                "description": (
                    "Show the customer's current cart contents with prices and totals. "
                    "Use when the customer asks 'what's in my cart?', 'show my cart', etc."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            },
        },
    ]
