"""Products router — CRUD for multi-product configuration (SDT1-95).

Provides endpoints to create, read, update, and delete product records.
Each product stores Jira, GitHub, and Railway configuration that the
Control Centre and Jira proxy use when a product is selected.

Environment variables serve as the default (single-product) fallback.
"""

import logging
import os
import uuid
from typing import Optional, Dict

import jwt as _jwt
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import get_db
from models import Product

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/products", tags=["products"])

_JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
_JWT_ALGORITHM = "HS256"


# ── Auth ──────────────────────────────────────────────────────────────────────


def _require_auth(authorization: Optional[str] = Header(None)) -> dict:
    """Validate JWT token. Cryptographic check only — no DB lookup."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    token = authorization[7:]
    try:
        return _jwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGORITHM])
    except _jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except _jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# ── Schemas ───────────────────────────────────────────────────────────────────


class ProductCreate(BaseModel):
    name: str
    jira_project_key: str
    jira_base_url: str
    github_org: str
    github_repo: str
    railway_project_id: Optional[str] = None
    railway_backend_service_name: Optional[str] = None
    railway_frontend_service_name: Optional[str] = None
    railway_dev_service_id: Optional[str] = None
    railway_test_service_id: Optional[str] = None
    railway_prod_service_id: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    jira_project_key: Optional[str] = None
    jira_base_url: Optional[str] = None
    github_org: Optional[str] = None
    github_repo: Optional[str] = None
    railway_project_id: Optional[str] = None
    railway_backend_service_name: Optional[str] = None
    railway_frontend_service_name: Optional[str] = None
    railway_dev_service_id: Optional[str] = None
    railway_test_service_id: Optional[str] = None
    railway_prod_service_id: Optional[str] = None


def _to_dict(product: Product) -> dict:
    return {
        "id": str(product.id),
        "name": product.name,
        "jira_project_key": product.jira_project_key,
        "jira_base_url": product.jira_base_url,
        "github_org": product.github_org,
        "github_repo": product.github_repo,
        "railway_project_id": product.railway_project_id,
        "railway_backend_service_name": product.railway_backend_service_name,
        "railway_frontend_service_name": product.railway_frontend_service_name,
        "railway_dev_service_id": product.railway_dev_service_id,
        "railway_test_service_id": product.railway_test_service_id,
        "railway_prod_service_id": product.railway_prod_service_id,
    }


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get("")
def list_products(db: Session = Depends(get_db)):
    """List all products. Public endpoint for Control Centre product selector."""
    products = db.query(Product).order_by(Product.name).all()
    return {"products": [_to_dict(p) for p in products]}


@router.get("/{product_id}")
def get_product(product_id: str, db: Session = Depends(get_db)):
    """Get a single product by ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return _to_dict(product)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_product(
    body: ProductCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(_require_auth),
):
    """Create a new product. Requires authentication."""
    product = Product(
        id=uuid.uuid4(),
        name=body.name,
        jira_project_key=body.jira_project_key,
        jira_base_url=body.jira_base_url,
        github_org=body.github_org,
        github_repo=body.github_repo,
        railway_project_id=body.railway_project_id,
        railway_backend_service_name=body.railway_backend_service_name,
        railway_frontend_service_name=body.railway_frontend_service_name,
        railway_dev_service_id=body.railway_dev_service_id,
        railway_test_service_id=body.railway_test_service_id,
        railway_prod_service_id=body.railway_prod_service_id,
    )
    db.add(product)
    try:
        db.commit()
        db.refresh(product)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Product name already exists")
    logger.info("Product created: %s", product.name)
    return _to_dict(product)


@router.put("/{product_id}")
def update_product(
    product_id: str,
    body: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(_require_auth),
):
    """Update a product. Requires authentication."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    for field, value in updates.items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    logger.info("Product updated: %s", product_id)
    return _to_dict(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(_require_auth),
):
    """Delete a product. Requires authentication."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    logger.info("Product deleted: %s", product_id)
