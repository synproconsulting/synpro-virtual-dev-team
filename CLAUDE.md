# Virtual Dev Team — Project Context

> This file is the single source of truth for Claude Code and Claude chat sessions.
> Load it at the start of every session to restore full project context.

> Sprint history moved to CLAUDE_HISTORY.md

---

## What This Project Is

An AI-powered Virtual Development Team that automates the full software development lifecycle. Given a plain-English feature brief, the system plans a sprint in Jira, implements the code via AI agents, raises PRs, runs CI, reviews and merges — with a React Control Centre dashboard to monitor and control everything.

**Owner:** Johan Wessels — SynPro Consulting
**Started:** April 21, 2025
**Current state:** Sprints 1–7 complete and merged. Sprint 8 not yet planned.

---

## Live Deployments

| Service | URL |
|---|---|
| Control Centre (frontend) | https://control-centre-service-production.up.railway.app |
| UAT Backend (FastAPI) | https://synpro-virtual-dev-team-production.up.railway.app |
| UAT Frontend (React) | https://virtual-dev-team-uat-frontend-production.up.railway.app |

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

---

## Key Architectural Decisions

These are conscious design choices — not defaults or accidents. Understanding the *why* prevents future sessions from accidentally reversing them.

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
6. Opens PR: title format `[SDT1-XX] Summary` — Manager Agent parses the ticket key from this

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
| Sprint IDs (native) | Sprint 1: 35, Sprint 2: 69, Sprint 3: 70, Sprint 4: 71, Sprint 5: 72, Sprint 6: 105, Sprint 7: 138, Sprint 8: 171 |
| Sprint fix version IDs | Sprint 1: 10000, Sprint 2: 10033, Sprint 3: 10066, Sprint 4: 10099, Sprint 5: 10132, Sprint 6: 10198, Sprint 7: 10231, Sprint 8: 10264 |
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
- **PR title format:** `[SDT1-XX] Description` — Manager Agent parses ticket key from this
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
