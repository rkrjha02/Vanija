import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.data.models import Product
from app.embeddings import EmbeddingError, embed_documents
from app.embeddings.gemini import MAX_TEXTS_PER_REQUEST

logger = logging.getLogger(__name__)

_sleep = asyncio.sleep


@dataclass
class ProductEmbedReport:
    embedded: int = 0
    skipped: int = 0
    failed: list[str] = field(default_factory=list)


class _Pacer:
    """Keeps embedding requests under the per-minute limit."""

    def __init__(self, requests_per_minute: int):
        self.min_gap = 60.0 / requests_per_minute
        self.last_call: float | None = None

    async def wait(self) -> None:
        if self.last_call is not None:
            remaining = self.min_gap - (time.monotonic() - self.last_call)
            if remaining > 0:
                await _sleep(remaining)
        self.last_call = time.monotonic()


def build_product_text(product: Product) -> str:
    """Build a combined text string from a product row for embedding."""
    lines = [f"{product.name} | Brand: {product.brand} | Category: {product.category}"]

    if product.short_description:
        lines.append(product.short_description)
    if product.description:
        lines.append(product.description)
    if product.specs:
        spec_parts = [f"{k}: {v}" for k, v in product.specs.items()]
        lines.append("Specs: " + ", ".join(spec_parts))
    if product.tags:
        lines.append("Tags: " + ", ".join(product.tags))

    return "\n".join(lines)


def product_text_hash(text: str) -> str:
    """Short fingerprint of the product text. Same text -> same hash."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


async def embed_products(session: AsyncSession) -> ProductEmbedReport:
    """Embed all products that are new or whose text changed."""
    report = ProductEmbedReport()

    result = await session.execute(
        select(Product).where(Product.is_active.is_(True)).order_by(Product.id)
    )
    all_products = result.scalars().all()

    to_embed: list[tuple[Product, str, str]] = []
    for product in all_products:
        text = build_product_text(product)
        text_hash = product_text_hash(text)
        if product.embedding is not None and product.embedding_hash == text_hash:
            report.skipped += 1
            continue
        to_embed.append((product, text, text_hash))

    if not to_embed:
        return report

    total = len(to_embed)
    pacer = _Pacer(settings.embedding_requests_per_minute)

    for batch_start in range(0, total, MAX_TEXTS_PER_REQUEST):
        batch = to_embed[batch_start : batch_start + MAX_TEXTS_PER_REQUEST]

        items = [(p.name, text) for p, text, _ in batch]
        try:
            await pacer.wait()
            vectors = await embed_documents(items)
        except EmbeddingError as exc:
            failed_ids = [p.id for p, _, _ in batch]
            logger.error("Embedding failed for products %s: %s", failed_ids, exc)
            report.failed.extend(failed_ids)
            continue

        for (product, _, text_hash), vector in zip(batch, vectors):
            await session.execute(
                update(Product)
                .where(Product.id == product.id)
                .values(embedding=vector, embedding_hash=text_hash)
            )
            report.embedded += 1

        await session.commit()
        print(f"  Embedded {min(batch_start + len(batch), total)}/{total} products...")

    return report
