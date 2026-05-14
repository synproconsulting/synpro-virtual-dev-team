#!/usr/bin/env python3
"""Seed the SynPro VSDC product into the UAT backend (SDT1-120).

Idempotent: checks for an existing product named "SynPro VSDC" via
GET /api/products. If found, prints a skip message and exits 0.
Otherwise, logs in via POST /auth/login with SEED_EMAIL / SEED_PASSWORD,
then creates the product via POST /api/products with a Bearer token.

All credentials are read from environment variables - no hardcoded
values. The product name, GitHub org and GitHub repo are fixed for
this specific product (SynPro VSDC).

Usage:
    python seed_product.py

Required environment variables:
    API_BASE_URL                 Base URL of the UAT backend, e.g.
                                 https://synpro-virtual-dev-team-production.up.railway.app
    SEED_EMAIL                   Registered UAT user e-mail
    SEED_PASSWORD                Registered UAT user password
    JIRA_BASE_URL                -> jira_base_url
    JIRA_PROJECT_KEY             -> jira_project_key
    JIRA_EMAIL                   -> jira_email
    JIRA_API_TOKEN               -> jira_api_token
    GITHUB_TOKEN                 -> github_token
    ANTHROPIC_API_KEY            -> anthropic_api_key
    RESEND_API_KEY               -> resend_api_key
    SMTP_FROM_EMAIL              -> resend_from_email
    RAILWAY_PROJECT_ID           -> railway_project_id
    RAILWAY_BACKEND_SERVICE_ID   -> dev_backend_service_id
    RAILWAY_FRONTEND_SERVICE_ID  -> dev_frontend_service_id

Exit codes:
    0 - success or product already exists
    1 - missing env vars, HTTP error, or unexpected response
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Dict, Optional, Tuple

PRODUCT_NAME = "SynPro VSDC"
GITHUB_ORG = "synproconsulting"
GITHUB_REPO = "synpro-virtual-dev-team"

# Env-var name -> Product field name. Insertion order is preserved so
# the missing-vars error message lists variables in a stable, useful order.
ENV_TO_FIELD: Dict[str, str] = {
    "JIRA_BASE_URL": "jira_base_url",
    "JIRA_PROJECT_KEY": "jira_project_key",
    "JIRA_EMAIL": "jira_email",
    "JIRA_API_TOKEN": "jira_api_token",
    "GITHUB_TOKEN": "github_token",
    "ANTHROPIC_API_KEY": "anthropic_api_key",
    "RESEND_API_KEY": "resend_api_key",
    "SMTP_FROM_EMAIL": "resend_from_email",
    "RAILWAY_PROJECT_ID": "railway_project_id",
    "RAILWAY_BACKEND_SERVICE_ID": "dev_backend_service_id",
    "RAILWAY_FRONTEND_SERVICE_ID": "dev_frontend_service_id",
}

AUTH_VARS = ("SEED_EMAIL", "SEED_PASSWORD")
INFRA_VARS = ("API_BASE_URL",)


def read_required_env() -> Tuple[str, Dict[str, str]]:
    """Validate that every required environment variable is set.

    Returns:
        Tuple of ``(api_base_url, values)``. ``api_base_url`` is the
        backend base URL with any trailing slash stripped; ``values`` is
        a dict mapping every required env-var name to its trimmed value.

    Exits with status 1 if any variable is missing or empty, printing
    the full list of missing names to stderr.
    """
    missing = []
    values: Dict[str, str] = {}

    for name in INFRA_VARS + AUTH_VARS + tuple(ENV_TO_FIELD.keys()):
        raw = os.environ.get(name, "")
        trimmed = raw.strip()
        if not trimmed:
            missing.append(name)
        else:
            values[name] = trimmed

    if missing:
        print("Error: missing required environment variable(s):", file=sys.stderr)
        for name in missing:
            print(f"  - {name}", file=sys.stderr)
        sys.exit(1)

    api_base_url = values.pop("API_BASE_URL").rstrip("/")
    return api_base_url, values


def http_request(
    method: str,
    url: str,
    *,
    payload: Optional[dict] = None,
    headers: Optional[dict] = None,
) -> Tuple[int, dict]:
    """Send a JSON HTTP request via urllib and return ``(status, body)``.

    ``body`` is the decoded JSON object when the response is JSON, or
    ``{"_raw": <text>}`` when the response is not JSON-decodable.
    HTTP error responses are not raised - the status code and parsed
    body are returned the same way as success responses, so callers
    can produce specific error messages without try/except gymnastics.
    """
    body_bytes: Optional[bytes] = None
    req_headers = {"Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    if payload is not None:
        body_bytes = json.dumps(payload).encode("utf-8")
        req_headers["Content-Type"] = "application/json"

    req = urllib.request.Request(
        url=url, data=body_bytes, headers=req_headers, method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8") or "{}"
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, {"_raw": raw}
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8", errors="replace") if err.fp else ""
        try:
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            data = {"_raw": raw}
        return err.code, data


def find_existing(api_base_url: str) -> bool:
    """Return True when a product named ``PRODUCT_NAME`` already exists."""
    status, data = http_request("GET", f"{api_base_url}/api/products")
    if status != 200:
        print(
            f"Error: GET /api/products returned HTTP {status}: {data}",
            file=sys.stderr,
        )
        sys.exit(1)
    products = data.get("products") if isinstance(data, dict) else None
    if not isinstance(products, list):
        print(
            "Error: GET /api/products returned an unexpected payload: "
            f"{data}",
            file=sys.stderr,
        )
        sys.exit(1)
    return any(
        isinstance(p, dict) and p.get("name") == PRODUCT_NAME for p in products
    )


def login(api_base_url: str, email: str, password: str) -> str:
    """Authenticate and return a Bearer access token.

    Exits with status 1 on authentication failure so the caller does not
    proceed to a POST that would just return 401.
    """
    status, data = http_request(
        "POST",
        f"{api_base_url}/auth/login",
        payload={"email": email, "password": password},
    )
    if status != 200:
        print(
            f"Error: POST /auth/login returned HTTP {status}: {data}",
            file=sys.stderr,
        )
        sys.exit(1)
    token = data.get("access_token") if isinstance(data, dict) else None
    if not token:
        print(
            "Error: POST /auth/login succeeded but no access_token was "
            f"returned: {data}",
            file=sys.stderr,
        )
        sys.exit(1)
    return token


def build_payload(values: Dict[str, str]) -> dict:
    """Build the POST /api/products body from validated env values.

    TEST and PROD service IDs are intentionally omitted - per the
    SDT1-118 schema they are optional, and the backend treats an absent
    field as "leave unset" rather than overwriting with empty.
    """
    payload: dict = {
        "name": PRODUCT_NAME,
        "github_org": GITHUB_ORG,
        "github_repo": GITHUB_REPO,
    }
    for env_name, field_name in ENV_TO_FIELD.items():
        payload[field_name] = values[env_name]
    return payload


def create_product(api_base_url: str, token: str, payload: dict) -> dict:
    """POST the payload, returning the created Product representation."""
    status, data = http_request(
        "POST",
        f"{api_base_url}/api/products",
        payload=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    if status != 201:
        print(
            f"Error: POST /api/products returned HTTP {status}: {data}",
            file=sys.stderr,
        )
        sys.exit(1)
    return data if isinstance(data, dict) else {}


def main() -> int:
    api_base_url, values = read_required_env()
    print(f"Target backend: {api_base_url}")

    print(f"Checking whether product '{PRODUCT_NAME}' already exists...")
    if find_existing(api_base_url):
        print("Product already exists, skipping")
        return 0

    print(
        f"Product '{PRODUCT_NAME}' not found - "
        "logging in to create it."
    )
    token = login(api_base_url, values["SEED_EMAIL"], values["SEED_PASSWORD"])

    payload = build_payload(values)
    print(
        "Creating product (fields: "
        f"{', '.join(sorted(payload.keys()))})..."
    )
    created = create_product(api_base_url, token, payload)
    product_id = created.get("id", "<unknown>")
    print(f"Success: created product '{PRODUCT_NAME}' (id={product_id})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
