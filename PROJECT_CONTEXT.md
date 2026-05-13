# PROJECT_CONTEXT.md - Virtual Dev Team

> Deep implementation reference for Claude Code sessions.
> Supplements CLAUDE.md - read CLAUDE.md first for project overview, sprint history, and environment setup.
> Last updated: 2026-05-05 (Sprint 6 complete)

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
11. [CI Dev Agent System Prompt Rules](#11-ci-dev-agent-system-prompt-rules)
12. [Architectural Decisions](#12-architectural-decisions)

---

## 1. Agent Workflow Logic & Rules

### PM Agent (`agents/pm_agent.py`)

**Framework:** CrewAI + Claude Sonnet 4.5 (Anthropic SDK)

**Two task modes:**
- `groom` - Cleans up backlog: adds descriptions, story points, priorities; no brief needed
- `plan --brief "..."` - Creates Epic + 4-6 Stories, creates Sprint 1, assigns stories to sprint

**Tool groups (split to avoid CrewAI schema limits):**
- `BACKLOG_TOOLS` - List backlog, list all issues, create Epic/Story, update issue
- `SPRINT_TOOLS` - List sprints, create sprint, add to sprint, post comment, transition issue
- `ALL_PM_TOOLS` - Both combined

**Hard rules baked into system prompt:**
- Never invent Jira issue keys - always retrieve from API first
- Check for duplicates before creating new issues
- Story summaries must be under 100 characters
- Story points must be Fibonacci: 1, 2, 3, 5, 8, 13 (max 8 per story)
- Stories over 8 points get a FLAGGED Jira comment recommending split
- Target 20-40 story points per sprint
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
1. Call `EnsureRepoTool` - creates repo if missing
2. Call `ListBranchesTool` - check for existing feature branch
3. Call `CreateBranchTool` - create `feature/<ticket-id>-<slug>` from main
4. Write implementation files one by one using `CommitFileTool`
5. Call `CreatePRTool` - opens PR (returns existing if already open for branch)

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
1. `ListOpenPRsTool` - find open PRs
2. `GetPRDetailsTool(pr_number)` - title, description, files changed
3. `GetCIStatusTool(pr_number)` - check all CI check-runs
4. `GetPRDiffTool(pr_number)` - read code diff (truncated to 8000 chars)
5. Decide: APPROVE ? `ApprovePRTool` then `MergePRTool`, or REQUEST_CHANGES ? `RequestChangesTool`

**Merge conditions (all must pass):**
- All blocking CI jobs passing: `test` matrix (Python 3.11 + 3.12) and `security` (bandit)
- SonarCloud, Playwright E2E, and Railway deploy are **not** blocking - see Section 8
- No merge conflicts (`pr.mergeable` must be True)
- Code has proper structure, type hints, docstrings
- No hardcoded secrets detected in diff

**Why `ApprovePRTool` posts a comment instead of a review approval:**
GitHub blocks self-approval on repositories - the GITHUB_TOKEN belongs to the same account that owns the repo, so submitting a formal "APPROVED" review is rejected. The workaround is posting an approval comment, then immediately calling `MergePRTool`.

**Post-merge actions (always done):**
1. `UpdateJiraStatusTool(issue_key, "Done")` - transitions Jira ticket
2. `PostJiraCommentTool(issue_key, body)` - posts PR reference + summary to Jira

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
- `--auto` - reads environment: `PR_NUMBER`, `EVENT_NAME`, `MANUAL_PR`, `HEAD_SHA`
- `--pr <N>` - explicit PR number for manual runs

**CI waiting logic:**
- Polls `/repos/{owner}/{repo}/commits/{sha}/check-runs` every 10 seconds
- Timeout: 15 minutes
- A check-run is considered "done" when `status == "completed"`
- Ignored check-run names: `"Manager Agent review"`, `"wait-and-review"`, any job with `"manually triggered"` in name
- Result: True if all completed check-runs have `conclusion == "success"`, False if any failed

**Merge conflict handling:**
- Checks `pr.mergeable` field from GitHub API
- If False: posts comment on the PR explaining the conflict, closes PR, posts Jira comment, triggers `auto-implement` workflow via `DISPATCH_HEADERS` (PAT_TOKEN - GITHUB_TOKEN cannot dispatch workflows)
- Retrigger failure is not silent: if dispatch returns non-2xx, posts a PR comment saying manual intervention required
- The `trigger_auto_implement()` helper centralises all three retrigger call sites

**Merge method:** Always squash merge - produces a single clean commit on `main`.

**Jira status transition aliases handled:**
`"Closed"`, `"Complete"`, `"Completed"`, `"Finished"` ? all mapped to `"Done"`

---

## 2. Multi-Agent Coordination

### Interactive Mode (local CLI)

```
python main.py --agent sprint
          ?
          ?
    orchestrator.py
          ?
          ?? Fetches To Do tickets sorted by customfield_10071
          ?
          ?? For each ticket (serial):
               ?? Triggers auto-implement workflow (GitHub Actions API)
               ?? Polls for PR (max 5 min, every 10 sec)
               ?? Polls for CI passing (max 15 min)
               ?? Triggers auto-review workflow (GitHub Actions API)
               ?? Polls for merge (max 10 min)
```

**Predefined execution order fallback (Sprint 4):**
```python
EXECUTION_ORDER = ["SDT1-31", "SDT1-36", "SDT1-33", "SDT1-29", "SDT1-30", "SDT1-28", "SDT1-35"]
```
Primary sort is `customfield_10071`; this list is fallback when field is missing.

**Orchestrator loop model (while-loop, re-queries Jira per iteration):**
`run_sprint()` calls `get_open_sprint_tickets()` at the top of every iteration and processes `tickets[0]` - always the lowest execution-order To Do ticket. Loop exits when Jira returns an empty list. This means:
- A ticket moved to Done mid-run is never revisited
- A ticket that fails but remains To Do is automatically retried on the next iteration
- Restarting the Orchestrator mid-sprint is always safe - already-Done tickets are never picked up

### Automated Mode (GitHub Actions)

```
Push to feature/* branch
          ?
          ?
   ci.yml triggers
   (test, security, sonar, e2e, deploy)
          ?
          ?
   auto-review.yml triggers
   (on pull_request: opened/synchronize/reopened)
          ?
          ?
   ci_manager_agent.py --auto
          ?
          ?? Wait for all CI checks on HEAD_SHA
          ?? Check mergeable state
          ?? Call Claude to review diff
          ?
          ?? APPROVE ? squash merge ? update Jira ? post comment
          ?? REQUEST_CHANGES ? post comment only
```

### Conflict Recovery Flow

```
ci_manager_agent detects merge conflict
          ?
          ?? post_comment() on PR: explains conflict, says retrigger incoming
          ?? Closes PR via GitHub API
          ?? Posts Jira comment: "Merge conflict - PR closed"
          ?? trigger_auto_implement() using DISPATCH_HEADERS (PAT_TOKEN)
               ?? Success (204): Auto Implement fires for the ticket
               ?? Failure (4xx): posts PR comment "retrigger failed - manual intervention required"

ci_dev_agent receives feedback
          ?
          ?? Deletes existing branch, recreates from latest main SHA
               (feedback string included in system prompt context)
```

**Why PAT_TOKEN:** GITHUB_TOKEN is blocked by GitHub from triggering `workflow_dispatch` on other workflows (recursive loop prevention). Using GITHUB_TOKEN caused all retriggering to silently fail - confirmed on PR #98 (SDT1-46 stranded). Fixed in PR #101.

### Agent Communication (no shared state)

Agents do not share memory or communicate directly. Coordination happens through:
- **GitHub API** - PR state, CI check status, merge status
- **Jira API** - ticket status transitions, comments
- **GitHub Actions** - workflow dispatch events carrying `ticket`, `summary`, `feedback` inputs

---

## 3. API Endpoints (UAT Backend)

**Base URL:** `https://synpro-virtual-dev-team-production.up.railway.app`  
**Source:** `uat/backend/main.py` (router split - SDT1-47)  
**Framework:** FastAPI (Python)  
**CORS:** Configured via `FRONTEND_URL` env var (default: `*`). Must be `*` or explicitly include the Control Centre URL (`https://control-centre-service-production.up.railway.app`). If set to the UAT frontend URL only, all Control Centre proxy calls fail - browser receives no `Access-Control-Allow-Origin` header. Set `FRONTEND_URL=*` in Railway backend service variables for UAT.

**Backend router modules** (`uat/backend/`):
- `auth.py` - registration, login, JWT, password reset
- `profile.py` - profile read/update
- `notifications.py` - notification system
- `proxy.py` - Jira proxy endpoints (avoids CORS)
- `pm_agent.py` - PM Agent chat and sprint generation
- `manager_agent_router.py` - Jira transition endpoints with exponential backoff retry (self-contained, no imports from `agents/`)

### Auth Endpoints

| Method | Path | Auth Required | Description |
|--------|------|---------------|-------------|
| POST | `/auth/register` | No | Register new user |
| POST | `/auth/login` | No | Authenticate, get JWT |
| POST | `/auth/password-reset/request` | No | Request password reset token |
| POST | `/auth/password-reset/complete` | No | Consume token, set new password |
| GET | `/auth/me` | Bearer JWT | Get current user info |
| GET | `/health` | No | Health check |

**`POST /auth/register` - Request/Response:**
```json
// Request
{ "email": "...", "password": "...", "username": "..." }

// Response 201
{ "access_token": "...", "token_type": "bearer",
  "user": { "id": 1, "email": "...", "username": "...", "created_at": "..." } }
```
Password validation: min 8 chars, at least one uppercase, lowercase, digit, special character.

**`POST /auth/password-reset/request` - UAT behaviour:**
Always returns HTTP 200 (prevents email enumeration). In UAT mode, returns `reset_token` directly in response body instead of sending email. This is **UAT Finding #1** - to be fixed in Sprint 5 (S5-14).

**JWT config:**
- Algorithm: HS256
- Expiry: 24 hours (configurable via `JWT_EXPIRY_HOURS` env var)
- Signing secret: `JWT_SECRET` env var (dev default: `"dev-secret-change-in-production"`)
- Password hashing: PBKDF2-HMAC-SHA256, 32-byte salt, 100,000 iterations

### Jira Proxy Endpoints

Exist because Jira Cloud blocks CORS from browser - all Jira calls from Control Centre go through these.

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

**`POST /api/pm-agent/generate-sprint` - Response shape:**
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
Note: This endpoint generates JSON but does **not** push to Jira. The Control Centre "Generate Sprint Plan" button calls this but the approve-to-Jira flow is not wired (Sprint 5 - S5-11).

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

### New Endpoints Added in Sprint 6

**Orchestrator API** (`/api/orchestrator/*` - SDT1-66): start/resume/pause/cancel sprint execution, query progress, list resumable states. State persisted in `orchestrator_states` table (UUID id, sprint_id, ticket_queue JSON, completed_tickets JSON, failed_tickets JSON, status enum PENDING/RUNNING/PAUSED/COMPLETED/FAILED/CANCELLED).

**Railway API** (`/api/railway/*` - SDT1-58): list projects/services/environments, trigger deployments, query deployment status. Uses `RailwayClient` in `railway_api.py` with `RAILWAY_API_TOKEN` env var.

> **Token naming:** `RAILWAY_TOKEN` = CI deploy token (GitHub Secret). `RAILWAY_API_TOKEN` = backend runtime token (Railway service variable). Both required but for different purposes.

---

## 4. Component Structure & Data Flow

### UAT Frontend (`uat/frontend/src/`)

```
src/
??? App.jsx          - Router, auth state, localStorage
??? api.js           - Axios instance, all API call wrappers
??? pages/
    ??? LoginPage.jsx         - Email/password form ? /auth/login
    ??? RegisterPage.jsx      - Email/username/password ? /auth/register
    ??? DashboardPage.jsx     - Protected: user info display + sign out
    ??? ResetRequestPage.jsx  - Email ? /auth/password-reset/request
    ??? ResetCompletePage.jsx - Token + new password ? /auth/password-reset/complete
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
- `getErrorMessage(error)` - extracts `error.response.data.detail` for display

### Control Centre (deployed separately)

**Source:** In GitHub repo (`synproconsulting/synpro-virtual-dev-team`), not in local working directory.  
**Deployed to:** `https://control-centre-service-production.up.railway.app`

**Architecture:**
```
Browser ? GitHub API (direct - CORS allowed by GitHub)
Browser ? FastAPI backend (proxy - /proxy/jira/*)
Browser ? Anthropic API (via /api/pm-agent/* - API key never in browser)
```

**Tab status:**

| Tab | Working | Notes |
|-----|---------|-------|
| Overview | Yes | Redesigned (Sprint 6 - SDT1-59, PR #147) |
| Sprint Status | Yes | Sprint selector, per-ticket PR refs, CI runs |
| Workflows | Yes | GitHub Actions monitor, auto-refresh every 30s |
| UAT Deploy | Yes | Wired to Railway GraphQL API (Sprint 6 - SDT1-58, PR #125) |
| SonarCloud | Yes | Results view added (Sprint 6 - SDT1-61, PR #135) |
| PM Agent | Partial | Chat works; history not persisted (S5-10); approve not wired to Jira (S5-11) |

**Data flow - Sprint Status tab:**
```
Control Centre ? GET github.com/api.v3/repos/.../actions/runs
               ? GET /proxy/jira/sprint/{id}/issues
               ? GET /proxy/jira/issues?status=...
               ? Renders ticket list with PR links + CI badge
```

---

## 5. Tool Implementations

### GitHub Client (`tools/github_client.py`)

Low-level GitHub REST API v3 wrapper. All methods raise `Exception` on non-2xx responses.

**Key methods:**

| Method | Notes |
|--------|-------|
| `ensure_repo_exists()` | Creates repo if missing; idempotent |
| `get_branch_sha(branch)` | Returns latest commit SHA - required for all write ops |
| `commit_file(path, content, message, branch)` | Handles both new files (no SHA) and updates (fetches existing SHA first) |
| `commit_multiple_files(files, message, branch)` | Git Trees API - creates tree + commit in one call; clean single commit |
| `create_pull_request(title, body, head, base)` | Returns existing PR if branch already has one open |
| `list_tree(branch, path_prefix)` | Recursive tree of blobs - used by CI Dev Agent to read existing files |

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
- `_run(self, ...)` returns a formatted string (never raises - agent sees failure message)
- Field aliases handled for flexibility (e.g., `CommitMultipleFilesTool` accepts `filename`, `file_path`, `code`, `text` as alternatives to `path`, `content`)

**Manager tools split (REVIEW_TOOLS / MERGE_TOOLS):**
CrewAI has a schema size limit per agent. Manager tools are split into two groups and the agent uses both, but they're registered separately to avoid hitting the limit.

---

## 6. GitHub Actions Workflows

### `auto-implement.yml`

**Trigger:** `workflow_dispatch` (manual or API-triggered)  
**Inputs:** `ticket` (required), `summary` (required), `feedback` (optional - for conflict recovery)  
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
- `PR_NUMBER` - from PR event context or dispatch input
- `MANUAL_PR` - the dispatch input value (if manually triggered)
- `EVENT_NAME` - `github.event_name`
- `HEAD_SHA` - `github.event.pull_request.head.sha` or `github.sha`
- `PAT_TOKEN` - `${{ secrets.PAT_TOKEN }}` - used by `ci_manager_agent.py` for `workflow_dispatch` retriggers (GITHUB_TOKEN cannot dispatch workflows)

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
| deploy | main push only | No | Railway GraphQL API `serviceInstanceRedeploy` mutation via `curl` + `jq` - no CLI install required |

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
Target per sprint: **20-40 points**

### Jira Sprint IDs

| Sprint | Fix Version ID | Native Sprint ID |
|--------|---------------|-----------------|
| Sprint 1 | 10000 | 35 |
| Sprint 2 | 10033 | 69 |
| Sprint 3 | 10066 | 70 |
| Sprint 4 | 10099 | 71 |
| Sprint 5 | 10132 | 72 |
| Sprint 6 | 10198 | 105 |
| Sprint 7 | 10231 | 138 |
| Sprint 8 | 10264 | 171 |
| Sprint 9 | 10297 | 204 |
| Sprint 10 | 10330 | 237 |
| Sprint 11 | 10363 | 270 |
| Sprint 12 | 10396 | 303 |
| Sprint 13 | 10429 | 336 |
| Sprint 14 | 10462 | 369 |

### CI Timeout Values (orchestrator)

| Wait | Max time | Poll interval |
|------|----------|---------------|
| PR open | 5 minutes | 10 seconds |
| CI passing | 30 minutes | 10 seconds |
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

### Non-Blocking CI Jobs - Excluded from Merge Gate by Design

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
- File updates: Always fetches current SHA first via `get_file()` before `commit_file()` - avoids SHA mismatch errors

### Jira Client
- Transition failures: `raise ValueError(f"Status '{name}' not found. Available: {list}")`
- Other failures: `raise Exception` with response body

### CrewAI Tools
- All `_run()` methods catch exceptions and return error strings
- Agent sees: `"Error: <message>"` in tool result and can decide next step
- Never raises - raising inside a tool crashes the CrewAI task

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
- A ticket that is permanently broken will loop indefinitely - move it to Done or out of To Do in Jira to unblock the sprint

### CI Dev Agent - Directory Path Guard
`gh_read_file` checks `isinstance(data, list)` after parsing the GitHub API response. The Contents API returns a JSON array (not a file dict) when the requested path is a directory. Without this guard, `data["content"]` raises `TypeError` and crashes the entire run. The guard returns `None` (same as 404), letting the agent try a different path.

---

## 10. Utility & Maintenance Scripts

Scripts that have accumulated at the project root from prior sprints. These are not part of the agent pipeline - they're one-off helpers.

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

**Note:** These scripts do not use the agent framework - they call the Jira/GitHub clients directly.

---

## Appendix - Environment Variables

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
| `FRONTEND_URL` | `"*"` | CORS allowed origins - must be `*` or include Control Centre URL; set in Railway service variables |

### Optional

| Variable | Used by | Description |
|----------|---------|-------------|
| `RAILWAY_TOKEN` | CI deploy | Railway deployment token |
| `RAILWAY_PROJECT_ID` | CI deploy | Railway project UUID |
| `SONAR_TOKEN` | CI SonarCloud | SonarCloud analysis token |
| `JWT_EXPIRY_HOURS` | UAT backend | Token lifetime (default: 24) |
| `OPENAI_API_KEY` | CrewAI | Set to `"sk-no-openai-needed"` - required by CrewAI framework even though Claude is used |


---

## 11. CI Dev Agent System Prompt Rules

Source: `ci_dev_agent.py` - `SYSTEM_PROMPT` constant and `TOOLS` list.

This section documents the full ruleset baked into the CI Dev Agent's system prompt and tool schema. Every Auto Implement run triggered by GitHub Actions (`auto-implement.yml`) operates under these rules. The CrewAI Dev Agent (`agents/dev_agent.py`) enforces the same rules via its backstory - any change must be applied to both (AD-4).

---

### Agent Identity and Configuration

| Setting | Value |
|---|---|
| Role | Skilled Python/React developer implementing Jira tickets |
| Model | `claude-sonnet-4-5` |
| Max tokens per turn | 16 000 |
| Max tool-loop iterations | 40 |
| Stop condition | `stop_reason == "end_turn"` or no tool calls returned |
| Exit on no PR | `sys.exit(1)` - CI step fails and blocks the ticket |

---

### Mandatory Workflow (exact order)

The agent must call four tools in this exact sequence. Calling `stage_file` or `create_pr` before `create_branch` results in an error because `state["branch"]` is `None`.

| Step | Tool | When |
|------|------|------|
| 1 | `create_branch` | First call - always, before reading or staging anything |
| 2 | `read_file` | Before every file that may already exist - existing content must be merged in, never overwritten |
| 3 | `stage_file` | Once per file - supply complete final content |
| 4 | `create_pr` | Once, after all files are staged - commits and opens the PR atomically |

---

### Repository Layout Rules (from system prompt)

| Path | Rule |
|------|------|
| `uat/backend/` | **Flat layout** - all Python files sit directly in `uat/backend/`. No `src/` subdirectory, no `__init__.py` files. Tests go in `uat/backend/tests/`. Imports are flat: `from models import ...` |
| `control-centre/src/components/` | React components |
| `control-centre/src/api/` | API helper modules |
| `agents/`, `tools/` (repo root) | Agent and orchestration code |

---

### Jira Custom Fields (from system prompt)

| Field | Alias | Purpose |
|---|---|---|
| `customfield_10071` | `execution_order` (integer) | Set by PM Agent at sprint planning; read by Orchestrator to sequence tickets |
| `customfield_10016` | `story_points` (integer) | Story point estimate |

---

### Code Standards (from system prompt)

- **Python version:** 3.11+
- **Type hints:** Required on all functions
- **Docstrings:** Required on all public functions and classes
- **Secrets:** Never hardcoded - environment variables only
- **Tests:** Write meaningful pytest tests for all new backend logic
- **File size:** Keep files focused; split across multiple files rather than one large file

---

### Merge Rule (Critical - from system prompt)

> "If `read_file` returns content, you MUST incorporate the existing content into your staged version - never discard existing code when extending a file."

The agent calls `read_file` before touching any shared file (e.g. `models.py`, `main.py`, `requirements.txt`). The returned content is merged with the new changes before staging. Discarding existing code would silently delete all prior work in that file.

---

### Dependency Rule (Critical - from system prompt)

> "`requirements.txt` is a critical file - always read its existing content before writing, never remove existing dependencies, only append new ones. Removing a dependency will break the deployed service for every feature that depends on it."

Applies to `uat/backend/requirements.txt`. This rule is also a Hard Rule in CLAUDE.md and is enforced in the CrewAI Dev Agent backstory (see AD-4).

---

### PR Title Format (from system prompt)

```
[TICKET-ID] Brief description
```

Example: `[SDT1-74] Control Centre shows current sprint status`

`ci_manager_agent.py` parses the ticket key from the PR title using `\[([A-Z]+-\d+)\]`. A missing or malformed bracket causes the Manager Agent to silently skip the Jira status transition after merge.

---

### Tool Definitions (from `TOOLS` list)

#### `create_branch`
- Creates `feature/{ticket}-{slug}` from the latest main SHA
- Deletes any existing branch with the same name first - guarantees a clean diff with no stale commits (AD-3)
- Sets `state["branch"]`; `create_pr` will error if this is unset

#### `read_file`
- Reads a file by path and branch (default: `main`)
- Returns `None` for both 404 (file not found) and directory paths
  - **Directory guard:** checks `isinstance(data, list)` after parsing the GitHub Contents API response. The API returns a JSON array for directory paths, which would raise `TypeError` on `data["content"]` without this guard. Introduced in fix PR #95 (Sprint 5).
- When `None` is returned, the agent sees `"File '...' does not exist on branch '...'"` and should try an alternative path

#### `stage_file`
- Stores `{path: content}` in `state["staged"]`
- All staged files are committed in a single atomic commit when `create_pr` is called

#### `create_pr`
- Idempotent: checks for an existing open PR on the branch first; returns early with the existing PR number if found
- Constructs commit message: `feat({ticket.lower()}): {summary[:60].lower()}`
- Delegates to `gh_commit_files()` which uses the Git Trees API - one clean commit regardless of how many files were staged
- Guards against double-call: returns an error if `state["pr_number"]` is already set
- Calls `sys.exit(1)` if the PR cannot be created (fails the CI step)

---

### State Object

A mutable `state` dict is passed by reference to every tool call, carrying context across the entire loop:

```python
state = {
    "ticket":    str,         # e.g. "SDT1-74"
    "summary":   str,         # e.g. "Control Centre shows current sprint status"
    "branch":    str | None,  # set by create_branch; None until then
    "staged":    dict,        # {path: content} accumulated by stage_file calls
    "pr_number": int | None,  # set by create_pr on success
    "pr_url":    str | None,  # set by create_pr on success
}
```

---

### Branch Naming

Derived at runtime from ticket ID and summary:

```python
slug        = re.sub(r'[^a-z0-9-]', '-', summary.lower())[:40].rstrip('-')
branch_name = f"feature/{ticket.lower()}-{slug}"
```

Example: `SDT1-74` + `"Control Centre shows current sprint status"` ? `feature/sdt1-74-control-centre-shows-current-sprint`

---

### Feedback / Conflict-Retrigger Behaviour

When `ci_manager_agent.py` detects a merge conflict it closes the PR and retriggers `auto-implement.yml` with a `--feedback` string. The agent prepends this to the task context:

```
FEEDBACK FROM PREVIOUS ATTEMPT (address all points):
{feedback}
```

`create_branch` then deletes the stale branch and recreates it from the latest main SHA, ensuring the retrigger starts clean with no pre-existing conflicts (AD-3, AD-18).

---

### Relationship to CrewAI Dev Agent

`ci_dev_agent.py` and `agents/dev_agent.py` are intentional duplicates maintained in sync by hand (AD-4). The CI agent uses the raw Anthropic SDK tool-use loop; the CrewAI agent uses `BaseTool` subclasses. Both enforce identical layout rules, the merge rule, and the dependency rule. Any change to the ruleset must be applied to both files.

---

## 12. Architectural Decisions

These are conscious design choices — not defaults or accidents. Understanding the *why* prevents future sessions from accidentally reversing them. CLAUDE.md lists each decision as a one-line summary for discoverability; the full **Decision**, **Why**, **Consequence**, and **Do not** text for every AD lives below.

---

### AD-1 · SonarCloud and Railway deploy are not merge-gate checks

**Decision:** Both run with `continue-on-error: true` in `ci.yml` and are excluded from the Manager Agent blocking check list. The only blocking CI jobs are the `test` matrix (Python 3.11 + 3.12) and the `bandit` security scan.

**Why:** SonarCloud is triggered selectively from the Control Centre before promoting a build to TEST or PROD — running it on every feature-branch PR would be redundant and costly. Railway deploy only runs after merge to `main`, so it can never be a pre-merge gate.

**Do not:** Add SonarCloud or Railway deploy as blocking conditions in `manager_agent.py`, `ci_manager_agent.py`, `GetCIStatusTool`, or any merge-readiness logic.

---

### AD-2 · No git CLI — all GitHub operations use the REST API

**Decision:** The Dev Agent creates branches, commits files, and opens PRs entirely via the GitHub Contents API and Git Trees API over HTTP. No `git` binary is required.

**Why:** Agents run in GitHub Actions runners and arbitrary Python environments. Eliminating the git dependency means agents work anywhere Python and `requests` are available. Base64 encoding handles binary-safe file content. The SHA-based update protocol replaces the need for local refs.

**Consequence:** File updates require the current blob SHA (fetched before writing). The `commit_file` tool handles this automatically via `get_file()` → SHA lookup before `PUT /contents/{path}`.

---

### AD-3 · Feature branches are always recreated from `main`, never updated in place

**Decision:** Before creating a branch, the Dev Agent deletes any existing branch with the same name and recreates it fresh from the latest `main` SHA.

**Why:** In-place branch updates accumulate divergence from `main` and produce complex diffs that are harder for the Manager Agent to review. Starting fresh from `main` on every invocation guarantees a clean, minimal diff and eliminates merge conflicts entirely.

**Consequence:** Any work committed to a branch that has not yet been merged to `main` will be lost if the Dev Agent retriggers for the same ticket. This is intentional — the branch is ephemeral; `main` is the source of truth.

---

### AD-4 · Two parallel agent implementations: CrewAI (local) and raw Anthropic SDK (CI)

**Decision:** The same three agents exist in two forms — CrewAI-wrapped versions in `agents/` (used locally via `main.py`) and self-contained single-file versions in `ci_dev_agent.py` / `ci_manager_agent.py` (used by GitHub Actions).

**Why:** CrewAI's full dependency graph is heavy and unsuitable for GitHub Actions runners. The CI versions use the Anthropic SDK directly with `tool_use` content blocks, keeping the runner lightweight. The local CrewAI versions provide a better development and debugging experience.

**Consequence:** Any logic change to review criteria, merge conditions, or file structure rules must be applied to **both** implementations. They are not shared-code — they are intentional duplicates kept in sync manually.

---

### AD-5 · Jira sprints are tracked via fix versions, not native Agile sprints

**Decision:** The PM Agent assigns tickets to sprints using Jira's `fixVersions` field (release management), not the native Agile sprint API. Sprint IDs are pre-created fix versions (e.g. Sprint 5 = version ID 10132).

**Why:** The Agile sprint API requires board-specific configuration and returns different data structures from the standard REST API. Fix versions are simpler to create and query programmatically and don't require board access.

**Consequence:** A dual JQL query is always needed to catch all tickets: `fixVersion = {fix_id} OR sprint = {native_id}`. Neither field alone is reliable. The PM Agent may create a new fix version instead of reusing an existing one if the name string doesn't match exactly — always pre-create sprint versions manually and verify before running the PM Agent.

---

### AD-6 · Manager Agent posts a COMMENT review, not a formal APPROVE

**Decision:** `ApprovePRTool` submits a `COMMENT`-type review body, not an `APPROVE`-type review event. The merge is called immediately after.

**Why:** GitHub blocks the same token from approving PRs it owns. The `GITHUB_TOKEN` (and the PAT used in CI) belongs to the repo owner, so a formal `APPROVE` review event is rejected with a 422. The workaround is posting an approval comment then calling the merge API directly.

**Consequence:** Merged PRs do not show a green "Approved" badge in the GitHub UI. This is expected — the approval is recorded as a comment. Do not interpret the absence of a formal approval as a process failure.

---

### AD-7 · Jira API calls are always proxied through the FastAPI backend

**Decision:** The Control Centre browser app never calls the Jira API directly. All Jira requests go through `/proxy/jira/*` endpoints on the UAT FastAPI backend.

**Why:** Jira's REST API does not set permissive CORS headers, so direct browser-to-Jira calls are blocked. The GitHub API does allow CORS, so the Control Centre calls GitHub directly. The Anthropic API key is a server secret and also never exposed to the browser.

**Do not:** Add direct Jira calls to the Control Centre frontend. The proxy pattern is load-bearing.

---

### AD-8 · Password reset token is returned in the API response (UAT mode, by design)

**Decision:** `POST /auth/password-reset/request` returns the reset token in the JSON response body, and the frontend displays it on screen.

**Why:** The UAT environment has no SMTP server configured. Returning the token directly lets testers exercise the reset flow without email infrastructure. This is UAT Finding #1 and is tracked as SDT1-50 for remediation before any TEST/PROD promotion.

**Do not:** Treat this as a normal security pattern or replicate it in any new endpoint. It exists only because SDT1-50 has not yet been implemented.

---

### AD-9 · Ticket execution order uses `customfield_10071`, not Jira dependency links

**Decision:** Each story has an integer execution order in `customfield_10071`. The Orchestrator sorts by this field. Jira `blocks`/`is-blocked-by` link types are not used.

**Why:** Resolving Jira link graphs requires recursive API calls and topological sorting — significantly more complex than sorting by a single integer field. The custom field is set by the PM Agent at sprint planning time and is sufficient for the linear execution sequences used so far.

**Consequence:** Dependency relationships are implicit in the ordering number, not machine-readable as links. SDT1-53 (Sprint 5) will add proper link support. Until then, the PM Agent must set `customfield_10071` correctly on every story.

---

### AD-10 · All agents are stateless — `memory=False` on every CrewAI agent

**Decision:** All three CrewAI agents (`pm_agent.py`, `dev_agent.py`, `manager_agent.py`) are instantiated with `memory=False`.

**Why:** Stateful CrewAI memory uses a vector store that adds latency, cost, and non-determinism. Each agent run is scoped to a single task (plan a sprint, implement a ticket, review a PR) and requires no cross-session context. The session context is provided explicitly via the task description.

---

### AD-11 · CrewAI requires an OpenAI API key even when using Anthropic — use a stub

**Decision:** `.env` sets `OPENAI_API_KEY=sk-no-openai-needed`. This is a dummy value.

**Why:** CrewAI's framework validates the presence of `OPENAI_API_KEY` at import time regardless of which LLM provider is configured. The agents use `claude-sonnet-4-5` via the `LLM(model=...)` constructor, so OpenAI is never actually called. The stub satisfies the framework check.

---

### AD-12 · PM Agent tool set is split into BACKLOG_TOOLS and SPRINT_TOOLS

**Decision:** The PM Agent's tools are divided into two groups. `BACKLOG_TOOLS` covers epic/story creation; `SPRINT_TOOLS` covers sprint population. The agent is instantiated with `BACKLOG_TOOLS` by default and the caller swaps to `SPRINT_TOOLS` for sprint-phase tasks.

**Why:** The combined tool schema of all PM tools exceeds a threshold that causes issues with Claude's tool-use context window. Splitting keeps each invocation's tool list small enough to function reliably.

**Consequence:** When invoking the PM Agent for sprint planning specifically, the `tools` override must be passed. Using the default `BACKLOG_TOOLS` for a sprint task will silently omit the sprint population tools.

---

### AD-13 · Manager Agent diff is truncated at 8 000 characters (CrewAI) / 12 000 characters (CI)

**Decision:** `GetPRDiffTool` in `manager_tools.py` truncates diffs at 8 000 chars. `ci_manager_agent.py` truncates at 12 000 chars. Both cut from the end of the diff.

**Why:** Large diffs exceed Claude's effective context for tool-use. Truncation prevents context overflow and keeps review latency predictable.

**Known weakness:** Truncation from the end means new files appended at the bottom of a PR diff are invisible to the Manager. SDT1-46 will fix this by reordering: new files first, modified hunks second, deletions last.

---

### AD-14 · Playwright E2E tests run against the live Railway-deployed UAT backend

**Decision:** E2E tests in `tests/e2e/` hit the actual production UAT URL (`https://synpro-virtual-dev-team-production.up.railway.app`), not a local or ephemeral test environment.

**Why:** Spinning up a full Docker stack in CI for every PR is expensive and slow. The UAT backend is always running on Railway and is the canonical test target. E2E test results reflect real deployment behaviour.

**Consequence:** E2E tests depend on Railway availability. If the UAT service is down or mid-deploy, E2E tests will fail for infrastructure reasons unrelated to the PR. This is why Playwright runs with `continue-on-error: true`.

---

### AD-15 · GitHub Actions use a PAT (`PAT_TOKEN`), not the default `GITHUB_TOKEN`

**Decision:** `auto-implement.yml` and `auto-review.yml` authenticate with a Personal Access Token stored as `PAT_TOKEN`, not the built-in `GITHUB_TOKEN`.

**Why:** The default `GITHUB_TOKEN` cannot push to branches protected by branch protection rules, and cannot trigger other workflow runs (a security restriction GitHub applies to prevent recursive workflow loops). The PAT bypasses both restrictions and must be rotated when the owner account credentials change.

---

### AD-16 · `uat/backend/` uses a flat module layout — no packages, no `src/` subdirectory

**Decision:** All Python source files sit directly in `uat/backend/`. No `src/` subdirectory, no `__init__.py` files. Imports are flat: `from models import ...`, not `from src.models import ...`.

**Why:** The backend is a small, focused FastAPI app. A package hierarchy would add indirection without benefit at this scale. The flat layout also matches how Railway's Procfile resolves modules at startup.

**Do not:** Create `src/` subdirectories or `__init__.py` files inside `uat/backend/`. The Dev Agent backstory and `ci_dev_agent.py` prompt both enforce this layout explicitly.

---

### AD-17 · Orchestrator re-queries Jira before each ticket — no startup cache

**Decision:** `run_sprint()` uses a `while True:` loop that calls `get_open_sprint_tickets()` at the top of every iteration, always processing `tickets[0]` (the lowest execution-order To Do ticket). The loop exits when Jira returns an empty list.

**Why:** Fetching once at startup and iterating a stale snapshot meant any external state change (manual Jira transition, failed retrigger, mid-run ticket completion) was invisible for the rest of the run. The while-loop model also makes automatic retry of failed tickets possible — if a ticket fails and remains To Do, the next iteration picks it up again without operator intervention.

**Consequence:** A ticket that genuinely cannot be implemented will loop indefinitely (fail → still To Do → retry). The Orchestrator does not implement a per-ticket retry cap. If a ticket is permanently broken, move it to Done or remove it from To Do in Jira to unblock the sprint.

---

### AD-18 · Manager Agent uses `PAT_TOKEN` (not `GITHUB_TOKEN`) for workflow dispatch retriggers

**Decision:** `ci_manager_agent.py` maintains two header dicts: `GH_HEADERS` (built-in `GITHUB_TOKEN`) for all read/write operations on PRs, commits, and reviews; and `DISPATCH_HEADERS` (PAT from `PAT_TOKEN` env var) exclusively for `workflow_dispatch` API calls. `auto-review.yml` exposes `PAT_TOKEN: ${{ secrets.PAT_TOKEN }}` to the script.

**Why:** GitHub's security model blocks `GITHUB_TOKEN` from triggering `workflow_dispatch` events on other workflows to prevent recursive loops. All retrigger calls (merge-conflict recovery → Auto Implement) silently returned 4xx when using `GITHUB_TOKEN` — tickets were left stranded with closed PRs and no new implementation. Confirmed failure on PR #98 (SDT1-46).

**Consequence:** Any new place in `ci_manager_agent.py` that needs to fire a workflow must use `DISPATCH_HEADERS`. If `PAT_TOKEN` is not set in the environment, it falls back to `GITHUB_TOKEN` (which will fail silently) — always verify the secret is present.

---

### AD-19 · `gh_read_file` in `ci_dev_agent.py` returns `None` for directory paths

**Decision:** `gh_read_file` checks `isinstance(data, list)` after `data = r.json()`. If the GitHub Contents API returns a directory listing (a JSON array), the function returns `None` — identical to how a 404 is handled.

**Why:** When Claude passes a directory path to `read_file`, the GitHub API returns a list of directory entries rather than a file dict. Accessing `data["content"]` on a list raises `TypeError: list indices must be integers or slices, not str`, crashing the entire Auto Implement run after files may have already been staged. Returning `None` lets the agent see "File not found" and try a different path.

**Do not:** Remove this guard or assume the GitHub Contents API always returns a dict.

---

### AD-20 · Manager Agent merge must use `PAT_TOKEN`, not `GITHUB_TOKEN`

**Decision:** `merge_pr()` in `ci_manager_agent.py` uses `DISPATCH_HEADERS` (`PAT_TOKEN`) for the `PUT /pulls/{pr_number}/merge` API call, not `GH_HEADERS` (`GITHUB_TOKEN`).

**Why:** GitHub does not fire `push` events for actions performed by `GITHUB_TOKEN` — this is the same recursive-loop prevention that blocks `GITHUB_TOKEN` from dispatching workflows (AD-15, AD-18). Every Manager Agent squash merge using `GITHUB_TOKEN` produced no push event on `main`, so `ci.yml` never ran and Railway never received a deploy trigger. All Sprint 5 merges (2026-04-30) produced zero CI runs on `main` as a result — the UAT backend ran stale code until the RAILWAY_TOKEN was manually rotated and a deploy manually triggered.

**Consequence:** `DISPATCH_HEADERS` is now used for three operations: workflow dispatch retriggers, the merge call, and any future write that must produce observable side effects on `main`. `GH_HEADERS` (`GITHUB_TOKEN`) is safe only for operations that do not need to trigger downstream workflows — PR reads, review comments, CI status checks.

**Do not:** Revert `merge_pr()` to `GH_HEADERS`. The CI and Railway deploy pipelines depend on the PAT-triggered push event.

---

### AD-21 · Railway deploy uses GraphQL API `serviceInstanceRedeploy`, not the CLI

**Decision:** The `ci.yml` deploy job calls the Railway GraphQL API (`https://backboard.railway.app/graphql/v2`) directly via `curl` + `jq` to trigger redeployments. It does not install the Railway CLI (`npm install -g @railway/cli`).

**How it works:**
1. `printf` constructs the GraphQL query JSON (avoids nested-shell-escape fragility)
2. `project(id: "$RAILWAY_PROJECT_ID")` returns all environments and services
3. `jq` with `ascii_downcase` resolves "production" environment ID and service ID by name (case-insensitive)
4. `serviceInstanceRedeploy(environmentId: ..., serviceId: ...)` mutation triggers the redeploy
5. If the API returns `{"errors":[...]}` or is unreachable, the step exits 0 (non-blocking) and logs all available environment/service names for debugging

**Why:** The Railway CLI (`railway up`) uses `railway.json` in the working directory and requires the correct service name at invocation time. The CLI also requires a project-scoped token and the service name must match exactly. The GraphQL API resolves service IDs dynamically by name, is dependency-free (no npm install), and is more transparent — the full response is echoed to CI logs.

**Secrets used:** `RAILWAY_TOKEN` (personal token in GitHub Secrets — must have project read+deploy access) and `RAILWAY_PROJECT_ID` (the project UUID).

**Do not:** Add `npm install -g @railway/cli` back to the deploy job. Use the GraphQL API pattern instead.

---

### AD-22 · `uat/backend/` is a self-contained service — no cross-directory imports at runtime

**Decision:** Every Python file in `uat/backend/` must import only from: the Python standard library, pip-installed packages in `uat/backend/requirements.txt`, and other files within `uat/backend/` itself. No imports from `agents/`, `tools/`, or any other top-level directory.

**Why:** Railway deploys `uat/backend/` as a standalone service. The working directory at startup is `uat/backend/`, and no other project directories are present on the filesystem. A `sys.path.insert` pointing to a parent directory works locally but resolves to a non-existent path in the Railway container. This caused at minimum two confirmed production crashes: `manager_agent_router.py` (Sprint 5) and `orchestrator_router.py` (Sprint 6).

**Consequence:** When a new router needs logic that currently lives in `agents/`, that logic must be inlined as local helper functions or rewritten as direct HTTP calls. Do not create shared library packages spanning `uat/backend/` and `agents/`.

**Pattern to follow:** See `manager_agent_router.py` and `orchestrator_router.py` (post-Sprint 6 fix) — both are fully self-contained with local helper functions and no cross-directory imports.

---

### AD-23 · One frontend per product — Control Centre IS the product frontend

**Decision:** The Control Centre and the UAT frontend are to be merged into a single frontend service per product. The Control Centre was always intended to be the product frontend — not a separate operator tool. The separate Virtual-Dev-Team-UAT-Frontend Railway service will be decommissioned in Sprint 12.

**Why:** Having two separate frontends for one product creates unnecessary duplication, split authentication, and confusion about which service is the real product. The Control Centre already contains the Sprint Status, Workflows, UAT Deploy, and PM Agent tabs — adding the user-facing pages (Login, Register, Dashboard, Profile, Notifications) makes it the complete product frontend.

**Consequence:** Sprint 12 will merge all UAT frontend pages into the Control Centre, decommission the UAT frontend Railway service, and update CORS and backend configuration accordingly.