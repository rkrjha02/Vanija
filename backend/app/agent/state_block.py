from app.config import settings

MAX_LISTS = 3


def update_state_block(
    current: list,
    new_products: list[dict],
    label: str,
) -> list:
    new_list = {
        "label": label,
        "products": [
            {"position": p["position"], "id": p["id"], "name": p["name"]}
            for p in new_products
        ],
    }

    updated = [new_list] + current

    total = sum(len(lst["products"]) for lst in updated)
    while total > settings.max_shown_products and len(updated) > 1:
        total -= len(updated[-1]["products"])
        updated.pop()

    if len(updated) > MAX_LISTS:
        updated = updated[:MAX_LISTS]

    return updated


def format_state_block(
    shown_products: list,
    last_search_context: dict | None = None,
) -> str:
    lines = []

    if last_search_context:
        query = last_search_context.get("query", "")
        offset = last_search_context.get("offset", 0)
        total_count = last_search_context.get("total_count", 0)
        filters = last_search_context.get("filters", {})
        count_returned = min(settings.default_search_limit, max(0, total_count - offset))
        start = offset + 1
        end = offset + count_returned
        ctx_line = f"Last product search: query='{query}', showed results {start}-{end} of {total_count} total."
        if filters:
            filter_parts = [f"{k}={v}" for k, v in sorted(filters.items())]
            ctx_line += f" Filters: {', '.join(filter_parts)}."
        ctx_line += " The customer can ask to see more."
        lines.append(ctx_line)

    for i, lst in enumerate(shown_products):
        if i == 0:
            prefix = "Latest list"
        else:
            prefix = "Earlier list"
        lines.append(f"{prefix} ({lst['label']}):")
        for p in lst["products"]:
            lines.append(f"  {p['position']}. {p['id']} - {p['name']}")

    if not lines:
        return ""

    return "\n".join(lines)
