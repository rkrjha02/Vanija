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


def format_state_block(shown_products: list) -> str:
    if not shown_products:
        return ""

    lines = []
    for i, lst in enumerate(shown_products):
        if i == 0:
            prefix = "Latest list"
        else:
            prefix = "Earlier list"
        lines.append(f"{prefix} ({lst['label']}):")
        for p in lst["products"]:
            lines.append(f"  {p['position']}. {p['id']} - {p['name']}")

    return "\n".join(lines)
