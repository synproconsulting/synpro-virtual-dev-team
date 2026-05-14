"""Jira proxy router - extracted from main.py (SDT1-47 refactor).

Proxies Jira API calls from the browser to avoid CORS restrictions.
Supports per-product Jira configuration via the product_id query parameter
(SDT1-95). When product_id is supplied, the product's jira_base_url and
jira_project_key are used; otherwise falls back to environment variables.
"""

import os
import re
import base64
import logging
from typing import Optional

import httpx
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import APIRouter, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# -- Config --------------------------------------------------------------------

JIRA_BASE_URL  = os.getenv("JIRA_BASE_URL", "")
JIRA_EMAIL     = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_PROJECT   = os.getenv("JIRA_PROJECT_KEY", "SDT1")
DATABASE_URL   = os.getenv("DATABASE_URL", "")


def jira_auth():
    creds   = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
    encoded = base64.b64encode(creds.encode()).decode()
    return {"Authorization": f"Basic {encoded}",
            "Accept": "application/json",
            "Content-Type": "application/json"}


def _get_product_jira_cfg(
    product_id: Optional[str],
    jira_project_key: Optional[str] = None,
) -> tuple:
    """Return ``(jira_base_url, jira_project_key)`` for a Jira call.

    Resolution priority for the project key:
      1. ``jira_project_key`` query-string override (when supplied)
      2. ``products`` row matching ``product_id``
      3. ``JIRA_PROJECT_KEY`` environment variable

    Resolution priority for the base URL:
      1. ``products`` row matching ``product_id``
      2. ``JIRA_BASE_URL`` environment variable

    Each field is resolved independently — a product row that only sets
    ``jira_project_key`` no longer forces a fallback to the env var for
    that same field (the previous "both or neither" check is the SDT1-121
    bug being fixed here). The explicit ``jira_project_key`` override
    lets the frontend pass the value it already has from
    ``productCredentials`` and bypass the DB lookup entirely.
    """
    base_url = JIRA_BASE_URL
    project  = JIRA_PROJECT
    if product_id and DATABASE_URL:
        try:
            conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
            cur  = conn.cursor()
            cur.execute(
                "SELECT jira_base_url, jira_project_key FROM products WHERE id = %s",
                (product_id,)
            )
            row = cur.fetchone()
            conn.close()
            if row:
                if row.get("jira_base_url"):
                    base_url = row["jira_base_url"]
                if row.get("jira_project_key"):
                    project = row["jira_project_key"]
        except Exception as exc:
            logger.warning("Product Jira config lookup failed for %s: %s", product_id, exc)
    if jira_project_key:
        project = jira_project_key
    return base_url, project


# Legacy default board ID for the SynPro VSDC / SDT1 deployment. Used only
# when no product is selected (single-product fallback). Per-product board
# IDs come from products.jira_board_id when that column exists.
_DEFAULT_JIRA_BOARD_ID = 34


def _get_product_jira_board_id(product_id: Optional[str]) -> Optional[int]:
    """Return the Jira board ID for a product, or ``None`` if not configured.

    Resolution:
      * ``product_id is None`` -> legacy default board (SynPro VSDC).
      * ``product_id`` set and the ``products`` row carries a non-null
        ``jira_board_id`` -> that value.
      * Anything else (no DATABASE_URL, row missing, column missing, value
        null) -> ``None``.

    Returning ``None`` for "not configured" lets callers skip the native
    sprints fetch entirely rather than silently falling back to another
    product's board. The ``jira_board_id`` column may not yet exist on the
    ``products`` table; the lookup catches that case and treats it as
    "not configured" without crashing the endpoint.
    """
    if product_id is None:
        return _DEFAULT_JIRA_BOARD_ID
    if not DATABASE_URL:
        return None
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur  = conn.cursor()
        cur.execute(
            "SELECT jira_board_id FROM products WHERE id = %s",
            (product_id,)
        )
        row = cur.fetchone()
        if row and row.get("jira_board_id") is not None:
            return int(row["jira_board_id"])
    except Exception as exc:
        logger.debug("Product board lookup skipped for %s: %s", product_id, exc)
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
    return None


# -- Router --------------------------------------------------------------------

router = APIRouter(prefix="/proxy/jira", tags=["proxy"])


@router.get("/issues")
async def proxy_jira_issues(
    status: str = Query(None, description="Filter by status e.g. 'To Do', 'Done'"),
    max_results: int = Query(100),
    product_id: Optional[str] = Query(None, description="Product ID for per-product Jira config"),
    jira_project_key: Optional[str] = Query(None, description="Override Jira project key directly (bypasses product lookup)"),
):
    """Proxy Jira issues to avoid CORS issues in the browser."""
    base_url, project = _get_product_jira_cfg(product_id, jira_project_key)
    if not base_url:
        return {"issues": [], "error": "JIRA_BASE_URL not configured"}

    jql = f"project = {project} ORDER BY updated DESC"
    if status:
        jql = f'project = {project} AND status = "{status}" ORDER BY updated DESC'

    fields = "summary,status,priority,issuetype,assignee,customfield_10016,customfield_10071"
    url    = f"{base_url}/rest/api/3/search/jql"

    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(
                url, headers=jira_auth(),
                params={"jql": jql, "maxResults": max_results, "fields": fields},
                timeout=15.0
            )
            if r.status_code == 200:
                data   = r.json()
                issues = [
                    {
                        "key":      i["key"],
                        "summary":  i["fields"]["summary"],
                        "status":   i["fields"].get("status", {}).get("name", "Unknown"),
                        "priority": i["fields"].get("priority", {}).get("name", "Medium"),
                        "type":     i["fields"].get("issuetype", {}).get("name", "Story"),
                        "points":   i["fields"].get("customfield_10016") or 0,
                        "order":    i["fields"].get("customfield_10071") or 999,
                    }
                    for i in data.get("issues", [])
                ]
                return {"issues": issues, "total": data.get("total", 0)}
            return {"issues": [], "error": f"Jira returned {r.status_code}"}
        except Exception as e:
            return {"issues": [], "error": str(e)}


@router.get("/issue/{issue_key}/transitions")
async def proxy_jira_transitions(
    issue_key: str,
    product_id: Optional[str] = Query(None),
):
    """Get available transitions for a Jira issue."""
    base_url, _ = _get_product_jira_cfg(product_id)
    if not base_url:
        return {"transitions": []}
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{base_url}/rest/api/3/issue/{issue_key}/transitions",
            headers=jira_auth(), timeout=10.0
        )
        return r.json() if r.status_code == 200 else {"transitions": []}


@router.post("/issue/{issue_key}/transition")
async def proxy_jira_transition(
    issue_key: str,
    body: dict,
    product_id: Optional[str] = Query(None),
):
    """Transition a Jira issue to a new status."""
    base_url, _ = _get_product_jira_cfg(product_id)
    if not base_url:
        return {"success": False, "error": "JIRA not configured"}
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{base_url}/rest/api/3/issue/{issue_key}/transitions",
            headers=jira_auth(), json=body, timeout=10.0
        )
        return {"success": r.status_code in (200, 204)}


@router.get("/sprints")
async def proxy_jira_sprints(
    product_id: Optional[str] = Query(None),
    jira_project_key: Optional[str] = Query(None, description="Override Jira project key directly (bypasses product lookup)"),
):
    """Get all sprints - combines fix versions and native sprints.

    Each sprint object includes state (active/closed/future), startDate, and
    endDate sourced from the Jira Agile API so the Control Centre can display
    sprint health without a separate API call (SDT1-74).
    """
    base_url, project = _get_product_jira_cfg(product_id, jira_project_key)
    if not base_url:
        return {"sprints": [], "error": "JIRA_BASE_URL not configured"}
    # Only fetch native sprints from a board the selected product actually
    # owns. When a product has no board configured we deliberately leave
    # board_id as None — never silently fall back to the SDT1 board, which
    # was the source of the cross-product sprint bleed (SDT1-121 follow-up).
    board_id = _get_product_jira_board_id(product_id)

    async with httpx.AsyncClient() as client:
        try:
            versions_r = await client.get(
                f"{base_url}/rest/api/3/project/{project}/versions",
                headers=jira_auth(), timeout=10.0
            )
            sprints_r = None
            if board_id is not None:
                sprints_r = await client.get(
                    f"{base_url}/rest/agile/1.0/board/{board_id}/sprint",
                    headers=jira_auth(), timeout=10.0,
                    params={"maxResults": 50}
                )

            sprints    = []
            seen_names = set()

            # Build a map from sprint number -> native sprint metadata
            native_sprint_map = {}
            if sprints_r is not None and sprints_r.status_code == 200:
                for s in sprints_r.json().get("values", []):
                    m = re.search(r'sprint\s+(\d+)', s.get("name", ""), re.IGNORECASE)
                    if m:
                        native_sprint_map[int(m.group(1))] = {
                            "id":        str(s["id"]),
                            "state":     s.get("state", "future"),
                            "startDate": s.get("startDate"),
                            "endDate":   s.get("endDate"),
                        }

            if versions_r.status_code == 200:
                for idx, v in enumerate(versions_r.json(), start=1):
                    if not v.get("archived", False):
                        vname      = v["name"]
                        m          = re.search(r'sprint\s+(\d+)', vname, re.IGNORECASE)
                        sprint_num = int(m.group(1)) if m else idx
                        native     = native_sprint_map.get(sprint_num, {})
                        native_id  = native.get("id")
                        # Prefer native sprint state; derive from version flags as fallback
                        if native.get("state"):
                            state = native["state"]
                        elif v.get("released", False):
                            state = "closed"
                        else:
                            state = "future"
                        sprints.append({
                            "id":        v["id"],
                            "nativeId":  native_id,
                            "name":      vname,
                            "released":  v.get("released", False),
                            "type":      "version",
                            "state":     state,
                            "startDate": native.get("startDate"),
                            "endDate":   native.get("endDate"),
                        })
                        seen_names.add(vname.lower())

            # Native-sprint-only fallback: ONLY when the selected product
            # has its own board configured. Without this gate the endpoint
            # would return another product's sprints whenever the active
            # product happens to have no fix versions yet.
            if board_id is not None and sprints_r is not None and \
               sprints_r.status_code == 200 and not sprints:
                for s in sprints_r.json().get("values", []):
                    name = s.get("name", "")
                    if s.get("state") != "future":
                        sprints.append({
                            "id":        str(s["id"]),
                            "nativeId":  str(s["id"]),
                            "name":      name,
                            "released":  s.get("state") == "closed",
                            "type":      "sprint",
                            "state":     s.get("state", "future"),
                            "startDate": s.get("startDate"),
                            "endDate":   s.get("endDate"),
                        })

            return {"sprints": sorted(sprints, key=lambda x: str(x["id"]))}
        except Exception as e:
            return {"sprints": [], "error": str(e)}


@router.get("/sprint/{version_id}/issues")
async def proxy_sprint_issues(
    version_id: str,
    product_id: Optional[str] = Query(None),
    jira_project_key: Optional[str] = Query(None, description="Override Jira project key directly (bypasses product lookup)"),
):
    """Get issues for a specific sprint (version or native sprint ID)."""
    base_url, project = _get_product_jira_cfg(product_id, jira_project_key)
    if not base_url:
        return {"issues": [], "error": "JIRA_BASE_URL not configured"}

    parts     = version_id.split("|")
    fix_id    = parts[0]
    native_id = parts[1] if len(parts) > 1 else fix_id
    jql = (
        f"project = {project} AND ("
        f"fixVersion = {fix_id} OR sprint = {native_id}"
        f") ORDER BY priority DESC"
    )
    fields = "summary,status,priority,issuetype,assignee,customfield_10016,customfield_10071,fixVersions,customfield_10020"

    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(
                f"{base_url}/rest/api/3/search/jql",
                headers=jira_auth(),
                params={"jql": jql, "maxResults": 100, "fields": fields},
                timeout=15.0
            )
            if r.status_code == 200:
                data   = r.json()
                issues = [
                    {
                        "key":      i["key"],
                        "summary":  i["fields"]["summary"],
                        "status":   i["fields"].get("status", {}).get("name", "Unknown"),
                        "priority": i["fields"].get("priority", {}).get("name", "Medium"),
                        "type":     i["fields"].get("issuetype", {}).get("name", "Story"),
                        "points":   i["fields"].get("customfield_10016") or 0,
                        "order":    i["fields"].get("customfield_10071") or 999,
                        "assignee": (i["fields"].get("assignee") or {}).get("displayName"),
                    }
                    for i in data.get("issues", [])
                    if i["fields"].get("issuetype", {}).get("name") not in ("Epic", "Sub-task", "Subtask")
                ]
                seen, unique = set(), []
                for i in issues:
                    if i["key"] not in seen:
                        seen.add(i["key"])
                        unique.append(i)
                return {"issues": unique, "total": len(unique)}
            return {"issues": [], "error": f"Jira returned {r.status_code}"}
        except Exception as e:
            return {"issues": [], "error": str(e)}


class CompleteSprintRequest(BaseModel):
    moveIncompleteTo: str = "backlog"
    nextSprintId: Optional[str] = None


@router.post("/sprint/{sprint_id}/complete")
async def proxy_complete_sprint(
    sprint_id: str,
    body: CompleteSprintRequest,
    product_id: Optional[str] = Query(None),
    jira_project_key: Optional[str] = Query(None, description="Override Jira project key directly (bypasses product lookup)"),
):
    """Complete (close) a Jira sprint and optionally move incomplete issues.

    sprint_id must be the native Jira sprint ID (not the fix-version ID).
    moveIncompleteTo: "backlog" (default) | "nextSprint"
    nextSprintId: required when moveIncompleteTo == "nextSprint"
    """
    base_url, project = _get_product_jira_cfg(product_id, jira_project_key)
    if not base_url:
        return {"success": False, "error": "JIRA not configured"}

    async with httpx.AsyncClient() as client:
        jql = f"project = {project} AND sprint = {sprint_id} AND status != Done"
        r   = await client.get(
            f"{base_url}/rest/api/3/search/jql",
            headers=jira_auth(),
            params={"jql": jql, "maxResults": 100, "fields": "summary,status"},
            timeout=15.0
        )
        incomplete_keys = []
        if r.status_code == 200:
            incomplete_keys = [i["key"] for i in r.json().get("issues", [])]

        if incomplete_keys:
            if body.moveIncompleteTo == "backlog":
                await client.post(
                    f"{base_url}/rest/agile/1.0/backlog/issue",
                    headers=jira_auth(),
                    json={"issues": incomplete_keys},
                    timeout=10.0
                )
            elif body.moveIncompleteTo == "nextSprint" and body.nextSprintId:
                await client.post(
                    f"{base_url}/rest/agile/1.0/sprint/{body.nextSprintId}/issue",
                    headers=jira_auth(),
                    json={"issues": incomplete_keys},
                    timeout=10.0
                )

        # POST is the partial-update endpoint — only the supplied fields are changed.
        # PUT requires ALL sprint fields (name, startDate, endDate, state) and returns
        # 400 "Sprint name is required" when only state is sent.
        close_r = await client.post(
            f"{base_url}/rest/agile/1.0/sprint/{sprint_id}",
            headers=jira_auth(),
            json={"state": "closed"},
            timeout=10.0
        )
        success = close_r.status_code in (200, 204)
        result: dict = {
            "success":         success,
            "statusCode":      close_r.status_code,
            "incompleteMoved": len(incomplete_keys),
        }
        if not success:
            try:
                err_body = close_r.json()
                errors = err_body.get("errors", {})
                msgs   = err_body.get("errorMessages", [])
                if errors:
                    result["error"] = "; ".join(f"{k}: {v}" for k, v in errors.items())
                elif msgs:
                    result["error"] = "; ".join(msgs)
                else:
                    result["error"] = f"Jira returned {close_r.status_code}"
            except Exception:
                result["error"] = f"Jira returned {close_r.status_code}"
        return result