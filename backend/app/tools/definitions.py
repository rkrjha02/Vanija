VALID_CATEGORIES: list[str] = []


def get_tool_definitions() -> list[dict]:
    # The LLM often sends null for an optional field it isn't using. Groq checks calls
    # against this schema and rejects null for a plain "integer"/"string" field.
    tools = _tool_definitions()
    for tool in tools:
        params = tool["function"]["parameters"]
        required = set(params.get("required", []))
        for name, prop in params["properties"].items():
            if name not in required:
                params["properties"][name] = _nullable(prop)
    return tools


def _nullable(prop: dict) -> dict:
    prop = dict(prop)
    prop["type"] = [prop["type"], "null"]
    if "enum" in prop:
        prop["enum"] = [*prop["enum"], None]
    return prop


def _tool_definitions() -> list[dict]:
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
        {
            "type": "function",
            "function": {
                "name": "view_saved_addresses",
                "description": (
                    "List the customer's saved delivery addresses. "
                    "Always call this before place_order."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "place_order",
                "description": (
                    "Prepare a Cash on Delivery order from the cart. It does NOT place the order: "
                    "it shows the customer a Confirm button. "
                    "Send either address_id of a saved address, or all six new address fields, never both."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "address_id": {
                            "type": "integer",
                            "description": "ID of a saved address from view_saved_addresses.",
                        },
                        "delivery_name": {"type": "string", "description": "Recipient's full name."},
                        "delivery_phone": {"type": "string", "description": "10-digit phone number."},
                        "address_line": {"type": "string", "description": "House, street, area."},
                        "city": {"type": "string"},
                        "state": {"type": "string"},
                        "pincode": {"type": "string", "description": "6-digit pincode."},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "cancel_order",
                "description": (
                    "Prepare cancelling a placed order. It does NOT cancel: it shows the customer a "
                    "'Yes, cancel order' button. Leave order_id out if the customer has only one order."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "integer",
                            "description": "The order to cancel, if the customer named one.",
                        },
                    },
                },
            },
        },
    ]
