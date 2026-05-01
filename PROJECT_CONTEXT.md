# PROJECT_CONTEXT.md — Virtual Dev Team

> Deep implementation reference for Claude Code sessions.
> Supplements CLAUDE.md — read CLAUDE.md first for project overview, sprint history, and environment setup.
> Last updated: 2026-04-30 (Sprint 5 complete)

---

## Table of Contents

1. [Agent Workflow Logic & Rules](#1-agent-workflow-logic--rules)
2. [Multi-Agent Coordination](#2-multi-agent-coordination)
3. [API Endpoints (UAT Backend)](#3-api-endpoints-uat-backend)
4. [Component Structure & Data Flow](#4-component-structure--data-flow)
5. [Tool Implementations](#5-tool-implementations)
6. [GitHub Actions Workflows](#6-github-actions-workflows)
7. [Key Constants & Rules](#7-key-constants--rules)
8. [CI/CD Logic & Skip Rules](#8-cicd-logic--skip-rules)
9. [Error Handling Patterns](#9-error-handling-patterns)
10. [Utility & Maintenance Scripts](#10-utility--maintenance-scripts)

---

## 1. Agent Workflow Logic & Rules

### PM Agent (`agents/pm_agent.py`)

**Framework:** CrewAI + Claude Sonnet 4.5 (Anthropic SDK)

**Two task modes:**
- `groom` — Cleans up backlog: adds descriptions, story points, priorities; no brief needed
- `plan --brief "..."` — Creates Epic + 4-6 Stories, creates Sprint 1, assigns stories to sprint

**Tool groups (split to avoid CrewAI schema limits):**
- `BACKLOG_TOOLS` — List backlog, list all issues, create Epic/Story, update issue
- `SPRINT_TOOLS` — List sprints, create sprint, add to sprint, post comment, transition issue
- `ALL_PM_TOOLS` — Both combined

**Hard rules baked into system prompt:**
- Never invent Jira issue keys — always retrieve from API first
- Check for duplicates before creating new issues
- Story summaries must be under 100 characters
- Story points must be Fibonacci: 1, 2, 3, 5, 8, 13 (max 8 per story)
- Stories over 8 points get a FLAGGED Jira comment recommending split
- Target 20–40 story points per sprint
- Always link Stories to their parent Epic
- Priorities: Highest, High, Medium, Low (never invent others)
- `customfield_10071` = execution order (integer, determines implementation sequence)

**Sprint assignment mechanism:**
- Uses `fixVersions` field, not native Jira sprint field
- Sprint IDs map to Jira "versions": Sprint 1=10000, Sprint 2=10033, Sprint 3=10066, Sprint 4=10099
- Native sprint IDs (for JQL): Sprint 1=35, Sprint 2=69, Sprint 3=70, Sprint 4=71, Sprint 5=72
- Backend uses dual JQL: `fixVersion = {fix_id} OR sprint = {native_id}` to catch all tickets

---

### Dev Agent (`agents/dev_agent.py`)

**Framework:** CrewAI + Claude Sonnet 4.5

**Workflow (in order):**
1. Call `EnsureRepoTool` — creates repo if missing
2. Call `ListBranchesTool` — check for existing feature branch
3. Call `CreateBranchTool` — create `feature/<ticket-id>-<slug>` from main
4. Write implementation files one by one using `CommitFileTool`
5. Call `CreatePRTool` — opens PR (returns existing if already open for branch)

**Branch naming:**
- Pattern: `feature/<ticket-id>-<slug>`
- Slug: lowercase, max 40 chars, only `[a-z0-9-]`
- Always branches from latest `main`

**Code standards enforced by system prompt:**
- Python 3.11+, type hints on all functions
- Docstrings on classes and all public functions
- No hardcoded secrets (use environment variables)
- Functions under 30 lines where possible
- Files organized under `src/<module>/` and `tests/`
- Always include `requirements.txt` and `README.md`

**Critical constraint:** Use `CommitFileTool` once per file. Never use `CommitMultipleFilesTool` in CrewAI mode (only used in CI mode).

---

### Manager Agent (`agents/manager_agent.py`)

**Framework:** CrewAI + Claude Sonnet 4.5

**Review process (sequential steps):**
1. `ListOpenPRsTool` — find open PRs
2. `GetPRDetailsTool(pr_number)` — title, description, files changed
3. `GetCIStatusTool(pr_number)` — check all CI check-runs
4. `GetPRDiffTool(pr_number)` — read code diff (truncated to 8000 chars)
5. Decide: APPROVE → `ApprovePRTool` then `MergePRTool`, or REQUEST_CHANGES → `RequestChangesTool`

**Merge conditions (all must pass):**
- All blocking CI jobs passing: `test` matrix (Python 3.11 + 3.12) and `security` (bandit)
- SonarCloud, Playwright E2E, and Railway deploy are **not** blocking — see Section 8
- No merge conflicts (`pr.mergeable` must be True)
- Code has proper structure, type hints, docstrings
- No hardcoded secrets detected in diff

**Why `ApprovePRTool` posts a comment instead of a review approval:**
GitHub blocks self-approval on repositories — the GITHUB_TOKEN belongs to the same account that owns the repo, so submitting a formal "APPROVED" review is rejected. The workaround is posting an approval comment, then immediately calling `MergePRTool`.

**Post-merge actions (always done):**
1. `UpdateJiraStatusTool(issue_key, "Done")` — transitions Jira ticket
2. `PostJiraCommentTool(issue_key, body)` — posts PR reference + summary to Jira

**Ticket key extraction from PR:**
1. Try PR title regex: `\[([A-Z]+-\d+)\]` (e.g., `[SDT1-31]`)
2. Fallback: branch name regex `feature/([a-z0-9]+-\d+)-`

---

### CI Dev Agent (`ci_dev_agent.py`)

**Purpose:** Standalone (no CrewAI) Dev Agent for GitHub Actions. Uses raw Anthropic SDK calls with tool_use content blocks.

**Ticket type detection (by keywords in summary, case-insensitive):**
- Control Centre tickets: `dashboard`, `ui`, `sprint status`, `workflow monitor`, `sonarcloud`, `pm agent chat`, `sprint trigger`, `auto review`, `control centre`, `control center`
- All others: Python/Auth tickets (default)

**Behavior difference by ticket type:**

| Behaviour | Control Centre | Python/Auth |
|-----------|---------------|-------------|
| Target directory | `control-centre/` | `src/auth/` and `tests/` |
| Read existing files before writing | Yes (list_tree + get_file) | Yes |
| Update README.md | No | Append |
| Update requirements.txt | No | Append + deduplicate |
| Update `src/auth/__init__.py` | No | Yes |

**Deduplication logic for requirements.txt:**
- Split each line on `==` or `>=` to get package name
- Keep only latest occurrence by package name
- Prevents duplicate entries when agent appends to existing file

**JSON response salvage:**
- If Claude returns malformed JSON, attempts regex extraction: `r'"files"\s*:\s*\[.*?\]'` with `re.DOTALL`
- Falls back to empty files list if salvage fails

**Branch strategy:**
- Gets latest `main` SHA
- Deletes existing feature branch if present (prevents merge conflicts on retrigger)
- Creates fresh branch from `main`

---

### CI Manager Agent (`ci_manager_agent.py`)

**Purpose:** Standalone Manager Agent for GitHub Actions.

**Entry modes:**
- `--auto` — reads environment: `PR_NUMBER`, `EVENT_NAME`, `MANUAL_PR`, `HEAD_SHA`
- `--pr <N>` — explicit PR number for manual runs

**CI waiting logic:**
- Polls `/repos/{owner}/{repo}/commits/{sha}/check-runs` every 10 seconds
- Timeout: 15 minutes
- A check-run is considered "done" when `status == "completed"`
- Ignored check-run names: `"Manager Agent review"`, `"wait-and-review"`, any job with `"manually triggered"` in name
- Result: True if all completed check-runs have `conclusion == "success"`, False if any failed

**Merge conflict handling:**
- Checks `pr.mergeable` field from GitHub API
- If False: posts comment on the PR explaining the conflict, closes PR, posts Jira comment, triggers `auto-implement` workflow via `DISPATCH_HEADERS` (PAT_TOKEN — GITHUB_TOKEN cannot dispatch workflows)
- Retrigger failure is not silent: if dispatch returns non-2xx, posts a PR comment saying manual intervention required
- The `trigger_auto_implement()` helper centralises all three retrigger call sites

**Merge method:** Always squash merge — produces a single clean commit on `main`.

**Jira status transition aliases handled:**
`"Closed"`, `"Complete"`, `"Completed"`, `"Finished"` → all mapped to `"Done"`

---

## 2. Multi-Agent Coordination

### Interactive Mode (local CLI)

```
python main.py --agent sprint
          │
          ▼
    orchestrator.py
          │
          ├─ Fetches To Do tickets sorted by customfield_10071
          │
          └─ For each ticket (serial):
               ├─ Triggers auto-implement workflow (GitHub Actions API)
               ├─ Polls for PR (max 5 min, every 10 sec)
               ├─ Polls for CI passing (max 15 min)
               ├─ Triggers auto-review workflow (GitHub Actions API)
               └─ Polls for merge (max 10 min)
```

**Predefined execution order fallback (Sprint 4):**
```python
EXECUTION_ORDER = ["SDT1-31", "SDT1-36", "SDT1-33", "SDT1-29", "SDT1-30", "SDT1-28", "SDT1-35"]
```
Primary sort is `customfield_10071`; this list is fallback when field is missing.

**Orchestrator loop model (while-loop, re-queries Jira per iteration):**
`run_sprint()` calls `get_open_sprint_tickets()` at the top of every iteration and processes `tickets[0]` — always the lowest execution-order To Do ticket. Loop exits when Jira returns an empty list. This means:
- A ticket moved to Done mid-run is never revisited
- A ticket that fails but remains To Do is automatically retried on the next iteration
- Restarting the Orchestrator mid-sprint is always safe — already-Done tickets are never picked up

### Automated Mode (GitHub Actions)

```
Push to feature/* branch
          │
          ▼
   ci.yml triggers
   (test, security, sonar, e2e, deploy)
          │
          ▼
   auto-review.yml triggers
   (on pull_request: opened/synchronize/reopened)
          │
          ▼
   ci_manager_agent.py --auto
          │
          ├─ Wait for all CI checks on HEAD_SHA
          ├─ Check mergeable state
          ├─ Call Claude to review diff
          │
          ├─ APPROVE → squash merge → update Jira → post comment
          └─ REQUEST_CHANGES → post comment only
```

### Conflict Recovery Flow

```
ci_manager_agent detects merge conflict
          │
          ├─ post_comment() on PR: explains conflict, says retrigger incoming
          ├─ Closes PR via GitHub API
          ├─ Posts Jira comment: "Merge conflict — PR closed"
          └─ trigger_auto_implement() using DISPATCH_HEADERS (PAT_TOKEN)
               ├─ Success (204): Auto Implement fires for the ticket
               └─ Failure (4xx): posts PR comment "retrigger failed — manual intervention required"

ci_dev_agent receives feedback
          │
          └─ Deletes existing branch, recreates from latest main SHA
               (feedback string included in system prompt context)
```

**Why PAT_TOKEN:** GITHUB_TOKEN is blocked by GitHub from triggering `workflow_dispatch` on other workflows (recursive loop prevention). Using GITHUB_TOKEN caused all retriggering to silently fail — confirmed on PR #98 (SDT1-46 stranded). Fixed in PR #101.

### Agent Communication (no shared state)

Agents do not share memory or communicate directly. Coordination happens through:
- **GitHub API** — PR state, CI check status, merge status
- **Jira API** — ticket status transitions, comments
- **GitHub Actions** — workflow dispatch events carrying `ticket`, `summary`, `feedback` inputs

---

## 3. API Endpoints (UAT Backend)

**Base URL:** `https://synpro-virtual-dev-team-production.up.railway.app`  
**Source:** `uat/backend/main.py` (router split — SDT1-47)  
**Framework:** FastAPI (Python)  
**CORS:** Configured via `FRONTEND_URL` env var (default: `*`). Must be `*` or explicitly include the Control Centre URL (`https://control-centre-service-production.up.railway.app`). If set to the UAT frontend URL only, all Control Centre proxy calls fail — browser receives no `Access-Control-Allow-Origin` header. Set `FRONTEND_URL=*` in Railway backend service variables for UAT.

**Backend router modules** (`uat/backend/`):
- `auth.py` — registration, login, JWT, password reset
- `profile.py` — profile read/update
- `notifications.py` — notification system
- `proxy.py` — Jira proxy endpoints (avoids CORS)
- `pm_agent.py` — PM Agent chat and sprint generation
- `manager_agent_router.py` — Jira transition endpoints with exponential backoff retry (self-contained, no imports from `agents/`)

### Auth Endpoints

| Method | Path | Auth Required | Description |
|--------|------|---------------|-------------|
| POST | `/auth/register` | No | Register new user |
| POST | `/auth/login` | No | Authenticate, get JWT |
| POST | `/auth/password-reset/request` | No | Request password reset token |
| POST | `/auth/password-reset/complete` | No | Consume token, set new password |
| GET | `/auth/me` | Bearer JWT | Get current user info |
| GET | `/health` | No | Health check |

**`POST /auth/register` — Request/Response:**
```json
// Request
{ "email": "...", "password": "...", "username": "..." }

// Response 201
{ "access_token": "...", "token_type": "bearer",
  "user": { "id": 1, "email": "...", "username": "...", "created_at": "..." } }
```
Password validation: min 8 chars, at least one uppercase, lowercase, digit, special character.

**`POST /auth/password-reset/request` — UAT behaviour:**
Always returns HTTP 200 (prevents email enumeration). In UAT mode, returns `reset_token` directly in response body instead of sending email. This is **UAT Finding #1** — to be fixed in Sprint 5 (S5-14).

**JWT config:**
- Algorithm: HS256
- Expiry: 24 hours (configurable via `JWT_EXPIRY_HOURS` env var)
- Signing secret: `JWT_SECRET` env var (dev default: `"dev-secret-change-in-production"`)
- Password hashing: PBKDF2-HMAC-SHA256, 32-byte salt, 100,000 iterations

### Jira Proxy Endpoints

Exist because Jira Cloud blocks CORS from browser — all Jira calls from Control Centre go through these.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/proxy/jira/issues` | List issues, optional `?status=` filter |
| GET | `/proxy/jira/issue/{issue_key}/transitions` | Available status transitions |
| POST | `/proxy/jira/issue/{issue_key}/transition` | Execute a transition |
| GET | `/proxy/jira/sprints` | List sprints (combines fixVersions + native sprints) |
| GET | `/proxy/jira/sprint/{version_id}/issues` | Issues in a sprint |

### PM Agent Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/pm-agent/chat` | Stateless chat with PM Agent (Claude Sonnet 4.5) |
| POST | `/api/pm-agent/generate-sprint` | Generate sprint plan from brief |

**`POST /api/pm-agent/generate-sprint` — Response shape:**
```json
{
  "epic": { "title": "...", "description": "..." },
  "stories": [
    { "title": "...", "description": "...", "points": 5, "priority": "High" }
  ],
  "summary": "...",
  "total_points": 38,
  "risks": ["..."]
}
```
Note: This endpoint generates JSON but does **not** push to Jira. The Control Centre "Generate Sprint Plan" button calls this but the approve-to-Jira flow is not wired (Sprint 5 — S5-11).

### Database Schema

```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR UNIQUE NOT NULL,
  username VARCHAR,
  password_hash VARCHAR NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE password_reset_tokens (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  token VARCHAR UNIQUE NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  used BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 4. Component Structure & Data Flow

### UAT Frontend (`uat/frontend/src/`)

```
src/
├── App.jsx          — Router, auth state, localStorage
├── api.js           — Axios instance, all API call wrappers
└── pages/
    ├── LoginPage.jsx         — Email/password form → /auth/login
    ├── RegisterPage.jsx      — Email/username/password → /auth/register
    ├── DashboardPage.jsx     — Protected: user info display + sign out
    ├── ResetRequestPage.jsx  — Email → /auth/password-reset/request
    └── ResetCompletePage.jsx — Token + new password → /auth/password-reset/complete
```

**Auth state management:**
- `user` and `token` in React state (App.jsx)
- `token` persisted to `localStorage` (key: `"token"`)
- On mount: reads localStorage, calls `/auth/me` to validate, restores session
- On sign out: clears state + localStorage

**Route protection:**
- `/dashboard` redirects to `/login` if `token` is null
- `/login` and `/register` redirect to `/dashboard` if `token` is set

**API client (`api.js`):**
- Base URL: `VITE_API_URL` environment variable (empty string = same origin)
- `Content-Type: application/json` header on all requests
- `getErrorMessage(error)` — extracts `error.response.data.detail` for display

### Control Centre (deployed separately)

**Source:** In GitHub repo (`synproconsulting/synpro-virtual-dev-team`), not in local working directory.  
**Deployed to:** `https://control-centre-service-production.up.railway.app`

**Architecture:**
```
Browser → GitHub API (direct — CORS allowed by GitHub)
Browser → FastAPI backend (proxy — /proxy/jira/*)
Browser → Anthropic API (via /api/pm-agent/* — API key never in browser)
```

**Tab status:**

| Tab | Working | Notes |
|-----|---------|-------|
| Overview | No | Needs redesign (Sprint 5 — S5-07) |
| Sprint Status | Yes | Sprint selector, per-ticket PR refs, CI runs |
| Workflows | Yes | GitHub Actions monitor, auto-refresh every 30s |
| UAT Deploy | No | Static form, not wired to Railway API (S5-02) |
| SonarCloud | No | Trigger only, no results view (S5-09) |
| PM Agent | Partial | Chat works; history not persisted (S5-10); approve not wired to Jira (S5-11) |

**Data flow — Sprint Status tab:**
```
Control Centre → GET github.com/api.v3/repos/.../actions/runs
               → GET /proxy/jira/sprint/{id}/issues
               → GET /proxy/jira/issues?status=...
               → Renders ticket list with PR links + CI badge
```

---

## 5. Tool Implementations

### GitHub Client (`tools/github_client.py`)

Low-level GitHub REST API v3 wrapper. All methods raise `Exception` on non-2xx responses.

**Key methods:**

| Method | Notes |
|--------|-------|
| `ensure_repo_exists()` | Creates repo if missing; idempotent |
| `get_branch_sha(branch)` | Returns latest commit SHA — required for all write ops |
| `commit_file(path, content, message, branch)` | Handles both new files (no SHA) and updates (fetches existing SHA first) |
| `commit_multiple_files(files, message, branch)` | Git Trees API — creates tree + commit in one call; clean single commit |
| `create_pull_request(title, body, head, base)` | Returns existing PR if branch already has one open |
| `list_tree(branch, path_prefix)` | Recursive tree of blobs — used by CI Dev Agent to read existing files |

**Why single-file commits in CrewAI mode:**
Each `commit_file` call is a separate tool invocation. CrewAI agents call tools one at a time; the `commit_multiple_files` tool exists for CI mode where Claude returns a JSON array of files in one response.

### Jira Client (`tools/jira_client.py`)

Low-level Jira Cloud REST API v3 wrapper.

**Custom fields:**
- `customfield_10016` = Story Points
- `customfield_10071` = Execution Order

**ADF conversion:**
All description text must be in Atlassian Document Format. The `_adf(text)` helper wraps plain text:
```python
def _adf(text: str) -> dict:
    return {
        "type": "doc", "version": 1,
        "content": [{"type": "paragraph",
                     "content": [{"type": "text", "text": text}]}]
    }
```

**Sprint management via versions (not native sprints):**
- `list_sprints()` returns project versions (not Jira's native Sprint API)
- `create_sprint(name, ...)` creates a version; returns existing if name matches
- `add_issues_to_sprint(sprint_id, issue_keys)` sets `fixVersions` field

**Transition logic:**
- `transition_issue(issue_key, status_name)` fetches available transitions first
- Raises `ValueError` with list of valid options if target status not found
- Case-insensitive match on transition name

### CrewAI Tool Wrappers

All tools in `tools/pm_tools.py`, `tools/dev_tools.py`, `tools/manager_tools.py` follow this pattern:
- Subclass `BaseTool` from CrewAI
- `_run(self, ...)` returns a formatted string (never raises — agent sees failure message)
- Field aliases handled for flexibility (e.g., `CommitMultipleFilesTool` accepts `filename`, `file_path`, `code`, `text` as alternatives to `path`, `content`)

**Manager tools split (REVIEW_TOOLS / MERGE_TOOLS):**
CrewAI has a schema size limit per agent. Manager tools are split into two groups and the agent uses both, but they're registered separately to avoid hitting the limit.

---

## 6. GitHub Actions Workflows

### `auto-implement.yml`

**Trigger:** `workflow_dispatch` (manual or API-triggered)  
**Inputs:** `ticket` (required), `summary` (required), `feedback` (optional — for conflict recovery)  
**Runner:** `ubuntu-latest`  
**Permissions:** `contents:write`, `pull-requests:write`  
**Python deps installed:** `anthropic`, `requests`, `python-dotenv`  
**Command:** `python ci_dev_agent.py --ticket ${{ inputs.ticket }} --summary ${{ inputs.summary }} --feedback ${{ inputs.feedback }}`

### `auto-review.yml`

**Triggers:**
- `pull_request` events: `opened`, `synchronize`, `reopened`
- `workflow_dispatch` with optional `pr_number` input

**Runner:** `ubuntu-latest`  
**Permissions:** `contents:write`, `pull-requests:write`, `issues:write`  
**Python deps installed:** `anthropic`, `requests`, `python-dotenv`  
**Command:** `python ci_manager_agent.py --auto`  

**Environment variables passed:**
- `PR_NUMBER` — from PR event context or dispatch input
- `MANUAL_PR` — the dispatch input value (if manually triggered)
- `EVENT_NAME` — `github.event_name`
- `HEAD_SHA` — `github.event.pull_request.head.sha` or `github.sha`
- `PAT_TOKEN` — `${{ secrets.PAT_TOKEN }}` — used by `ci_manager_agent.py` for `workflow_dispatch` retriggers (GITHUB_TOKEN cannot dispatch workflows)

### `ci.yml`

**Triggers:** Push to any branch; PR to `main`

**Job summary:**

| Job | Condition | Blocking | What it does |
|-----|-----------|----------|--------------|
| test (3.11, 3.12) | Always | Yes | pytest, skip `tests/e2e/`, upload coverage |
| security | Always | No (`--exit-zero`) | bandit scan on `src/` |
| sonarcloud | main push only | No (continue-on-error) | Full code analysis |
| quality-gate | After sonarcloud | No | Reads SonarCloud gate result |
| playwright | main push only | No (continue-on-error) | E2E against live UAT backend |
| deploy | main push only | No | Railway GraphQL API `serviceInstanceRedeploy` mutation via `curl` + `jq` — no CLI install required |

**Graceful skip:** If `src/` or `tests/` directories don't exist, test jobs skip without failing.

**Railway deploy flow (GraphQL API):**
1. `printf` constructs query JSON: `project(id: "$RAILWAY_PROJECT_ID"){ environments services }`
2. `jq` with `ascii_downcase` resolves production environment ID and service ID by name
3. `serviceInstanceRedeploy(environmentId, serviceId)` mutation triggers the redeploy
4. Full API response echoed to CI logs; step exits 0 on any error (non-blocking)
5. Service names: backend = `synpro-virtual-dev-team`, frontend = `Virtual-Dev-Team-UAT-Frontend`

---

## 7. Key Constants & Rules

### Story Points
Fibonacci only: `1, 2, 3, 5, 8, 13`  
Maximum per story: **8** (stories with 13 points get a FLAGGED Jira comment)  
Target per sprint: **20–40 points**

### Jira Sprint IDs

| Sprint | Fix Version ID | Native Sprint ID |
|--------|---------------|-----------------|
| Sprint 1 | 10000 | 35 |
| Sprint 2 | 10033 | 69 |
| Sprint 3 | 10066 | 70 |
| Sprint 4 | 10099 | 71 |
| Sprint 5 | 10132 | 72 |

### CI Timeout Values (orchestrator)

| Wait | Max time | Poll interval |
|------|----------|---------------|
| PR open | 5 minutes | 10 seconds |
| CI passing | 15 minutes | 10 seconds |
| PR merged | 10 minutes | 10 seconds |

### CI Timeout (ci_manager_agent)

| Wait | Max time | Poll interval |
|------|----------|---------------|
| Check-runs complete | 15 minutes | 10 seconds |

### PR Diff Truncation
`GetPRDiffTool` truncates diff to **8000 characters** before sending to Claude. Large PRs may have incomplete diff context.

### Execution Order Default
Tickets without `customfield_10071` set get execution order **999** (placed at end of queue).

---

## 8. CI/CD Logic & Skip Rules

### Jobs Ignored by Manager Agent

When waiting for CI, the CI Manager Agent skips these check-run names:
- `"Manager Agent review"`
- `"wait-and-review"`
- Any name containing `"manually triggered"`

This prevents the agent from waiting on its own review job or on manual-trigger-only jobs.

### Non-Blocking CI Jobs — Excluded from Merge Gate by Design

These jobs run with `continue-on-error: true` or `--exit-zero` in `ci.yml`. They are **deliberately excluded** from the Manager Agent's merge gate and must never be added as blocking conditions:

| Job | Reason excluded |
|---|---|
| SonarCloud analysis | Triggered manually from Control Centre before TEST/PROD promote, not on every PR |
| SonarCloud quality gate | Depends on SonarCloud analysis job; same exclusion applies |
| Playwright E2E tests | Informational only at UAT stage; will gate TEST/PROD in a future sprint |
| Railway deploy | Runs on `main` push after merge; not a pre-merge gate |

**This is an architectural decision, not a gap.** SonarCloud analysis is invoked selectively from the Control Centre dashboard on specific components before a build is promoted to TEST or PROD. Running it on every feature-branch PR would be redundant and costly.

The Manager Agent (`manager_agent.py`, `ci_manager_agent.py`) and any tool evaluating merge readiness (`GetCIStatusTool`) must only treat the following as blocking:

### Blocking CI Jobs (will prevent merge)

- `test` matrix jobs (Python 3.11 and 3.12)
- `security` scan (bandit)

### Control Centre Ticket Detection

`ci_dev_agent.py` detects Control Centre tickets by keywords in the summary (case-insensitive):

```python
CC_KEYWORDS = [
    "control centre", "control center", "dashboard", "ui",
    "sprint status", "workflow monitor", "sonarcloud",
    "pm agent chat", "sprint trigger", "auto review"
]
```

When detected: files go to `control-centre/`, shared files (`README.md`, `requirements.txt`, `src/auth/__init__.py`) are NOT modified.

---

## 9. Error Handling Patterns

### GitHub Client
- Non-2xx responses: `raise Exception(f"GitHub API error {status}: {text[:400]}")`
- File updates: Always fetches current SHA first via `get_file()` before `commit_file()` — avoids SHA mismatch errors

### Jira Client
- Transition failures: `raise ValueError(f"Status '{name}' not found. Available: {list}")`
- Other failures: `raise Exception` with response body

### CrewAI Tools
- All `_run()` methods catch exceptions and return error strings
- Agent sees: `"Error: <message>"` in tool result and can decide next step
- Never raises — raising inside a tool crashes the CrewAI task

### CI Dev Agent (JSON salvage)
```python
# If Claude response is not valid JSON:
match = re.search(r'"files"\s*:\s*\[.*?\]', response_text, re.DOTALL)
if match:
    files = json.loads("{" + match.group() + "}")["files"]
else:
    files = []  # no files to commit
```

### Orchestrator Timeout Handling
- Each polling loop has a hard timeout; on timeout, orchestrator logs warning and moves to next ticket
- Failed tickets (no PR opened, CI failure) are automatically retried on the next while-loop iteration if they remain To Do in Jira
- A ticket that is permanently broken will loop indefinitely — move it to Done or out of To Do in Jira to unblock the sprint

### CI Dev Agent — Directory Path Guard
`gh_read_file` checks `isinstance(data, list)` after parsing the GitHub API response. The Contents API returns a JSON array (not a file dict) when the requested path is a directory. Without this guard, `data["content"]` raises `TypeError` and crashes the entire run. The guard returns `None` (same as 404), letting the agent try a different path.

---

## 10. Utility & Maintenance Scripts

Scripts that have accumulated at the project root from prior sprints. These are not part of the agent pipeline — they're one-off helpers.

| Script | Purpose |
|--------|---------|
| `test_connection.py` | Verify Jira credentials and connectivity |
| `diagnose_board.py` | List all Jira boards visible to the service account |
| `test_github.py` | Test GitHub API connectivity and token scopes |
| `test_jira_transition.py` | Test status transition on a specific ticket |
| `setup_ci.py` | Initial CI setup helper |
| `setup_step5.py` | Sprint 5 setup helper |
| `fix_sonar_issues.py` | Fix SonarCloud configuration issues |
| `push_ci_update.py` | Push CI workflow changes to main |
| `push_ci_to_branch.py` | Push CI workflow changes to a feature branch |

**Note:** These scripts do not use the agent framework — they call the Jira/GitHub clients directly.

---

## Appendix — Environment Variables

### Required for Agents

| Variable | Used by | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | All agents | Claude API key |
| `JIRA_BASE_URL` | PM Agent, Manager | `https://synproconsulting.atlassian.net` |
| `JIRA_EMAIL` | PM Agent, Manager | Service account email |
| `JIRA_API_TOKEN` | PM Agent, Manager | Jira API token |
| `JIRA_PROJECT_KEY` | PM Agent, Manager | `SDT1` |
| `GITHUB_TOKEN` | Dev Agent, Manager | PAT (needs `repo` scope) |
| `GITHUB_USERNAME` | Dev Agent | GitHub org/user (`synproconsulting`) |
| `GITHUB_REPO` | Dev Agent | Repository name (`synpro-virtual-dev-team`) |

### Required for UAT Backend

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | None | PostgreSQL connection string |
| `JWT_SECRET` | `"dev-secret-change-in-production"` | JWT signing secret |
| `FRONTEND_URL` | `"*"` | CORS allowed origins — must be `*` or include Control Centre URL; set in Railway service variables |

### Optional

| Variable | Used by | Description |
|----------|---------|-------------|
| `RAILWAY_TOKEN` | CI deploy | Railway deployment token |
| `RAILWAY_PROJECT_ID` | CI deploy | Railway project UUID |
| `SONAR_TOKEN` | CI SonarCloud | SonarCloud analysis token |
| `JWT_EXPIRY_HOURS` | UAT backend | Token lifetime (default: 24) |
| `OPENAI_API_KEY` | CrewAI | Set to `"sk-no-openai-needed"` — required by CrewAI framework even though Claude is used |
