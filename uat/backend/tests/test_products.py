"""
Unit tests for the /api/products endpoints (SDT1-95).

Verifies:
- GET /api/products returns all products
- GET /api/products/{id} returns 404 for a missing product
- POST /api/products returns 401 without authentication
- POST /api/products creates a product with valid auth and body
- PUT /api/products/{id} returns 401 without authentication
- PUT /api/products/{id} returns 404 for a missing product (with auth)
- DELETE /api/products/{id} returns 401 without authentication
- DELETE /api/products/{id} removes a product with valid auth
"""

import sys
import os
import uuid
import pytest
from unittest.mock import MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from products_router import router as products_router, _require_auth
from database import get_db


PRODUCT_ID = str(uuid.uuid4())


class _MockProduct:
    id = PRODUCT_ID
    name = "Acme App"
    jira_project_key = "ACME"
    jira_base_url = "https://acme.atlassian.net"
    github_org = "acmeorg"
    github_repo = "acme-app"
    railway_project_id = "proj-abc"
    railway_backend_service_name = "acme-backend"
    railway_frontend_service_name = "acme-frontend"


_mock_product = _MockProduct()


def _make_mock_db(product=_mock_product, product_list=None):
    if product_list is None:
        product_list = [_mock_product]
    db = MagicMock()
    q = MagicMock()
    db.query.return_value = q
    q.order_by.return_value.all.return_value = product_list
    q.filter.return_value.first.return_value = product
    return db


def _db_override(db):
    def _inner():
        yield db
    return _inner


def _auth_override():
    return {"sub": "user-123", "email": "admin@test.com"}


@pytest.fixture
def client_public():
    """DB mocked, no auth override (for public GET endpoints)."""
    app = FastAPI()
    app.include_router(products_router)
    app.dependency_overrides[get_db] = _db_override(_make_mock_db())
    return TestClient(app)


@pytest.fixture
def client_auth():
    """DB mocked and auth bypassed."""
    app = FastAPI()
    app.include_router(products_router)
    app.dependency_overrides[get_db] = _db_override(_make_mock_db())
    app.dependency_overrides[_require_auth] = _auth_override
    return TestClient(app)


@pytest.fixture
def client_no_auth():
    """DB mocked, no auth override — write endpoints return 401."""
    app = FastAPI()
    app.include_router(products_router)
    app.dependency_overrides[get_db] = _db_override(_make_mock_db())
    return TestClient(app)


class TestListProducts:
    def test_returns_product_list(self, client_public):
        resp = client_public.get("/api/products")
        assert resp.status_code == 200
        data = resp.json()
        assert "products" in data
        assert len(data["products"]) == 1
        p = data["products"][0]
        assert p["name"] == "Acme App"
        assert p["jira_project_key"] == "ACME"
        assert p["jira_base_url"] == "https://acme.atlassian.net"
        assert p["github_org"] == "acmeorg"
        assert p["github_repo"] == "acme-app"
        assert p["railway_project_id"] == "proj-abc"
        assert p["railway_backend_service_name"] == "acme-backend"
        assert p["railway_frontend_service_name"] == "acme-frontend"

    def test_returns_empty_list_when_no_products(self):
        app = FastAPI()
        app.include_router(products_router)
        app.dependency_overrides[get_db] = _db_override(_make_mock_db(product_list=[]))
        client = TestClient(app)
        resp = client.get("/api/products")
        assert resp.status_code == 200
        assert resp.json() == {"products": []}


class TestGetProduct:
    def test_returns_product(self, client_public):
        resp = client_public.get(f"/api/products/{PRODUCT_ID}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Acme App"
        assert data["jira_base_url"] == "https://acme.atlassian.net"

    def test_returns_404_for_missing(self):
        app = FastAPI()
        app.include_router(products_router)
        app.dependency_overrides[get_db] = _db_override(_make_mock_db(product=None))
        client = TestClient(app)
        resp = client.get("/api/products/nonexistent-id")
        assert resp.status_code == 404


class TestCreateProduct:
    _VALID_BODY = {
        "name": "New Product",
        "jira_project_key": "NEW",
        "jira_base_url": "https://new.atlassian.net",
        "github_org": "neworg",
        "github_repo": "new-repo",
    }

    def test_401_without_auth(self, client_no_auth):
        resp = client_no_auth.post("/api/products", json=self._VALID_BODY)
        assert resp.status_code == 401

    def test_201_with_auth(self, client_auth):
        resp = client_auth.post("/api/products", json=self._VALID_BODY)
        assert resp.status_code == 201
        data = resp.json()
        assert "name" in data
        assert "jira_base_url" in data
        assert "github_org" in data


class TestUpdateProduct:
    def test_401_without_auth(self, client_no_auth):
        resp = client_no_auth.put(f"/api/products/{PRODUCT_ID}", json={"name": "Updated"})
        assert resp.status_code == 401

    def test_200_with_auth(self, client_auth):
        resp = client_auth.put(f"/api/products/{PRODUCT_ID}", json={"name": "Updated"})
        assert resp.status_code == 200

    def test_404_for_missing_product(self):
        app = FastAPI()
        app.include_router(products_router)
        app.dependency_overrides[get_db] = _db_override(_make_mock_db(product=None))
        app.dependency_overrides[_require_auth] = _auth_override
        client = TestClient(app)
        resp = client.put("/api/products/nonexistent", json={"name": "X"})
        assert resp.status_code == 404


class TestDeleteProduct:
    def test_401_without_auth(self, client_no_auth):
        resp = client_no_auth.delete(f"/api/products/{PRODUCT_ID}")
        assert resp.status_code == 401

    def test_204_with_auth(self, client_auth):
        resp = client_auth.delete(f"/api/products/{PRODUCT_ID}")
        assert resp.status_code == 204