"""Data layer for admin product management. Only this file writes to the products table."""

import json
import logging
from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.models import Product

logger = logging.getLogger(__name__)

CATEGORY_PREFIXES = {
    "phone": "PHN",
    "laptop": "LAP",
    "headphone": "HPH",
}
DEFAULT_PREFIX = "PRD"


def _product_to_admin_dict(row: Product) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "category": row.category,
        "brand": row.brand,
        "price": float(row.price) if isinstance(row.price, Decimal) else row.price,
        "stock": row.stock,
        "description": row.description,
        "short_description": row.short_description,
        "specs": row.specs,
        "tags": row.tags,
        "is_active": row.is_active,
        "has_embedding": row.embedding is not None,
    }


async def get_all_categories(session: AsyncSession) -> list[str]:
    result = await session.execute(
        select(Product.category).distinct().order_by(Product.category)
    )
    return [row[0] for row in result.all()]


async def list_products(
    session: AsyncSession,
    search: str | None = None,
    category: str | None = None,
    brand: str | None = None,
    is_active: bool | None = None,
    sort_by: str = "name",
    sort_order: str = "asc",
    page: int = 1,
    page_size: int = 20,
) -> dict:
    query = select(Product)

    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
    if category:
        query = query.where(func.lower(Product.category) == category.lower())
    if brand:
        query = query.where(func.lower(Product.brand) == brand.lower())
    if is_active is not None:
        query = query.where(Product.is_active.is_(is_active))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0

    sort_column = getattr(Product, sort_by, Product.name)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await session.execute(query)
    rows = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "products": [_product_to_admin_dict(r) for r in rows],
    }


async def get_product_by_id(session: AsyncSession, product_id: str) -> dict | None:
    result = await session.execute(
        select(Product).where(Product.id == product_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        return None
    return _product_to_admin_dict(row)


async def get_product_row(session: AsyncSession, product_id: str) -> Product | None:
    result = await session.execute(
        select(Product).where(Product.id == product_id)
    )
    return result.scalar_one_or_none()


async def name_exists(session: AsyncSession, name: str, exclude_id: str | None = None) -> bool:
    query = select(func.count()).where(func.lower(Product.name) == name.lower())
    if exclude_id:
        query = query.where(Product.id != exclude_id)
    count = (await session.execute(query)).scalar() or 0
    return count > 0


async def names_that_exist(session: AsyncSession, names: list[str]) -> set[str]:
    if not names:
        return set()
    lower_names = [n.lower() for n in names]
    result = await session.execute(
        select(Product.name).where(func.lower(Product.name).in_(lower_names))
    )
    return {row[0] for row in result.all()}


async def generate_product_id(session: AsyncSession, category: str) -> str:
    prefix = CATEGORY_PREFIXES.get(category.lower(), DEFAULT_PREFIX)
    result = await session.execute(
        select(Product.id)
        .where(Product.id.like(f"{prefix}%"))
        .order_by(Product.id.desc())
        .limit(1)
    )
    last_id = result.scalar_one_or_none()
    if last_id:
        num_part = last_id[len(prefix):]
        try:
            next_num = int(num_part) + 1
        except ValueError:
            next_num = 1
    else:
        next_num = 1
    return f"{prefix}{next_num:03d}"


async def create_product(session: AsyncSession, data: dict) -> Product:
    product_id = await generate_product_id(session, data["category"])
    product = Product(
        id=product_id,
        name=data["name"],
        category=data["category"].lower(),
        brand=data.get("brand"),
        price=data["price"],
        stock=data["stock"],
        description=data.get("description"),
        short_description=data.get("short_description"),
        specs=data.get("specs"),
        tags=data.get("tags"),
        is_active=True,
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product


async def update_product(session: AsyncSession, product_id: str, data: dict) -> Product | None:
    row = await get_product_row(session, product_id)
    if row is None:
        return None
    for key, value in data.items():
        if key == "category" and value is not None:
            value = value.lower()
        setattr(row, key, value)
    await session.commit()
    await session.refresh(row)
    return row


async def set_active_status(session: AsyncSession, product_id: str, is_active: bool) -> Product | None:
    result = await session.execute(
        update(Product)
        .where(Product.id == product_id)
        .values(is_active=is_active)
        .returning(Product)
    )
    await session.commit()
    row = result.scalar_one_or_none()
    return row


async def bulk_insert_products(session: AsyncSession, products_data: list[dict]) -> list[Product]:
    products = []
    for data in products_data:
        product_id = await generate_product_id(session, data["category"])
        product = Product(
            id=product_id,
            name=data["name"],
            category=data["category"].lower(),
            brand=data.get("brand"),
            price=data["price"],
            stock=data["stock"],
            description=data.get("description"),
            short_description=data.get("short_description"),
            specs=data.get("specs"),
            tags=data.get("tags"),
            is_active=True,
        )
        session.add(product)
        products.append(product)
    await session.commit()
    for p in products:
        await session.refresh(p)
    return products


async def update_product_embedding(
    session: AsyncSession, product_id: str, embedding: list[float], embedding_hash: str
) -> None:
    await session.execute(
        update(Product)
        .where(Product.id == product_id)
        .values(embedding=embedding, embedding_hash=embedding_hash)
    )
    await session.commit()
