from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

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
    category: str,
    min_price: int | None = None,
    max_price: int | None = None,
    brand: str | None = None,
    keyword: str | None = None,
    sort_by: str = "price_low_to_high",
    limit: int = 5,
) -> dict:
    query = select(Product).where(
        Product.is_active.is_(True),
        Product.category == category,
    )

    if min_price is not None:
        query = query.where(Product.price >= min_price)
    if max_price is not None:
        query = query.where(Product.price <= max_price)
    if brand:
        query = query.where(func.lower(Product.brand) == brand.lower())
    if keyword:
        pattern = f"%{keyword}%"
        query = query.where(
            Product.name.ilike(pattern) | Product.description.ilike(pattern)
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0

    if sort_by == "price_high_to_low":
        query = query.order_by(Product.price.desc())
    else:
        query = query.order_by(Product.price.asc())

    query = query.limit(limit)
    result = await session.execute(query)
    rows = result.scalars().all()

    products = []
    for i, row in enumerate(rows, start=1):
        product = _product_to_dict(row)
        product["position"] = i
        products.append(product)

    return {"total_matches": total, "products": products}


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
