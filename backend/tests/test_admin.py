import io
from unittest.mock import AsyncMock, patch

import pytest

from app.config import settings
from app.data.admin_products import (
    create_product,
    get_all_categories,
    get_product_by_id,
    list_products,
    name_exists,
    names_that_exist,
    set_active_status,
    update_product,
    generate_product_id,
    bulk_insert_products,
)

_TEST_EMBEDDING = [0.1] * settings.embedding_dimensions


def _mock_embed():
    """Mock embed_documents to return a fake vector for each input."""
    async def fake_embed(items):
        return [_TEST_EMBEDDING for _ in items]
    return patch("app.api.admin.embed_documents", side_effect=fake_embed)


# --- Data layer tests ---


class TestAdminDataLayer:
    async def test_get_all_categories(self, seeded_session):
        cats = await get_all_categories(seeded_session)
        assert "phone" in cats
        assert "laptop" in cats

    async def test_list_products_default(self, seeded_session):
        result = await list_products(seeded_session)
        assert result["total"] >= 5
        assert len(result["products"]) >= 5

    async def test_list_products_filter_category(self, seeded_session):
        result = await list_products(seeded_session, category="phone")
        for p in result["products"]:
            assert p["category"] == "phone"

    async def test_list_products_filter_active(self, seeded_session):
        result = await list_products(seeded_session, is_active=True)
        for p in result["products"]:
            assert p["is_active"] is True

    async def test_list_products_includes_inactive(self, seeded_session):
        result = await list_products(seeded_session)
        ids = [p["id"] for p in result["products"]]
        assert "PHN099" in ids

    async def test_list_products_search(self, seeded_session):
        result = await list_products(seeded_session, search="Phone A")
        assert result["total"] >= 1
        assert any(p["name"] == "Phone A" for p in result["products"])

    async def test_list_products_pagination(self, seeded_session):
        result = await list_products(seeded_session, page_size=2, page=1)
        assert len(result["products"]) == 2
        assert result["page"] == 1

    async def test_get_product_by_id(self, seeded_session):
        product = await get_product_by_id(seeded_session, "PHN001")
        assert product is not None
        assert product["id"] == "PHN001"
        assert "has_embedding" in product

    async def test_get_product_by_id_not_found(self, seeded_session):
        product = await get_product_by_id(seeded_session, "FAKE999")
        assert product is None

    async def test_name_exists(self, seeded_session):
        assert await name_exists(seeded_session, "Phone A") is True
        assert await name_exists(seeded_session, "Nonexistent Product") is False

    async def test_name_exists_excludes_id(self, seeded_session):
        assert await name_exists(seeded_session, "Phone A", exclude_id="PHN001") is False

    async def test_names_that_exist(self, seeded_session):
        result = await names_that_exist(seeded_session, ["Phone A", "Nonexistent"])
        assert "Phone A" in result
        assert "Nonexistent" not in result

    async def test_generate_product_id(self, seeded_session):
        pid = await generate_product_id(seeded_session, "phone")
        assert pid.startswith("PHN")
        num = int(pid[3:])
        assert num > 0

    async def test_create_product(self, session):
        product = await create_product(session, {
            "name": "Test Product",
            "category": "phone",
            "price": 9999,
            "stock": 5,
            "brand": "TestBrand",
        })
        assert product.id.startswith("PHN")
        assert product.name == "Test Product"
        assert product.is_active is True

    async def test_update_product(self, seeded_session):
        updated = await update_product(seeded_session, "PHN001", {"price": 8888})
        assert updated is not None
        assert float(updated.price) == 8888

    async def test_set_active_status(self, seeded_session):
        result = await set_active_status(seeded_session, "PHN001", is_active=False)
        assert result is not None
        assert result.is_active is False

    async def test_bulk_insert(self, session):
        data = [
            {"name": "Bulk A", "category": "phone", "price": 1000, "stock": 1},
            {"name": "Bulk B", "category": "laptop", "price": 2000, "stock": 2},
        ]
        products = await bulk_insert_products(session, data)
        assert len(products) == 2
        assert products[0].id.startswith("PHN")
        assert products[1].id.startswith("LAP")


# --- API endpoint tests (using HTTPX + FastAPI TestClient) ---


@pytest.fixture
def admin_client(seeded_session):
    """Create a test client with the seeded session and admin auth injected."""
    from httpx import ASGITransport, AsyncClient
    from app.main import app
    from app.data.database import get_db
    from tests.token_helpers import make_admin_headers

    async def override_get_db():
        yield seeded_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    client = AsyncClient(
        transport=transport, base_url="http://test", headers=make_admin_headers(),
    )
    return client


class TestAdminEndpoints:
    async def test_get_categories(self, admin_client):
        async with admin_client as client:
            resp = await client.get("/admin/categories")
        assert resp.status_code == 200
        cats = resp.json()
        assert "phone" in cats

    async def test_list_products(self, admin_client):
        async with admin_client as client:
            resp = await client.get("/admin/products")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "products" in data
        assert data["total"] >= 5

    async def test_list_products_filter(self, admin_client):
        async with admin_client as client:
            resp = await client.get("/admin/products", params={"category": "phone", "is_active": True})
        assert resp.status_code == 200
        data = resp.json()
        for p in data["products"]:
            assert p["category"] == "phone"
            assert p["is_active"] is True

    async def test_get_product(self, admin_client):
        async with admin_client as client:
            resp = await client.get("/admin/products/PHN001")
        assert resp.status_code == 200
        assert resp.json()["id"] == "PHN001"

    async def test_get_product_not_found(self, admin_client):
        async with admin_client as client:
            resp = await client.get("/admin/products/FAKE999")
        assert resp.status_code == 404

    async def test_create_product(self, admin_client):
        with _mock_embed():
            async with admin_client as client:
                resp = await client.post("/admin/products", json={
                    "name": "New Test Phone",
                    "category": "phone",
                    "price": 12999,
                    "stock": 10,
                    "brand": "TestBrand",
                })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "New Test Phone"
        assert data["id"].startswith("PHN")

    async def test_create_product_duplicate_name(self, admin_client):
        with _mock_embed():
            async with admin_client as client:
                resp = await client.post("/admin/products", json={
                    "name": "Phone A",
                    "category": "phone",
                    "price": 5000,
                    "stock": 1,
                })
        assert resp.status_code == 409

    async def test_update_product(self, admin_client):
        with _mock_embed():
            async with admin_client as client:
                resp = await client.put("/admin/products/PHN001", json={"price": 7777})
        assert resp.status_code == 200
        assert resp.json()["price"] == 7777

    async def test_update_product_not_found(self, admin_client):
        async with admin_client as client:
            resp = await client.put("/admin/products/FAKE999", json={"price": 100})
        assert resp.status_code == 404

    async def test_delete_product(self, admin_client):
        async with admin_client as client:
            resp = await client.delete("/admin/products/PHN001")
        assert resp.status_code == 200
        assert resp.json()["status"] == "deactivated"

    async def test_reactivate_product(self, admin_client):
        async with admin_client as client:
            await client.delete("/admin/products/PHN001")
            resp = await client.post("/admin/products/PHN001/reactivate")
        assert resp.status_code == 200
        assert resp.json()["is_active"] is True

    async def test_upload_csv(self, admin_client):
        csv_content = "name,category,price,stock,brand\nCSV Phone,phone,5000,10,TestBrand\n"
        with _mock_embed():
            async with admin_client as client:
                resp = await client.post(
                    "/admin/products/upload",
                    files={"file": ("products.csv", csv_content.encode(), "text/csv")},
                )
        assert resp.status_code == 200
        data = resp.json()
        assert data["added"] == 1
        assert data["skipped"] == 0

    async def test_upload_csv_skip_existing(self, admin_client):
        csv_content = "name,category,price,stock\nPhone A,phone,5000,10\nNew Upload,phone,6000,5\n"
        with _mock_embed():
            async with admin_client as client:
                resp = await client.post(
                    "/admin/products/upload",
                    files={"file": ("products.csv", csv_content.encode(), "text/csv")},
                )
        assert resp.status_code == 200
        data = resp.json()
        assert data["added"] == 1
        assert data["skipped"] == 1
        assert "Phone A" in data["skipped_names"]

    async def test_upload_csv_validation_error(self, admin_client):
        csv_content = "name,category,price,stock\n,phone,5000,10\n"
        async with admin_client as client:
            resp = await client.post(
                "/admin/products/upload",
                files={"file": ("products.csv", csv_content.encode(), "text/csv")},
            )
        assert resp.status_code == 400

    async def test_upload_csv_missing_columns(self, admin_client):
        csv_content = "name,price\nTest,5000\n"
        async with admin_client as client:
            resp = await client.post(
                "/admin/products/upload",
                files={"file": ("products.csv", csv_content.encode(), "text/csv")},
            )
        assert resp.status_code == 400
        assert "Missing required columns" in resp.json()["detail"]
