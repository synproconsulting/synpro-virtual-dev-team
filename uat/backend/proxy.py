"""Jira proxy router - extracted from main.py (SDT1-47 refactor).

Proxies Jira API calls from the browser to avoid CORS restrictions.
"""

import os
import re
import base64

import httpx
from fastapi import APIRouter, Query

# -- Config --------------------------------------------------------------------

JIRA_BASE_URL  = os.getenv("JIRA_BASE_URL", "")
JIRA_EMAIL     = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_PROJECT   = os.getenv("JIRA_PROJECT_KEY", "SDT1")


def jira_auth():
    creds   = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
    encoded = base64.b64encode(creds.encode()).decode()
    return {"Authorization": f"Basic {encoded}",
            "Accept": "application/json",
            "Content-Type": "application/json"}


# -- Router --------------------------------------------------------------------

router = APIRouter(prefix="/proxy/jira", tags=["proxy"])


@router.get("/issues")
async def proxy_jira_issues(
    status: str = Query(None, description="Filter by status e.g. 'To Do', 'Done'"),
    max_results: int = Query(100)
):
    """Proxy Jira issues to avoid CORS issues in the browser."""
    if not JIRA_BASE_URL:
        return {"issues": [], "error": "JIRA_BASE_URL not configured"}

    jql = f"project = {JIRA_PROJECT} ORDER BY updated DESC"
    if status:
        jql = f'project = {JIRA_PROJECT} AND status = "{status}" ORDER BY updated DESC'

    fields = "summary,status,priority,issuetype,assignee,customfield_10016,customfield_10071"
    url    = f"{JIRA_BASE_URL}/rest/api/3/search/jql"

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
async def proxy_jira_transitions(issue_key: str):
    """Get available transitions for a Jira issue."""
    if not JIRA_BASE_URL:
        return {"transitions": []}
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/transitions",
            headers=jira_auth(), timeout=10.0
        )
        return r.json() if r.status_code == 200 else {"transitions": []}


@router.post("/issue/{issue_key}/transition")
async def proxy_jira_transition(issue_key: str, body: dict):
    """Transition a Jira issue to a new status."""
    if not JIRA_BASE_URL:
        return {"success": False, "error": "JIRA not configured"}
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/transitions",
            headers=jira_auth(), json=body, timeout=10.0
        )
        return {"success": r.status_code in (200, 204)}


@router.get("/sprints")
async def proxy_jira_sprints():
    """Get all sprints - combines fix versions and native sprints.

    Each sprint object includes state (active/closed/future), startDate, and
    endDate sourced from the Jira Agile API so the Control Centre can display
    sprint health without a separate API call (SDT1-74).
    """
    if not JIRA_BASE_URL:
        return {"sprints": [], "error": "JIRA_BASE_URL not configured"}
    async with httpx.AsyncClient() as client:
        try:
            versions_r = await client.get(
                f"{JIRA_BASE_URL}/rest/api/3/project/{JIRA_PROJECT}/versions",
                headers=jira_auth(), timeout=10.0
            )
            sprints_r = await client.get(
                f"{JIRA_BASE_URL}/rest/agile/1.0/board/34/sprint",
                headers=jira_auth(), timeout=10.0,
                params={"maxResults": 50}
            )

            sprints    = []
            seen_names = set()

            # Build a map from sprint number -> native sprint metadata
            native_sprint_map = {}
            if sprints_r.status_code == 200:
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

            if sprints_r.status_code == 200 and not sprints:
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
async def proxy_sprint_issues(version_id: str):
    """Get issues for a specific sprint (version or native sprint ID)."""
    if not JIRA_BASE_URL:
        return {"issues": [], "error": "JIRA_BASE_URL not configured"}

    parts     = version_id.split("|")
    fix_id    = parts[0]
    native_id = parts[1] if len(parts) > 1 else fix_id
    jql = (
        f"project = {JIRA_PROJECT} AND ("
        f"fixVersion = {fix_id} OR sprint = {native_id}"
        f") ORDER BY priority DESC"
    )
    fields = "summary,status,priority,issuetype,assignee,customfield_10016,customfield_10071,fixVersions,customfield_10020"

    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(
                f"{JIRA_BASE_URL}/rest/api/3/search/jql",
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