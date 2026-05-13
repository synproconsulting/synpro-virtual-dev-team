"""Products router - CRUD for multi-product configuration (SDT1-95, SDT1-118).

Provides endpoints to create, read, update, and delete product records.
Each product stores Jira, GitHub, Railway, and Resend configuration that
the Control Centre and proxies use when a product is selected.

Secret credentials (Jira API token, GitHub token, Anthropic API key,
Resend API key) are accepted as plaintext on POST/PUT and stored
encrypted via Fernet (SDT1-118). The standard list and detail responses
strip ``*_enc`` columns; a dedicated ``GET /api/products/{id}/credentials``
endpoint returns the decrypted secrets to authenticated callers.

Environment variables serve as the default (single-product) fallback.
"""

import logging
import os
import uuid
from typing import Optional

import jwt as _jwt
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import get_db, run_migrations_for_url
from encryption import decrypt_secret, encrypt_secret
from models import Product

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/products", tags=["products"])

_JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
_JWT_ALGORITHM = "HS256"


# ?? Auth ??????????????????????????????????????????????????????????????????????


def _require_auth(authorization: Optional[str] = Header(None)) -> dict:
    """Validate JWT token. Cryptographic check only - no DB lookup."""
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


# ?? Schemas ???????????????????????????????????????????????????????????????????


class ProductCreate(BaseModel):
    """Create payload - plaintext secrets are encrypted before storage."""

    name: str
    jira_project_key: str
    jira_base_url: Optional[str] = None
    jira_email: Optional[str] = None
    jira_api_token: Optional[str] = None
    github_org: Optional[str] = None
    github_repo: str
    github_token: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    resend_api_key: Optional[str] = None
    resend_from_email: Optional[str] = None
    railway_project_id: Optional[str] = None
    railway_dev_service_id: Optional[str] = None
    railway_test_service_id: Optional[str] = None
    railway_prod_service_id: Optional[str] = None
    dev_backend_service_id: Optional[str] = None
    dev_frontend_service_id: Optional[str] = None
    test_backend_service_id: Optional[str] = None
    test_frontend_service_id: Optional[str] = None
    prod_backend_service_id: Optional[str] = None
    prod_frontend_service_id: Optional[str] = None
    db_url_dev: Optional[str] = None
    db_url_test: Optional[str] = None
    db_url_prod: Optional[str] = None


class ProductUpdate(BaseModel):
    """Update payload - every field is optional; plaintext secrets are encrypted."""

    name: Optional[str] = None
    jira_project_key: Optional[str] = None
    jira_base_url: Optional[str] = None
    jira_email: Optional[str] = None
    jira_api_token: Optional[str] = None
    github_org: Optional[str] = None
    github_repo: Optional[str] = None
    github_token: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    resend_api_key: Optional[str] = None
    resend_from_email: Optional[str] = None
    railway_project_id: Optional[str] = None
    railway_dev_service_id: Optional[str] = None
    railway_test_service_id: Optional[str] = None
    railway_prod_service_id: Optional[str] = None
    dev_backend_service_id: Optional[str] = None
    dev_frontend_service_id: Optional[str] = None
    test_backend_service_id: Optional[str] = None
    test_frontend_service_id: Optional[str] = None
    prod_backend_service_id: Optional[str] = None
    prod_frontend_service_id: Optional[str] = None
    db_url_dev: Optional[str] = None
    db_url_test: Optional[str] = None
    db_url_prod: Optional[str] = None


class ProductResponse(BaseModel):
    """Public product representation - never includes ``*_enc`` columns."""

    id: str
    name: str
    jira_project_key: str
    jira_base_url: Optional[str] = None
    jira_email: Optional[str] = None
    github_org: Optional[str] = None
    github_repo: str
    resend_from_email: Optional[str] = None
    railway_project_id: Optional[str] = None
    railway_dev_service_id: Optional[str] = None
    railway_test_service_id: Optional[str] = None
    railway_prod_service_id: Optional[str] = None
    dev_backend_service_id: Optional[str] = None
    dev_frontend_service_id: Optional[str] = None
    test_backend_service_id: Optional[str] = None
    test_frontend_service_id: Optional[str] = None
    prod_backend_service_id: Optional[str] = None
    prod_frontend_service_id: Optional[str] = None
    db_url_dev: Optional[str] = None
    db_url_test: Optional[str] = None
    db_url_prod: Optional[str] = None


class ProductCredentialsResponse(ProductResponse):
    """Authenticated credentials view - includes decrypted secrets."""

    jira_api_token: Optional[str] = None
    github_token: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    resend_api_key: Optional[str] = None


# Plaintext input field name ? encrypted column name
_SECRET_FIELDS = {
    "jira_api_token": "jira_api_token_enc",
    "github_token": "github_token_enc",
    "anthropic_api_key": "anthropic_api_key_enc",
    "resend_api_key": "resend_api_key_enc",
}

# Non-secret fields copied verbatim from request payload to the Product row.
_PLAIN_FIELDS = (
    "name",
    "jira_project_key",
    "jira_base_url",
    "jira_email",
    "github_org",
    "github_repo",
    "resend_from_email",
    "railway_project_id",
    "railway_dev_service_id",
    "railway_test_service_id",
    "railway_prod_service_id",
    "dev_backend_service_id",
    "dev_frontend_service_id",
    "test_backend_service_id",
    "test_frontend_service_id",
    "prod_backend_service_id",
    "prod_frontend_service_id",
    "db_url_dev",
    "db_url_test",
    "db_url_prod",
)


def _to_public_dict(product: Product) -> dict:
    """Serialise a Product row without any ``*_enc`` columns."""
    return {
        "id": str(product.id),
        "name": product.name,
        "jira_project_key": product.jira_project_key,
        "jira_base_url": product.jira_base_url,
        "jira_email": product.jira_email,
        "github_org": product.github_org,
        "github_repo": product.github_repo,
        "resend_from_email": product.resend_from_email,
        "railway_project_id": product.railway_project_id,
        "railway_dev_service_id": product.railway_dev_service_id,
        "railway_test_service_id": product.railway_test_service_id,
        "railway_prod_service_id": product.railway_prod_service_id,
        "dev_backend_service_id": product.dev_backend_service_id,
        "dev_frontend_service_id": product.dev_frontend_service_id,
        "test_backend_service_id": product.test_backend_service_id,
        "test_frontend_service_id": product.test_frontend_service_id,
        "prod_backend_service_id": product.prod_backend_service_id,
        "prod_frontend_service_id": product.prod_frontend_service_id,
        "db_url_dev": product.db_url_dev,
        "db_url_test": product.db_url_test,
        "db_url_prod": product.db_url_prod,
    }


def _decrypt_or_none(ciphertext: Optional[str]) -> Optional[str]:
    """Decrypt a stored ciphertext, returning ``None`` for null columns."""
    if ciphertext is None:
        return None
    return decrypt_secret(ciphertext)


def _apply_payload(product: Product, payload: dict) -> None:
    """Copy plain fields verbatim and encrypt secret fields onto ``product``.

    Only keys present in ``payload`` are applied - ``None`` values are
    treated as "unset" and skipped, matching the previous update semantics.
    """
    for field in _PLAIN_FIELDS:
        if payload.get(field) is not None:
            setattr(product, field, payload[field])
    for plain_field, enc_column in _SECRET_FIELDS.items():
        plaintext = payload.get(plain_field)
        if plaintext is not None:
            setattr(product, enc_column, encrypt_secret(plaintext))


# ?? Routes ????????????????????????????????????????????????????????????????????


@router.get("")
def list_products(db: Session = Depends(get_db)):
    """List all products. Public endpoint for Control Centre product selector."""
    products = db.query(Product).order_by(Product.name).all()
    return {"products": [_to_public_dict(p) for p in products]}


@router.get("/{product_id}")
def get_product(product_id: str, db: Session = Depends(get_db)):
    """Get a single product by ID. Secrets are not returned by this endpoint."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return _to_public_dict(product)


@router.get("/{product_id}/credentials")
def get_product_credentials(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(_require_auth),
) -> dict:
    """Return a product including decrypted secret credentials.

    Authenticated callers receive every column on the row, with each
    ``*_enc`` column decrypted into its plaintext form. Null columns
    are returned as ``None``.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    response = _to_public_dict(product)
    response.update(
        {
            "jira_api_token": _decrypt_or_none(product.jira_api_token_enc),
            "github_token": _decrypt_or_none(product.github_token_enc),
            "anthropic_api_key": _decrypt_or_none(product.anthropic_api_key_enc),
            "resend_api_key": _decrypt_or_none(product.resend_api_key_enc),
        }
    )
    return response


@router.post("", status_code=status.HTTP_201_CREATED)
def create_product(
    body: ProductCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(_require_auth),
):
    """Create a new product. Plaintext secrets are encrypted before storage."""
    payload = body.model_dump()
    product = Product(id=uuid.uuid4())
    # ``name``, ``jira_project_key`` and ``github_repo`` are required on the
    # schema, so they will always be present in ``payload`` here.
    product.name = payload["name"]
    product.jira_project_key = payload["jira_project_key"]
    product.github_repo = payload["github_repo"]
    _apply_payload(product, payload)
    db.add(product)
    try:
        db.commit()
        db.refresh(product)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Product name already exists")
    logger.info("Product created: %s", product.name)
    return _to_public_dict(product)


@router.put("/{product_id}")
def update_product(
    product_id: str,
    body: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(_require_auth),
):
    """Update a product. Plaintext secret inputs are encrypted before storage."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    _apply_payload(product, body.model_dump())
    db.commit()
    db.refresh(product)
    logger.info("Product updated: %s", product_id)
    return _to_public_dict(product)


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


@router.post("/{product_id}/migrate")
def migrate_product_database(
    product_id: str,
    environment: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(_require_auth),
) -> dict:
    """Run Alembic migrations for a product's per-environment database.

    Initialises or upgrades the isolated database for the given product and
    environment. The db_url_dev / db_url_test / db_url_prod field must already
    be set on the product record before calling this endpoint.

    Args:
        product_id: UUID of the product.
        environment: Target environment - 'dev', 'test', or 'prod'.
    """
    if environment not in ("dev", "test", "prod"):
        raise HTTPException(status_code=400, detail="environment must be 'dev', 'test', or 'prod'")

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    url_map = {
        "dev": product.db_url_dev,
        "test": product.db_url_test,
        "prod": product.db_url_prod,
    }
    db_url = url_map[environment]

    if not db_url:
        raise HTTPException(
            status_code=422,
            detail=f"No database URL configured for environment '{environment}'",
        )

    try:
        run_migrations_for_url(db_url)
    except Exception as exc:
        logger.error("Migration failed product=%s env=%s: %s", product_id, environment, exc)
        raise HTTPException(status_code=500, detail=f"Migration failed: {exc}")

    logger.info("Migrations applied: product=%s environment=%s", product_id, environment)
    return {"message": f"Migrations applied successfully for environment '{environment}'"}
