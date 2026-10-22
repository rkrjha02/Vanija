from app.tools.registry import ALL_HANDLERS as TOOL_HANDLERS


def validate_tool_call(name: str, arguments: dict) -> tuple[dict | None, str | None]:
    if name not in TOOL_HANDLERS:
        return None, f"Unknown tool: {name}"

    arguments = {key: value for key, value in arguments.items() if value is not None}
    arguments.pop("customer_id", None)

    validator = TOOL_HANDLERS[name]["validate"]
    error = validator(arguments)
    if error:
        return None, error

    return arguments, None
