from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.data.models import Product

KEY_SPECS = {
    "phone": ["ram_gb", "storage_gb", "battery_mah", "camera_mp"],
    "laptop": ["ram_gb", "storage_gb", "display_inch", "processor"],
    "headphone": ["battery_hours", "noise_cancelling", "connectivity"],
}


def _pick_key_specs(category: str, specs: dict | None) -> dict:
    if not specs:
        return {}
    keys = KEY_SPECS.get(category, [])
    return {k: specs[k] for k in keys if k in specs}


def _product_to_dict(row: Product, include_all_specs: bool = False) -> dict:
    result = {
        "id": row.id,
        "name": row.name,
        "brand": row.brand,
        "category": row.category,
        "price": float(row.price) if isinstance(row.price, Decimal) else row.price,
        "in_stock": row.stock > 0,
    }
    if include_all_specs:
        result["units_left"] = row.stock
        result["description"] = row.description
        result["specs"] = row.specs or {}
    else:
        result["key_specs"] = _pick_key_specs(row.category, row.specs)
    return result


async def get_categories(session: AsyncSession) -> list[str]:
    result = await session.execute(
        select(Product.category)
        .where(Product.is_active.is_(True))
        .distinct()
        .order_by(Product.category)
    )
    return [row[0] for row in result.all()]


async def search_products(
    session: AsyncSession,
    query_embedding: list[float],
    category: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    brand: str | None = None,
    limit: int = 5,
    min_similarity: float | None = None,
) -> dict:
    if min_similarity is None:
        min_similarity = settings.product_min_similarity

    distance = Product.embedding.cosine_distance(query_embedding)
    query = select(Product, (1 - distance).label("similarity")).where(
        Product.is_active.is_(True),
        Product.embedding.isnot(None),
    )

    if category is not None:
        query = query.where(func.lower(Product.category) == category.lower())
    if min_price is not None:
        query = query.where(Product.price >= min_price)
    if max_price is not None:
        query = query.where(Product.price <= max_price)
    if brand:
        query = query.where(func.lower(Product.brand) == brand.lower())

    query = query.where(distance <= 1 - min_similarity)
    query = query.order_by(distance).limit(limit)

    result = await session.execute(query)
    rows = result.all()

    products = []
    for i, (row, similarity) in enumerate(rows, start=1):
        product = _product_to_dict(row)
        product["position"] = i
        products.append(product)

    return {"total_matches": len(products), "products": products}


async def get_product_details(
    session: AsyncSession, product_ids: list[str]
) -> list[dict]:
    result = await session.execute(
        select(Product).where(Product.id.in_(product_ids))
    )
    found = {row.id: row for row in result.scalars().all()}

    details = []
    for pid in product_ids:
        if pid in found:
            row = found[pid]
            if not row.is_active:
                details.append({"id": pid, "status": "not_found"})
            else:
                details.append(_product_to_dict(row, include_all_specs=True))
        else:
            details.append({"id": pid, "status": "not_found"})
    return details
