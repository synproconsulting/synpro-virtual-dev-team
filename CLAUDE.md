# Virtual Dev Team — Project Context

> This file is the single source of truth for Claude Code and Claude chat sessions.
> Load it at the start of every session to restore full project context.

> Sprint history moved to CLAUDE_HISTORY.md

---

## What This Project Is

An AI-powered Virtual Development Team that automates the full software development lifecycle. Given a plain-English feature brief, the system plans a sprint in Jira, implements the code via AI agents, raises PRs, runs CI, reviews and merges — with a React Control Centre dashboard to monitor and control everything.

**Owner:** Johan Wessels — SynPro Consulting
**Started:** April 21, 2025
**Current state:** Sprints 1–14 complete and merged. Sprint 15 in progress.

---

## Live Deployments

| Service | URL |
|---|---|
| Control Centre (frontend) | https://control-centre-service-production.up.railway.app |
| UAT Backend (FastAPI) | https://synpro-virtual-dev-team-production.up.railway.app |

> Virtual-Dev-Team-UAT-Frontend Railway service decommissioned in Sprint 12 (AD-23). All frontend functionality merged into Control Centre.

---

## Hard Rules

> These rules are non-negotiable and apply to every session, every agent, and every change — no exceptions.

**Never commit directly to `main`.** All changes — including single-line fixes, cleanups, corrections, and documentation updates — must go through:
1. A `feature/` or `fix/` branch
2. A pull request
3. CI pipeline
4. Manager Agent review and merge

Committing directly to `main` bypasses the audit trail, CI gates, and the Manager Agent review that this system exists to enforce. If a fix is urgent enough to feel like it needs to skip the process, that urgency is reason to follow the process more carefully, not less. If a direct-to-main commit is ever made by mistake, a retroactive PR must be opened immediately (as was done for SDT1-49).

**SonarCloud and Railway deploy are not merge-gate checks — by design.** Both run with `continue-on-error: true` in `ci.yml` and are intentionally excluded from the Manager Agent's blocking check list. The Manager Agent must only gate on unit tests (Python 3.11 + 3.12) and the bandit security scan. SonarCloud analysis is triggered manually from the Control Centre on selected components before promoting a build to TEST or PROD. Never add SonarCloud or Railway deploy as blocking conditions in the Manager Agent, `ci_manager_agent.py`, or any tool that evaluates merge readiness.

**`uat/backend/requirements.txt` is a critical file.** Before writing it, always read the existing content first. Never remove any existing dependency — only append new ones. Removing a package breaks the deployed Railway service for every feature that depends on it. This rule applies to both the CrewAI Dev Agent (`DEV_AGENT_BACKSTORY`) and the CI Dev Agent (`SYSTEM_PROMPT`).

**`GITHUB_TOKEN` cannot trigger `workflow_dispatch` events — use `PAT_TOKEN`.** GitHub blocks the built-in `GITHUB_TOKEN` from dispatching workflows on other files (a security restriction against recursive loops). Any code that calls the `/actions/workflows/*/dispatches` API must use `PAT_TOKEN` (the same secret used by `auto-implement.yml`). This applies to `ci_manager_agent.py`'s merge-conflict retrigger and any future agent that needs to fire a workflow. Failures are not silent — check the HTTP response and post a PR comment if the dispatch fails.

**`FRONTEND_URL` in Railway must be `*` or explicitly include the Control Centre origin.** The UAT backend CORS middleware reads `FRONTEND_URL` from the environment. If it is set to the UAT frontend URL only, the Control Centre (`https://control-centre-service-production.up.railway.app`) is blocked — the browser gets no `Access-Control-Allow-Origin` header and all proxy calls fail silently. For UAT, set `FRONTEND_URL=*` in the Railway backend service variables. The code handles `*` correctly: `allow_origins=["*"]`.

**`uat/backend/` routers must never import from the `agents/` directory.** The `uat/backend/` service is a self-contained Railway deployment — the `agents/` directory does not exist on the Railway filesystem at runtime. Any `import` from `agents/` crashes the service at startup. This caused multiple production outages in Sprint 6 (`orchestrator_router.py`; same pattern as `manager_agent_router.py` in Sprint 5). Every router must be fully self-contained: inline the logic or replace it with direct HTTP calls. The `sys.path.insert` hack does not work in Railway — there is no parent directory to insert.

**Always read `auth.py` before creating any new router in `uat/backend/`.** The exact name of the auth dependency function must be verified before use — it has drifted between sessions. As of Sprint 6 the correct import is `from auth import get_current_user as require_auth`. Assuming the name without reading the file produces routers that crash at startup.

**Security hardening tickets must list required Railway environment variable changes in the acceptance criteria.** Hardening changes (JWT secret validation, CORS locking) are ineffective until the new variables are set in the Railway service dashboard. Acceptance criteria for any security ticket that touches environment config must include: variable name, required value format, and which Railway service to update.

**Never run two Claude Code instances simultaneously on this project.** Concurrent instances make overlapping API calls to GitHub, Jira, and Railway — producing race conditions, duplicate PRs, and split-brain Jira state.

**uto-implement.yml is manual-only — never dispatch it programmatically.** Claude Code is the Dev Agent for Sprint 8 and beyond. The uto-implement.yml workflow exists for reference and manual single-ticket testing from the GitHub Actions UI only. The orchestrator.py Orchestrator must not dispatch it automatically via the GitHub API. Implement tickets directly with Claude Code.

**Claude Code is the Dev Agent — do not invoke `agents/dev_agent.py` directly.** Claude Code implements all tickets directly via the GitHub Contents API. `agents/dev_agent.py` and `auto-implement.yml` exist for reference and manual single-ticket testing only. Never dispatch `auto-implement.yml` programmatically or run `agents/dev_agent.py` as part of a sprint.

**The rule-based auto-merger is the Manager Agent — do not invoke `agents/manager_agent.py` or `ci_manager_agent.py` directly.** Since Sprint 8 (SDT1-79, PR #167), PRs are merged automatically by the rule-based auto-merger in `ci.yml` when all blocking CI checks pass. `agents/manager_agent.py` and `ci_manager_agent.py` exist for reference only.

**Sprint setup is performed directly via Jira API calls from Claude Code — do not invoke the PM Agent for sprint planning or sprint setup.** `agents/pm_agent.py` exists for reference only. All sprint setup (fix version creation, native sprint creation, ticket assignment, execution order, story points, priority) is done via direct Jira REST API calls.

**When Claude Code flags a discrepancy at the end of its output, resolve it in the current action — never defer to a follow-up.** If a sprint setup prompt produces output noting a corrected ticket key, wrong ID, or any inconsistency in CLAUDE.md, CLAUDE_HISTORY.md, or PROJECT_CONTEXT.md, that correction must be included in the same PR before it is submitted. Specifically: if any ticket key in CLAUDE_HISTORY.md is provisional (e.g. "SDT1-111 (to be created)"), it must be resolved and corrected in the same PR that sets up the sprint IDs — not in a follow-up PR.

**Jira ticket lifecycle: transition to In Progress before starting implementation.** Leave In Progress when PR is opened. Transition to Done only when the PR is merged to `main` and confirmed by the auto-merger. Never transition to Done on PR open. Until the auto-merger is taught to update Jira (SDT1-125), the operator (or a follow-up Claude Code session triggered after merge) is responsible for the Done transition — opening the PR is not the trigger.

**Before opening any fix PR that corrects a bug discovered during the current sprint, create a Jira bug ticket first.** Assign it to the current sprint (fix version + native sprint). Reference the ticket key in the PR title using conventional commit format: `fix(SDT1-XX): description`. Transition to In Progress before starting, leave In Progress when PR opens, Done on merge. No fix PR may be opened without a corresponding Jira ticket.

---

## Key Architectural Decisions

These are conscious design choices — not defaults or accidents. Understanding the *why* prevents future sessions from accidentally reversing them. CLAUDE.md keeps each decision as a one-line summary for discoverability; the full **Decision**, **Why**, **Consequence**, and **Do not** text for every AD lives in **PROJECT_CONTEXT.md Section 12**.

### AD-1 · SonarCloud and Railway deploy are not merge-gate checks — see PROJECT_CONTEXT.md Section 12
SonarCloud and Railway deploy run with `continue-on-error: true` and are excluded from the Manager Agent's blocking check list — only the `test` matrix (Python 3.11 + 3.12) and the `bandit` scan are blocking.

### AD-2 · No git CLI — all GitHub operations use the REST API — see PROJECT_CONTEXT.md Section 12
The Dev Agent creates branches, commits files, and opens PRs entirely via the GitHub Contents API and Git Trees API over HTTP — no `git` binary required.

### AD-3 · Feature branches are always recreated from `main`, never updated in place — see PROJECT_CONTEXT.md Section 12
Before creating a branch, the Dev Agent deletes any existing branch with the same name and recreates it fresh from the latest `main` SHA, guaranteeing clean diffs.

### AD-4 · Two parallel agent implementations: CrewAI (local) and raw Anthropic SDK (CI) — see PROJECT_CONTEXT.md Section 12
The same three agents exist in two forms — CrewAI-wrapped (`agents/`) for local use and self-contained single-file versions (`ci_dev_agent.py` / `ci_manager_agent.py`) for CI; logic changes must be applied to both.

### AD-5 · Jira sprints are tracked via fix versions, not native Agile sprints — see PROJECT_CONTEXT.md Section 12
Sprints are assigned via Jira's `fixVersions` field, not the native Agile sprint API; JQL must dual-query `fixVersion = {fix_id} OR sprint = {native_id}` to catch all tickets.

### AD-6 · Manager Agent posts a COMMENT review, not a formal APPROVE — see PROJECT_CONTEXT.md Section 12
`ApprovePRTool` submits a `COMMENT`-type review and then calls merge directly — GitHub blocks a token from submitting a formal `APPROVE` review on PRs it owns.

### AD-7 · Jira API calls are always proxied through the FastAPI backend — see PROJECT_CONTEXT.md Section 12
The Control Centre browser app never calls Jira directly — all Jira requests go through `/proxy/jira/*` on the UAT backend because Jira does not allow browser CORS.

### AD-8 · Password reset token is returned in the API response (UAT mode, by design) — see PROJECT_CONTEXT.md Section 12
`POST /auth/password-reset/request` returns the reset token in the response body and the UI displays it — UAT-only workaround for the missing SMTP server, tracked as SDT1-50.

### AD-9 · Ticket execution order uses `customfield_10071`, not Jira dependency links — see PROJECT_CONTEXT.md Section 12
Each story has an integer execution order in `customfield_10071`; the Orchestrator sorts by this field and Jira `blocks` / `is-blocked-by` link types are not used.

### AD-10 · All agents are stateless — `memory=False` on every CrewAI agent — see PROJECT_CONTEXT.md Section 12
Every CrewAI agent is instantiated with `memory=False`; context is passed explicitly via the task description rather than via the vector store.

### AD-11 · CrewAI requires an OpenAI API key even when using Anthropic — use a stub — see PROJECT_CONTEXT.md Section 12
`.env` must set `OPENAI_API_KEY=sk-no-openai-needed` to satisfy CrewAI's import-time check — the agents use `claude-sonnet-4-5` and OpenAI is never actually called.

### AD-12 · PM Agent tool set is split into BACKLOG_TOOLS and SPRINT_TOOLS — see PROJECT_CONTEXT.md Section 12
PM Agent tools are divided into `BACKLOG_TOOLS` (epic/story creation, default) and `SPRINT_TOOLS` (sprint population) — sprint-phase invocations must pass the `tools` override.

### AD-13 · Manager Agent diff is truncated at 8 000 characters (CrewAI) / 12 000 characters (CI) — see PROJECT_CONTEXT.md Section 12
PR diffs are truncated from the end at 8 000 chars (CrewAI) / 12 000 chars (CI) to stay within Claude's effective tool-use context.

### AD-14 · Playwright E2E tests run against the live Railway-deployed UAT backend — see PROJECT_CONTEXT.md Section 12
E2E tests hit the live UAT URL on Railway, not a local stack — Playwright runs with `continue-on-error: true` because results depend on Railway availability.

### AD-15 · GitHub Actions use a PAT (`PAT_TOKEN`), not the default `GITHUB_TOKEN` — see PROJECT_CONTEXT.md Section 12
`auto-implement.yml` and `auto-review.yml` authenticate with `PAT_TOKEN` because the default `GITHUB_TOKEN` cannot push to protected branches or trigger other workflows.

### AD-16 · `uat/backend/` uses a flat module layout — no packages, no `src/` subdirectory — see PROJECT_CONTEXT.md Section 12
All Python source files sit directly in `uat/backend/` with no `src/` subdirectory and no `__init__.py`; imports are flat (`from models import ...`).

### AD-17 · Orchestrator re-queries Jira before each ticket — no startup cache — see PROJECT_CONTEXT.md Section 12
`run_sprint()` re-queries Jira at the top of every iteration and always processes `tickets[0]` — failed-but-still-To-Do tickets are automatically retried, but permanently broken tickets can loop indefinitely.

### AD-18 · Manager Agent uses `PAT_TOKEN` (not `GITHUB_TOKEN`) for workflow dispatch retriggers — see PROJECT_CONTEXT.md Section 12
`ci_manager_agent.py` uses `DISPATCH_HEADERS` (PAT) exclusively for `workflow_dispatch` calls; `GITHUB_TOKEN` cannot fire workflow_dispatch events on other workflows.

### AD-19 · `gh_read_file` in `ci_dev_agent.py` returns `None` for directory paths — see PROJECT_CONTEXT.md Section 12
`gh_read_file` checks `isinstance(data, list)` after parsing — when the Contents API returns a directory listing it returns `None` (same as 404), avoiding a `TypeError` crash.

### AD-20 · Manager Agent merge must use `PAT_TOKEN`, not `GITHUB_TOKEN` — see PROJECT_CONTEXT.md Section 12
`merge_pr()` uses `DISPATCH_HEADERS` (PAT) because GitHub does not fire `push` events for `GITHUB_TOKEN` merges, which would block `ci.yml` and Railway deploy from running on `main`.

### AD-21 · Railway deploy uses GraphQL API `serviceInstanceRedeploy`, not the CLI — see PROJECT_CONTEXT.md Section 12
`ci.yml` calls the Railway GraphQL API directly via `curl` + `jq` and the `serviceInstanceRedeploy` mutation — no `npm install -g @railway/cli` required.

### AD-22 · `uat/backend/` is a self-contained service — no cross-directory imports at runtime — see PROJECT_CONTEXT.md Section 12
Files in `uat/backend/` may import only from stdlib, pip-installed packages in `uat/backend/requirements.txt`, and other files within `uat/backend/` itself — never from `agents/` or `tools/`.

### AD-23 · One frontend per product — Control Centre IS the product frontend — see PROJECT_CONTEXT.md Section 12
The Control Centre is the single product frontend; the separate Virtual-Dev-Team-UAT-Frontend Railway service was decommissioned in Sprint 12.

---

## Repository

- **GitHub org:** `synproconsulting`
- **Repo:** `synpro-virtual-dev-team` (public)
- **Default branch:** `main`
- **Branch naming:** `feature/sdt1-{ticket}-{slug}` (e.g. `feature/sdt1-31-sprint-status-dashboard`), `fix/sdt1-{ticket}-{slug}` for corrections

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI agents | CrewAI framework + Anthropic claude-sonnet-4-5 |
| Backend (UAT app) | FastAPI (Python) |
| Frontend (UAT app) | React + Vite |
| Control Centre | React + Vite (separate service) |
| Database | PostgreSQL (Railway managed) |
| Hosting | Railway (all services) |
| Task tracking | Jira Cloud — `synproconsulting.atlassian.net`, project key `SDT1` |
| Source control | GitHub — `synproconsulting/synpro-virtual-dev-team` |
| CI/CD | GitHub Actions |
| Code quality | SonarCloud |
| E2E testing | Playwright (runs against live UAT backend) |

---

## Project Structure

```
virtual-dev-team/
├── agents/
│   ├── pm_agent.py          # PM Agent — CrewAI, plans sprints, writes to Jira
│   ├── dev_agent.py         # Dev Agent — implements tickets, commits, opens PRs
│   └── manager_agent.py     # Manager Agent — reviews PRs, merges, closes tickets
├── tools/
│   ├── pm_tools.py          # Jira tools for PM Agent (create epic, story, sprint)
│   ├── dev_tools.py         # GitHub tools for Dev Agent (branch, commit, PR)
│   ├── manager_tools.py     # GitHub/Jira tools for Manager Agent
│   ├── github_client.py     # Shared GitHub API client
│   └── jira_client.py       # Shared Jira API client
├── uat/
│   ├── backend/
│   │   └── main.py          # FastAPI app — auth, profile, notifications + Jira/GitHub proxy
│   └── frontend/
│       └── src/             # React UAT frontend (pages: Login, Register, Dashboard, Reset)
├── workflows/               # GitHub Actions workflow YAMLs (local copy)
│   ├── ci.yml               # CI pipeline (test, security, sonar, playwright, deploy)
│   ├── auto-review.yml      # Manager Agent auto-review trigger
│   └── auto-implement.yml   # Dev Agent auto-implement trigger
├── tests/
│   └── e2e/
│       └── test_auth_e2e.py # Playwright E2E tests against live UAT backend
├── main.py                  # CLI entry point
├── orchestrator.py          # Orchestrator — sequences agents, manages sprint flow
├── ci_dev_agent.py          # CI-mode Dev Agent (used by GitHub Actions)
├── ci_manager_agent.py      # CI-mode Manager Agent (used by GitHub Actions)
└── .env                     # Local secrets (never committed)
```

> **Note:** The `control-centre/` source lives in the GitHub repo (`synproconsulting/synpro-virtual-dev-team`) and is deployed to Railway — it is not present in this local working directory. Ad-hoc maintenance scripts (`fix_*.py`, `check_*.py`, `push_*.py`) have accumulated at the root from prior sprints.

> **uat/backend/ layout:** This directory uses a **flat** layout — all Python source files sit directly in `uat/backend/` with no `src/` subdirectory and no `__init__.py` package files. Tests go in `uat/backend/tests/`. Imports inside `uat/backend/` are flat (e.g. `from models import ...`, not `from src.models import ...`). The Dev Agent must follow this layout when implementing backend tickets.

---

## The Four AI Agents

### 1. PM Agent (`agents/pm_agent.py`)
**Role:** AI Product Manager
**Framework:** CrewAI + claude-sonnet-4-5
**Invocation:**
```bash
python main.py --agent pm --task plan --brief "Build a notification system..."
```
**What it produces in Jira:**
- One Epic linking all stories
- Stories with: summary, description, acceptance criteria (ADF format), story points (1/2/3/5/8/13), priority (Highest→Lowest), execution order (`customfield_10071`)
- Story point max: 8 — stories over 8 get a FLAGGED Jira comment
- Sprint assignment via `fixVersions`

**Current limitations:**
- Chat history is React state only — lost on page refresh
- `Generate Sprint Plan` button in Control Centre generates JSON but doesn't push to Jira from UI
- No `blocks`/`is blocked by` Jira link types (only `customfield_10071` for execution order)
- No multi-product targeting

---

### 2. Dev Agent (`agents/dev_agent.py`)
**Role:** AI Developer — implements one ticket at a time
**Invocation:**
```bash
python main.py --agent dev --task implement --ticket SDT1-31 --summary "Sprint status dashboard"
```
**How it creates branches and PRs (GitHub Contents API — no git CLI):**
1. Gets latest `main` SHA
2. Deletes existing feature branch if present (prevents merge conflicts)
3. Creates fresh branch: `feature/sdt1-{ticket}-{slug}`
4. Commits files individually via `PUT /contents/{path}` with base64 encoding
5. For multi-file commits: uses Git Trees API (single commit, clean history)
6. Opens PR: title format `feat(SDT1-XX): summary` or `fix(SDT1-XX): summary` (conventional commits) — Manager Agent parses the ticket key from the `(SDT1-XX)` group

**Key design decisions:**
- Always branches from latest `main` — eliminates merge conflicts
- Pure HTTP via GitHub Contents API — no git installation needed
- SHA required for file updates — always checks existing SHA first

---

### 3. Manager Agent (`agents/manager_agent.py` / `ci_manager_agent.py`)
**Role:** AI Dev Manager — reviews PRs, enforces quality, merges
**Invocation:** Auto-triggered by GitHub Actions on every push, or manually:
```bash
python main.py --agent manager --task review --pr 71
```
**Review decision logic:**
- Waits for all CI checks to complete
- Checks PR mergeable state (rejects if merge conflicts)
- Asks Claude to review diff — APPROVE or REQUEST_CHANGES
- Merges on APPROVE, posts detailed feedback on REQUEST_CHANGES
- On merge: transitions Jira ticket to Done, posts PR reference comment
- Never rejects for SonarCloud being skipped (non-blocking by design)

---

### 4. Orchestrator (`orchestrator.py`)
**Role:** Sprint runner — sequences Dev Agent across all sprint tickets
**Invocation:**
```bash
python main.py --agent sprint
python main.py --agent sprint --dry-run   # prints ticket table, starts nothing
```

#### Ticket fetching (`get_open_sprint_tickets`)
- Calls `jira.list_all_issues(max_results=100)`, filters for `status == "To Do"`, drops `Epic`, `Sub-task`, `Subtask` issue types.
- Reads `customfield_10071` as the execution order integer. If the field is absent or null, defaults to `999`.
- Sorts by execution order ascending. For any ticket whose value is `999`, a hardcoded fallback list (`EXECUTION_ORDER`) provides secondary ordering — currently seeded with Sprint 4 ticket keys. Sprint 5+ tickets without `customfield_10071` set will pile at the end.

#### Per-ticket pipeline (`process_ticket`) — always serial, one ticket at a time
Each ticket runs through five steps in sequence before the next ticket starts:

| Step | What happens | Timeout |
|---|---|---|
| 1 | Trigger `auto-implement.yml` workflow dispatch | immediate (204 = success) |
| 2 | Poll for an open PR matching the ticket key in branch name or title | 5 min (30 × 10 s) |
| 3 | Poll PR head SHA check-runs until all complete | 30 min (180 × 10 s) |
| 4 | Trigger `auto-review.yml` workflow dispatch with `pr_number` | immediate |
| 5 | Poll until PR is merged or closed | 10 min (60 × 10 s) |

CI check exclusions (step 3): `"Manager Agent review"` and `"wait-and-review"` runs are filtered out before evaluating pass/fail — these are the review workflow's own jobs, not CI gates.

**Failure behaviour:**
- Step 2 timeout → returns `"failed"`, moves to next ticket.
- Step 3 CI failure → returns `"ci_failed"`, moves to next ticket immediately.
- Step 3 CI timeout → logs a warning and continues to step 4 anyway (does not block).
- Step 5 timeout → returns `"merge_timeout"`, **halts the sprint with `sys.exit(1)`**. Dependent tickets are not started. The operator must resolve the PR on GitHub, confirm the merge, then re-run the sprint. Already-merged tickets are safe to skip on re-run (their Jira status is Done, so they are not fetched as To Do).
- 5-second sleep between tickets on success or non-halt failures.

#### What is NOT implemented (as of Sprint 6)
- **Epic grouping:** no logic groups tickets by epic. Serial order is flat across the entire sprint.
- **Parallel execution:** `run_sprint()` accepts a `max_agents` parameter (default 1) that is never read or acted on inside the function. It is a dead parameter — a placeholder for future parallel support. All execution is strictly one ticket at a time.
- **Independent-epic detection:** no file-overlap analysis, no dependency graph traversal.

#### Execution order field requirement
Every sprint story **must** have `customfield_10071` set by the PM Agent at planning time. Stories without it receive order `999` and sort unpredictably behind all explicitly-ordered tickets. The fallback `EXECUTION_ORDER` list in the source is hardcoded for Sprint 4 and provides no guarantee for future sprints.

---

## Jira Configuration

| Setting | Value |
|---|---|
| Site | `synproconsulting.atlassian.net` |
| Project key | `SDT1` |
| Sprint IDs (native) | Sprint 1: 35, Sprint 2: 69, Sprint 3: 70, Sprint 4: 71, Sprint 5: 72, Sprint 6: 105, Sprint 7: 138, Sprint 8: 171, Sprint 9: 204, Sprint 10: 237, Sprint 11: 270, Sprint 12: 303, Sprint 13: 336, Sprint 14: 369, Sprint 15: 402 |
| Sprint fix version IDs | Sprint 1: 10000, Sprint 2: 10033, Sprint 3: 10066, Sprint 4: 10099, Sprint 5: 10132, Sprint 6: 10198, Sprint 7: 10231, Sprint 8: 10264, Sprint 9: 10297, Sprint 10: 10330, Sprint 11: 10363, Sprint 12: 10396, Sprint 13: 10429, Sprint 14: 10462, Sprint 15: 10495 |
| Execution order field | `customfield_10071` |
| Story points field | `customfield_10016` |

**Sprint query pattern** (backend uses dual query to catch all tickets):
```python
jql = f"project = SDT1 AND (fixVersion = {fix_id} OR sprint = {native_id})"
```

---

## GitHub Actions CI Pipeline

Triggered on every push to `feature/*` branches:

| Stage | What it does | Blocking? |
|---|---|---|
| Matrix test | pytest on Python 3.11 + 3.12 in parallel | Yes |
| Security scan | bandit on `src/` | No (--exit-zero) |
| SonarCloud | Full code analysis | No (continue-on-error) |
| Quality gate | SonarCloud gate result | No |
| Playwright E2E | Browser tests against live UAT backend | Yes |
| Deploy | Railway GraphQL API redeploy (main branch only, via `serviceInstanceRedeploy` mutation) | No |

---

## Control Centre — Tabs and Status

| Tab | Status | Notes |
|---|---|---|
| Overview | ✅ Redesigned | Sprint 6 (SDT1-59, PR #147) |
| Sprint Status | ✅ Working | Sprint selector, metrics, per-ticket PR refs, CI runs |
| Workflows | ✅ Working | GitHub Actions monitor, auto-refreshes every 30s |
| UAT Deploy | ✅ Working | Wired to Railway GraphQL API (SDT1-58, PR #125) |
| SonarCloud | ✅ Working | Results view added (SDT1-61, PR #135) |
| PM Agent | ⚠️ Partial | Chat works, history not persisted, approve not wired to Jira |

**Architecture:**
```
Browser → GitHub API        (direct — CORS allowed)
Browser → FastAPI backend   (proxy — avoids Jira CORS restriction)
Browser → Anthropic API     (via backend — API key never in browser)
```

---

## UAT Application (What the Agents Build)

A user authentication and profile management system:
- User registration with email/password validation
- JWT session management
- Login/logout
- Profile management
- Password reset (**bug:** currently shows token on screen instead of emailing — UAT Finding #1)
- Notification system
- Delete account

### Backend Dependencies (`uat/backend/requirements.txt`)

Verified complete package list as of Sprint 5 completion (audited against all imports in `uat/backend/*.py`):

| Package | Version | Used by |
|---|---|---|
| `fastapi` | 0.104.1 | main, auth, middleware, notifications, pm_agent, profile, proxy |
| `uvicorn` | 0.24.0 | Runtime server |
| `sqlalchemy` | 2.0.23 | database, models, repository |
| `pydantic` | 2.5.0 | auth, config, pm_agent, schemas |
| `psycopg2-binary` | 2.9.9 | auth (imported as `psycopg2`) |
| `pyjwt` | 2.8.0 | auth (imported as `jwt`) |
| `python-dotenv` | 1.0.0 | Runtime env loading |
| `slowapi` | 0.1.9 | main, rate_limiter |
| `httpx` | 0.27.0 | proxy (async HTTP client) |
| `anthropic` | 0.49.0 | pm_agent (PM Agent chat/sprint endpoints) |
| `pytest` | 7.4.3 | Test suite |

**Dev Agent rule:** Before modifying `uat/backend/requirements.txt`, always read the existing file first. Never remove any package from this list — only append new ones. Removing a dependency breaks the deployed Railway service for every feature that depends on it.

---

## Environment Variables (.env)

```
JIRA_BASE_URL=https://synproconsulting.atlassian.net
JIRA_EMAIL=johan.wessels@synproconsulting.co
JIRA_API_TOKEN=<rotate at id.atlassian.com>
JIRA_PROJECT_KEY=SDT1
ANTHROPIC_API_KEY=<from console.anthropic.com>
GITHUB_TOKEN=<from github.com/settings/tokens — needs repo scope>
RAILWAY_TOKEN=<from Railway account settings>
RAILWAY_PROJECT_ID=<UUID from Railway project settings>
```

GitHub Secrets (for Actions): `RAILWAY_TOKEN`, `RAILWAY_PROJECT_ID`, `SONAR_TOKEN`

---

## Local Development

```bash
# Activate venv (Windows)
cd "C:\Johan\SynPro Consulting\Virtual Dev Team\virtual-dev-team"
.venv\Scripts\activate

# Test connections
python test_connection.py

# Run PM Agent
python main.py --agent pm --task plan --brief "Your brief here"

# Run Dev Agent on a ticket
python main.py --agent dev --task implement --ticket SDT1-XX --summary "Summary"

# Run Manager Agent on a PR
python main.py --agent manager --task review --pr 71

# Run full sprint
python main.py --agent sprint
```

---

## Key Conventions

- **Commit format:** `feat(sdt1-XX): description` (conventional commits)
- **PR title format:** `feat(SDT1-XX): description` or `fix(SDT1-XX): description` (conventional commits) — Manager Agent parses ticket key from the `(SDT1-XX)` group. The older `[SDT1-XX] Description` bracket form is still accepted by the parser for legacy PRs but is no longer the convention.
- **Story points:** Fibonacci — 1, 2, 3, 5, 8, 13 (max 8 per story)
- **Execution order:** `customfield_10071` in Jira — Orchestrator sorts by this
- **ADF:** Acceptance criteria written in Atlassian Document Format in Jira descriptions
- **CORS:** Jira calls always go via FastAPI proxy — never direct from browser

---

## Known Issues / Technical Debt

- SonarCloud non-blocking by design (future sprint will add gate before TEST/PROD)
- PM Agent sprint creation may create a new fix version instead of reusing an existing one — pre-create the version and manually reassign if needed (happened during Sprint 5 and Sprint 6 setup)
- `orchestrator_router.py` `/api/orchestrator/start` creates state and returns immediately — background execution is not yet wired. Acts as a state-creation stub until a background task runner is added.

---

## Tools Available (Sprint 5 onwards)

- **Claude Code** — installed, no more manual script runs or file copying needed
- **Atlassian Rovo MCP** — available to connect for direct Jira management from Claude chat

