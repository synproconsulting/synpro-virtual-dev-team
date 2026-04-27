"""
backend/main.py
───────────────
FastAPI application for the SynPro Virtual Dev Team UAT environment.
Wraps the auth module with a REST API and PostgreSQL persistence.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from contextlib import asynccontextmanager
import os
import uuid
import hashlib
import hmac
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone, timedelta
import jwt

# ── Config ─────────────────────────────────────────────────────────────────────

DATABASE_URL = os.environ.get("DATABASE_URL", "")
JWT_SECRET   = os.environ.get("JWT_SECRET", "dev-secret-change-in-production")
JWT_EXPIRY   = int(os.environ.get("JWT_EXPIRY_HOURS", "24"))
FRONTEND_URL = os.environ.get("FRONTEND_URL", "*")


# ── Database ───────────────────────────────────────────────────────────────────

def get_db():
    """Get a database connection."""
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="Database not configured")
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Create tables if they don't exist."""
    if not DATABASE_URL:
        print("WARNING: DATABASE_URL not set — running without database")
        return
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur  = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email         VARCHAR(255) UNIQUE NOT NULL,
                username      VARCHAR(100) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                is_active     BOOLEAN DEFAULT TRUE
            );

            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id    UUID REFERENCES users(id) ON DELETE CASCADE,
                token      VARCHAR(255) UNIQUE NOT NULL,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                used       BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("✓ Database tables initialized")
    except Exception as e:
        print(f"Database init error: {e}")


# ── App setup ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="SynPro Virtual Dev Team — Auth API",
    description="UAT environment for the authentication module",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    salt = os.urandom(32)
    key  = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return salt.hex() + ":" + key.hex()


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, key_hex = stored.split(":")
        salt = bytes.fromhex(salt_hex)
        key  = bytes.fromhex(key_hex)
        new  = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
        return hmac.compare_digest(key, new)
    except Exception:
        return False


def create_jwt(user_id: str, email: str) -> str:
    payload = {
        "sub":   user_id,
        "email": email,
        "iat":   datetime.now(timezone.utc),
        "exp":   datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def validate_password(password: str) -> list[str]:
    errors = []
    if len(password) < 8:
        errors.append("Minimum 8 characters")
    if not any(c.isupper() for c in password):
        errors.append("At least one uppercase letter")
    if not any(c.islower() for c in password):
        errors.append("At least one lowercase letter")
    if not any(c.isdigit() for c in password):
        errors.append("At least one number")
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("At least one special character")
    return errors


# ── Request/Response models ────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email:    str
    password: str
    username: str = ""


class LoginRequest(BaseModel):
    email:    str
    password: str


class ResetRequestModel(BaseModel):
    email: str


class ResetCompleteModel(BaseModel):
    token:        str
    new_password: str


class UserResponse(BaseModel):
    id:         str
    email:      str
    username:   str
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user:         UserResponse


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0",
            "db": "connected" if DATABASE_URL else "not configured"}


@app.post("/auth/register", response_model=TokenResponse)
def register(req: RegisterRequest, db=Depends(get_db)):
    # Validate password
    errors = validate_password(req.password)
    if errors:
        raise HTTPException(status_code=400,
                            detail={"message": "Password requirements not met",
                                    "errors": errors})

    username = req.username or req.email.split("@")[0]
    cur      = db.cursor()

    # Check duplicate
    cur.execute("SELECT id FROM users WHERE email = %s", (req.email.lower(),))
    if cur.fetchone():
        raise HTTPException(status_code=409,
                            detail="An account with this email already exists")

    # Create user
    user_id = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO users (id, email, username, password_hash) VALUES (%s, %s, %s, %s)",
        (user_id, req.email.lower(), username, hash_password(req.password))
    )
    db.commit()

    token = create_jwt(user_id, req.email.lower())
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=user_id, email=req.email.lower(),
                          username=username,
                          created_at=datetime.now(timezone.utc).isoformat())
    )


@app.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute(
        "SELECT id, email, username, password_hash, created_at FROM users WHERE email = %s",
        (req.email.lower(),)
    )
    user = cur.fetchone()

    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401,
                            detail="Invalid email or password")

    token = create_jwt(str(user["id"]), user["email"])
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=str(user["id"]), email=user["email"],
                          username=user["username"],
                          created_at=user["created_at"].isoformat())
    )


@app.post("/auth/password-reset/request")
def request_password_reset(req: ResetRequestModel, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT id FROM users WHERE email = %s", (req.email.lower(),))
    user = cur.fetchone()

    # Always return success to prevent email enumeration
    if not user:
        return {"message": "If that email exists, a reset link has been sent"}

    token      = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    cur.execute(
        "INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)",
        (str(user["id"]), token, expires_at)
    )
    db.commit()

    # In production this would send an email
    # For UAT we return the token directly so testers can use it
    return {"message": "Reset token generated",
            "token": token,
            "note": "UAT mode: token returned directly instead of emailed"}


@app.post("/auth/password-reset/complete")
def complete_password_reset(req: ResetCompleteModel, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute(
        """SELECT t.id, t.user_id, t.expires_at, t.used
           FROM password_reset_tokens t
           WHERE t.token = %s""",
        (req.token,)
    )
    token_row = cur.fetchone()

    if not token_row:
        raise HTTPException(status_code=400, detail="Invalid reset token")
    if token_row["used"]:
        raise HTTPException(status_code=400, detail="Token already used")
    if token_row["expires_at"] < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Token has expired")

    errors = validate_password(req.new_password)
    if errors:
        raise HTTPException(status_code=400,
                            detail={"message": "Password requirements not met",
                                    "errors": errors})

    cur.execute(
        "UPDATE users SET password_hash = %s WHERE id = %s",
        (hash_password(req.new_password), str(token_row["user_id"]))
    )
    cur.execute(
        "UPDATE password_reset_tokens SET used = TRUE WHERE id = %s",
        (str(token_row["id"]),)
    )
    db.commit()
    return {"message": "Password reset successfully"}


@app.get("/auth/me")
def get_current_user(authorization: str = "", db=Depends(get_db)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization[7:]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    cur = db.cursor()
    cur.execute(
        "SELECT id, email, username, created_at FROM users WHERE id = %s",
        (payload["sub"],)
    )
    user = cur.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(id=str(user["id"]), email=user["email"],
                        username=user["username"],
                        created_at=user["created_at"].isoformat())

# ── Jira Proxy Endpoints ────────────────────────────────────────────────────────

import httpx
from fastapi import Query
from fastapi.middleware.cors import CORSMiddleware

JIRA_BASE_URL  = os.getenv("JIRA_BASE_URL", "")
JIRA_EMAIL     = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_PROJECT   = os.getenv("JIRA_PROJECT_KEY", "SDT1")


def jira_auth():
    import base64 as b64
    creds = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
    encoded = b64.b64encode(creds.encode()).decode()
    return {"Authorization": f"Basic {encoded}", "Accept": "application/json", "Content-Type": "application/json"}


@app.get("/proxy/jira/issues")
async def proxy_jira_issues(
    status: str = Query(None, description="Filter by status e.g. 'To Do', 'Done'"),
    max_results: int = Query(100)
):
    """Proxy Jira issues to avoid CORS issues in the browser."""
    if not JIRA_BASE_URL:
        return {"issues": [], "error": "JIRA_BASE_URL not configured"}
    
    jql = f"project = {JIRA_PROJECT} ORDER BY updated DESC"
    if status:
        jql = f"project = {JIRA_PROJECT} AND status = \"{status}\" ORDER BY updated DESC"
    
    fields = "summary,status,priority,issuetype,assignee,customfield_10016,customfield_10071"
    url = f"{JIRA_BASE_URL}/rest/api/3/search/jql"
    
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(
                url,
                headers=jira_auth(),
                params={"jql": jql, "maxResults": max_results, "fields": fields},
                timeout=15.0
            )
            if r.status_code == 200:
                data = r.json()
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


@app.get("/proxy/jira/issue/{issue_key}/transitions")
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


@app.post("/proxy/jira/issue/{issue_key}/transition")
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

# ── Sprint Proxy Endpoints ──────────────────────────────────────────────────────

@app.get("/proxy/jira/sprints")
async def proxy_jira_sprints():
    """Get all sprints from Jira - combines fix versions and native sprints."""
    if not JIRA_BASE_URL:
        return {"sprints": [], "error": "JIRA_BASE_URL not configured"}
    async with httpx.AsyncClient() as client:
        try:
            # Get fix versions (our manual sprint tracking)
            versions_r = await client.get(
                f"{JIRA_BASE_URL}/rest/api/3/project/{JIRA_PROJECT}/versions",
                headers=jira_auth(), timeout=10.0
            )
            # Get native Jira sprints from agile board
            sprints_r = await client.get(
                f"{JIRA_BASE_URL}/rest/agile/1.0/board/34/sprint",
                headers=jira_auth(), timeout=10.0,
                params={"maxResults": 50}
            )

            sprints = []
            seen_names = set()

            # Build native sprint number->id map (e.g. sprint 4 -> id 71)
            import re as _re
            native_sprint_map = {}
            if sprints_r.status_code == 200:
                for s in sprints_r.json().get("values", []):
                    m = _re.search(r'sprint\s+(\d+)', s.get("name", ""), _re.IGNORECASE)
                    if m:
                        native_sprint_map[int(m.group(1))] = str(s["id"])

            # Add fix versions, enriched with matching native sprint ID by number
            if versions_r.status_code == 200:
                for idx, v in enumerate(versions_r.json(), start=1):
                    if not v.get("archived", False):
                        vname = v["name"]
                        # Extract sprint number from version name
                        m = _re.search(r'sprint\s+(\d+)', vname, _re.IGNORECASE)
                        sprint_num = int(m.group(1)) if m else idx
                        native_id = native_sprint_map.get(sprint_num)
                        sprints.append({
                            "id":        v["id"],
                            "nativeId":  native_id,
                            "name":      vname,
                            "released":  v.get("released", False),
                            "type":      "version",
                        })
                        seen_names.add(vname.lower())

            # Add native sprints only if no fix versions exist at all
            if sprints_r.status_code == 200 and not sprints:
                for s in sprints_r.json().get("values", []):
                    name = s.get("name", "")
                    if s.get("state") != "future":
                        sprints.append({
                            "id":       str(s["id"]),
                            "nativeId": str(s["id"]),
                            "name":     name,
                            "released": s.get("state") == "closed",
                            "type":     "sprint",
                        })

            return {"sprints": sorted(sprints, key=lambda x: str(x["id"]))}
        except Exception as e:
            return {"sprints": [], "error": str(e)}


@app.get("/proxy/jira/sprint/{version_id}/issues")
async def proxy_sprint_issues(version_id: str):
    """Get issues for a specific sprint (version or native sprint ID)."""
    if not JIRA_BASE_URL:
        return {"issues": [], "error": "JIRA_BASE_URL not configured"}

    # Query by fixVersion AND native sprint to catch all tickets
    # version_id may be "versionId|nativeSprintId" format
    parts = version_id.split("|")
    fix_id = parts[0]
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
                data = r.json()
                issues = [
                    {
                        "key":      i["key"],
                        "summary":  i["fields"]["summary"],
                        "status":   i["fields"].get("status", {}).get("name", "Unknown"),
                        "priority": i["fields"].get("priority", {}).get("name", "Medium"),
                        "type":     i["fields"].get("issuetype", {}).get("name", "Story"),
                        "points":   i["fields"].get("customfield_10016") or 0,
                        "order":    i["fields"].get("customfield_10071") or 999,
                        "assignee": i["fields"].get("assignee", {}).get("displayName") if i["fields"].get("assignee") else None,
                    }
                    for i in data.get("issues", [])
                    if i["fields"].get("issuetype", {}).get("name") not in ("Epic", "Sub-task", "Subtask")
                ]
                # Deduplicate by key
                seen = set()
                unique = []
                for i in issues:
                    if i["key"] not in seen:
                        seen.add(i["key"])
                        unique.append(i)
                return {"issues": unique, "total": len(unique)}
            return {"issues": [], "error": f"Jira returned {r.status_code}"}
        except Exception as e:
            return {"issues": [], "error": str(e)}

# ── PM Agent Endpoints ──────────────────────────────────────────────────────────

import anthropic as _anthropic
from pydantic import BaseModel as _BaseModel
from typing import List as _List, Optional as _Optional

class PMAgentMessage(_BaseModel):
    message: str
    history: _Optional[_List[dict]] = []

class SprintBriefRequest(_BaseModel):
    brief: str
    history: _Optional[_List[dict]] = []

def _get_anthropic_client():
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not configured")
    return _anthropic.Anthropic(api_key=api_key)

PM_AGENT_SYSTEM = """You are a Product Manager AI agent for a software development team.
Your role is to help plan sprints, create user stories, and manage product backlogs.

When given a feature brief, you should:
1. Break it down into epics and user stories
2. Estimate story points (1, 2, 3, 5, 8, 13)
3. Define acceptance criteria for each story
4. Suggest execution order based on dependencies
5. Flag any risks or dependencies

Format stories as:
- Title: clear, concise
- Description: as a [user], I want [feature] so that [benefit]
- Acceptance criteria: bullet points
- Story points: number
- Priority: Highest/High/Medium/Low/Lowest
- Execution order: number

Always ask clarifying questions if the brief is unclear."""

@app.post("/api/pm-agent/chat")
async def pm_agent_chat(request: PMAgentMessage):
    """Chat with the PM Agent."""
    try:
        client = _get_anthropic_client()
        messages = []
        for h in (request.history or []):
            if h.get("role") in ("user", "assistant"):
                messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": request.message})
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=2000,
            system=PM_AGENT_SYSTEM,
            messages=messages,
        )
        reply = response.content[0].text
        return {"reply": reply, "role": "assistant"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pm-agent/generate-sprint")
async def pm_agent_generate_sprint(request: SprintBriefRequest):
    """Generate a sprint plan from a feature brief."""
    try:
        client = _get_anthropic_client()
        prompt = f"""Given this feature brief, create a complete sprint plan:

{request.brief}

Return a JSON object with this structure:
{{
  "epic": {{
    "title": "Epic title",
    "description": "Epic description"
  }},
  "stories": [
    {{
      "title": "Story title",
      "description": "As a user...",
      "acceptance_criteria": ["criterion 1", "criterion 2"],
      "story_points": 5,
      "priority": "High",
      "execution_order": 1
    }}
  ],
  "summary": "Brief summary of the sprint plan",
  "total_points": 0,
  "risks": ["risk 1"]
}}

Return ONLY valid JSON, no markdown."""

        messages = []
        for h in (request.history or []):
            if h.get("role") in ("user", "assistant"):
                messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": prompt})

        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4000,
            system=PM_AGENT_SYSTEM,
            messages=messages,
        )
        import json as _json
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:-1])
        plan = _json.loads(raw)
        return {"plan": plan, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

