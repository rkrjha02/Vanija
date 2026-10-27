import csv
import io
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.admin_products import (
    bulk_insert_products,
    create_product,
    get_all_categories,
    get_product_by_id,
    get_product_row,
    list_products,
    name_exists,
    names_that_exist,
    set_active_status,
    update_product,
    update_product_embedding,
    _product_to_admin_dict,
)
from app.data.database import get_db
from app.embeddings import EmbeddingError, embed_documents
from app.ingest.product_embeddings import build_product_text, product_text_hash

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

EMBEDDED_FIELDS = {"name", "brand", "category", "short_description", "description", "specs", "tags"}


class ProductCreate(BaseModel):
    name: str
    category: str
    price: float
    stock: int
    brand: str | None = None
    short_description: str | None = None
    description: str | None = None
    specs: dict | None = None
    tags: list[str] | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be empty")
        return v.strip()

    @field_validator("price")
    @classmethod
    def price_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("price must be >= 0")
        return v

    @field_validator("stock")
    @classmethod
    def stock_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("stock must be >= 0")
        return v


class ProductUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    price: float | None = None
    stock: int | None = None
    brand: str | None = None
    short_description: str | None = None
    description: str | None = None
    specs: dict | None = None
    tags: list[str] | None = None
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("name must not be empty")
        return v.strip() if v else v

    @field_validator("price")
    @classmethod
    def price_non_negative(cls, v: float | None) -> float | None:
        if v is not None and v < 0:
            raise ValueError("price must be >= 0")
        return v

    @field_validator("stock")
    @classmethod
    def stock_non_negative(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError("stock must be >= 0")
        return v


async def _embed_product(session: AsyncSession, product) -> None:
    """Build text, embed, and store the embedding for a single product."""
    text = build_product_text(product)
    text_h = product_text_hash(text)
    try:
        vectors = await embed_documents([(product.name, text)])
        await update_product_embedding(session, product.id, vectors[0], text_h)
    except EmbeddingError:
        logger.warning("Embedding failed for product %s; stored without embedding", product.id)


# --- Endpoints ---


@router.get("/categories")
async def admin_categories(session: AsyncSession = Depends(get_db)):
    return await get_all_categories(session)


@router.get("/products")
async def admin_list_products(
    search: str | None = None,
    category: str | None = None,
    brand: str | None = None,
    is_active: bool | None = None,
    sort_by: str = "name",
    sort_order: str = "asc",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
):
    return await list_products(
        session,
        search=search,
        category=category,
        brand=brand,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )


@router.get("/products/{product_id}")
async def admin_get_product(product_id: str, session: AsyncSession = Depends(get_db)):
    product = await get_product_by_id(session, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/products", status_code=201)
async def admin_create_product(body: ProductCreate, session: AsyncSession = Depends(get_db)):
    if await name_exists(session, body.name):
        raise HTTPException(status_code=409, detail="A product with this name already exists")

    product = await create_product(session, body.model_dump())
    await _embed_product(session, product)
    await session.refresh(product)
    return _product_to_admin_dict(product)


@router.put("/products/{product_id}")
async def admin_update_product(
    product_id: str, body: ProductUpdate, session: AsyncSession = Depends(get_db)
):
    existing = await get_product_row(session, product_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Product not found")

    changes = body.model_dump(exclude_unset=True)
    if not changes:
        return _product_to_admin_dict(existing)

    if "name" in changes and changes["name"]:
        if await name_exists(session, changes["name"], exclude_id=product_id):
            raise HTTPException(status_code=409, detail="A product with this name already exists")

    updated = await update_product(session, product_id, changes)

    needs_reembed = any(k in EMBEDDED_FIELDS for k in changes)
    if needs_reembed:
        await _embed_product(session, updated)
        await session.refresh(updated)

    return _product_to_admin_dict(updated)


@router.delete("/products/{product_id}")
async def admin_delete_product(product_id: str, session: AsyncSession = Depends(get_db)):
    product = await set_active_status(session, product_id, is_active=False)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"status": "deactivated", "product_id": product_id}


@router.post("/products/{product_id}/reactivate")
async def admin_reactivate_product(product_id: str, session: AsyncSession = Depends(get_db)):
    product = await set_active_status(session, product_id, is_active=True)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return _product_to_admin_dict(product)


@router.post("/products/upload")
async def admin_upload_products(file: UploadFile, session: AsyncSession = Depends(get_db)):
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV file is empty or has no header")

    required_columns = {"name", "category", "price", "stock"}
    missing = required_columns - set(reader.fieldnames)
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {', '.join(sorted(missing))}",
        )

    rows: list[dict] = []
    errors: list[dict] = []
    for row_num, row in enumerate(reader, start=2):
        row_errors = _validate_csv_row(row, row_num)
        if row_errors:
            errors.extend(row_errors)
            continue
        rows.append(_parse_csv_row(row))

    if errors:
        raise HTTPException(status_code=400, detail={"message": "Validation failed", "errors": errors})

    all_names = [r["name"] for r in rows]
    existing_names = await names_that_exist(session, all_names)
    skipped = []
    to_insert = []
    for r in rows:
        if r["name"].lower() in {n.lower() for n in existing_names}:
            skipped.append(r["name"])
        else:
            to_insert.append(r)

    inserted = []
    if to_insert:
        inserted = await bulk_insert_products(session, to_insert)

    embedded_count = 0
    for product in inserted:
        try:
            await _embed_product(session, product)
            embedded_count += 1
        except Exception:
            logger.warning("Embedding failed for uploaded product %s", product.id)

    return {
        "added": len(inserted),
        "skipped": len(skipped),
        "skipped_names": skipped,
        "embedded": embedded_count,
        "errors": [],
    }


def _validate_csv_row(row: dict, row_num: int) -> list[dict]:
    errors = []
    if not row.get("name", "").strip():
        errors.append({"row": row_num, "reason": "name is empty"})
    if not row.get("category", "").strip():
        errors.append({"row": row_num, "reason": "category is empty"})

    price_str = row.get("price", "").strip()
    if not price_str:
        errors.append({"row": row_num, "reason": "price is empty"})
    else:
        try:
            price = float(price_str)
            if price < 0:
                errors.append({"row": row_num, "reason": "price must be >= 0"})
        except ValueError:
            errors.append({"row": row_num, "reason": f"price is not a number: {price_str}"})

    stock_str = row.get("stock", "").strip()
    if not stock_str:
        errors.append({"row": row_num, "reason": "stock is empty"})
    else:
        try:
            stock = int(stock_str)
            if stock < 0:
                errors.append({"row": row_num, "reason": "stock must be >= 0"})
        except ValueError:
            errors.append({"row": row_num, "reason": f"stock is not an integer: {stock_str}"})

    specs_str = row.get("specs", "").strip()
    if specs_str:
        try:
            json.loads(specs_str)
        except json.JSONDecodeError:
            errors.append({"row": row_num, "reason": "specs is not valid JSON"})

    return errors


def _parse_csv_row(row: dict) -> dict:
    data: dict = {
        "name": row["name"].strip(),
        "category": row["category"].strip().lower(),
        "price": float(row["price"].strip()),
        "stock": int(row["stock"].strip()),
    }
    if row.get("brand", "").strip():
        data["brand"] = row["brand"].strip()
    if row.get("short_description", "").strip():
        data["short_description"] = row["short_description"].strip()
    if row.get("description", "").strip():
        data["description"] = row["description"].strip()
    if row.get("tags", "").strip():
        data["tags"] = [t.strip() for t in row["tags"].split(",") if t.strip()]
    if row.get("specs", "").strip():
        data["specs"] = json.loads(row["specs"].strip())
    return data
