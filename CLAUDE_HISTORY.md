# Virtual Dev Team — Sprint History

> Moved from CLAUDE.md to reduce file size. Contains completed sprint records,
> fix PRs, infrastructure post-mortems, and lessons learned.

---

## Sprint History

### Sprint 1 — Auth Module
Tickets SDT1-1 through ~SDT1-10. User registration, login, JWT, password reset, profile basics.

### Sprint 2 — User Profile Module
Tickets SDT1-11 through ~SDT1-20. Profile page UI/UX, profile update endpoints, delete account.

### Sprint 3 — Notification System
Tickets SDT1-21 through ~SDT1-30. Email notifications, in-app notifications, notification preferences.
Note: SDT1-26 had a long conflict/retrigger loop — resolved via PR #71, Jira closed.

### Sprint 4 — Control Centre Dashboard
Tickets SDT1-31 through ~SDT1-40. Full Control Centre build: Sprint Status tab, Workflows tab, CI/CD monitoring, PM Agent chat UI, SonarCloud tab stub, UAT Deploy tab stub.

### Sprint 5 — Foundations ✅ Complete
Tickets SDT1-44 through SDT1-53. All 10 stories, 37 story points, merged to main.

| Exec # | Ticket | Summary | Status |
|--------|--------|---------|--------|
| 1 | SDT1-48 | Add Alembic migration framework with initial schema changes | ✅ Done |
| 2 | SDT1-49 | Add conversations and messages schema for PM Agent chat history | ✅ Done |
| 3 | SDT1-51 | Add products table for multi-product configuration | ✅ Done |
| 4 | SDT1-47 | Split main.py into separate router modules | ✅ Done |
| 5 | SDT1-50 | Fix password reset flow — send token via email only | ✅ Done (PR #96) |
| 6 | SDT1-45 | Add request logging middleware and rate limiting | ✅ Done (PR #88) |
| 7 | SDT1-44 | Add exponential backoff retry to Manager Agent Jira transitions | ✅ Done |
| 8 | SDT1-46 | Improve Manager Agent diff truncation to prioritise new files | ✅ Done (PR #103) |
| 9 | SDT1-52 | Add resume capability to Orchestrator with state persistence | ✅ Done |
| 10 | SDT1-53 | Extend PM Agent to write Jira blocks/is-blocked-by link types | ✅ Done (PR #100) |

**Fix PRs opened during Sprint 5 (infrastructure, not sprint tickets):**

| PR | Branch | What it fixed |
|----|--------|---------------|
| #89 | fix/pm-agent-execution-order | `execution_order` missing from `CreateStoryInput` schema; no backstory rule — caused all Sprint 5 tickets to have no execution order |
| #90 | fix/backend-add-httpx-requirement | `httpx` missing from `uat/backend/requirements.txt` — Railway deploy failing |
| #91 | fix/agent-prompts-requirements-txt-rule | requirements.txt critical-file rule added to both Dev Agent prompts |
| #92 | fix/backend-add-anthropic-requirement | `anthropic` missing from `uat/backend/requirements.txt` |
| #93 | fix/claude-md-document-backend-requirements | CLAUDE.md: document verified requirements.txt package list |
| #94 | fix/backend-health-endpoint | Add `GET /health` endpoint to UAT backend |
| #95 | fix/ci-dev-agent-read-file-directory | `gh_read_file` crashed on directory paths — TypeError crashing Auto Implement runs |
| #101 | fix/manager-agent-retrigger-and-comment | Manager Agent retrigger used GITHUB_TOKEN (blocked); no PR comment on conflict close |
| #102 | fix/orchestrator-re-query-jira-per-ticket | Orchestrator used stale ticket snapshot; switch to while-loop with Jira re-query per iteration |

> **Sprint 5 setup note:** During sprint creation the PM Agent created a spurious "Sprint 6 - Foundations" version (ID 10165) instead of reusing the pre-created Sprint 5 (ID 10132). The erroneous version was deleted and all stories were manually reassigned to fix version 10132. `customfield_10071` was also not set by the PM Agent (bug fixed in PR #89) and had to be set manually before the Orchestrator could run.

---

## Post-Sprint 5 Infrastructure Fixes

Infrastructure bugs discovered and fixed during Railway deployment investigation after Sprint 5 completed:

| PR | Branch | What it fixed |
|----|--------|---------------|
| #106 | fix/manager-agent-merge-pat-token | `merge_pr()` was using `GITHUB_TOKEN` — GitHub suppresses push events for GITHUB_TOKEN merges, so CI and Railway deploy never fired after any Manager Agent merge |
| #108 | fix/backend-manager-agent-router-rename | Renamed `manager_agent.py` → `manager_agent_router.py` in `uat/backend/` to avoid name collision with root-level `agents/manager_agent.py` |
| #109 | fix/backend-manager-agent-router-self-contained | Rewrote `manager_agent_router.py` as self-contained — original imported from `agents/manager_agent.py` via `sys.path.insert` hack, but `agents/manager_agent.py` is the CrewAI PR-reviewer and doesn't define those symbols; backend crashed at startup |
| #110 | fix/ci-railway-service-names | `railway up --service backend/frontend` used wrong service names; corrected to `synpro-virtual-dev-team` and `Virtual-Dev-Team-UAT-Frontend` |
| #111 | fix/ci-railway-api-deploy | Replaced Railway CLI deploy with GraphQL API `serviceInstanceRedeploy` mutation — removes npm install step, uses `RAILWAY_TOKEN` + `RAILWAY_PROJECT_ID` |
| #112 | fix/ci-railway-graphql-query | Fixed four issues in PR #111's GraphQL steps: `printf` for JSON construction, `ascii_downcase` for case-insensitive env name, echo full response for debug, grep for `"errors"` key in response |

**Root cause chain:** Sprint 5 merges used `GITHUB_TOKEN` → no push events on `main` → CI never ran → Railway never deployed → UAT backend ran stale code with broken imports (`manager_agent_router.py` crashing on startup) and wrong CORS config blocking the Control Centre.

---

### Sprint 6 — Control Centre Completion & Operational Hardening ✅ Complete
Epic SDT1-55. 15 stories, 48 story points. Fix version 10198, native sprint ID 105.

| Exec # | Ticket | Summary | Status | PR |
|--------|--------|---------|--------|----|
| 1 | SDT1-57 | PM Agent — CreateOrGetFixVersionTool with deterministic fix version ID | ✅ Done | #114 |
| 2 | SDT1-56 | Harden CORS FRONTEND_URL configuration | ✅ Done | #151 |
| 3 | SDT1-63 | Harden JWT secret key handling | ✅ Done | #117 |
| 4 | SDT1-62 | Remove password reset token from API response body | ✅ Done | #118 |
| 5 | SDT1-64 | Extend Orchestrator CI wait timeout from 15 to 30 minutes | ✅ Done | #150 |
| 6 | SDT1-58 | UAT Deploy tab — wire to Railway GraphQL API | ✅ Done | #125 |
| 7 | SDT1-60 | Cap Manager Agent retrigger loop to prevent infinite cycles | ✅ Done | #128 |
| 8 | SDT1-65 | PM Agent validation — warn on missing execution_order | ✅ Done | #149 |
| 9 | SDT1-66 | Orchestrator state persistence — resume after crash | ✅ Done | #148 |
| 10 | SDT1-59 | Overview tab redesign | ✅ Done | #147 |
| 11 | SDT1-61 | SonarCloud tab — add results view | ✅ Done | #135 |
| 12 | SDT1-67 | Railway GraphQL deploy — add validation and alerting in CI | ✅ Done | #136 |
| 13 | SDT1-70 | Token rotation runbook | ✅ Done | #146 |
| 14 | SDT1-69 | Add unit tests for manager_agent_router.py | ✅ Done | #139 |
| 15 | SDT1-68 | Add integration test for /api/railway/redeploy endpoint | ✅ Done | #142 |

**Backlog epic also created (not Sprint 6):** SDT1-71 — Sprint Lifecycle Management (3 stories: SDT1-72, SDT1-73, SDT1-74 / 11 pts). No sprint assignment — planned for a future sprint.

> **Sprint 6 setup notes:**
> - Fix version 10198 ("Sprint 6") was created manually — the spurious ID 10165 (deleted during Sprint 5) was not reused; Jira assigned 10198 as the next available ID.
> - Native sprint ID 105 ("SDT1 Sprint 6") already existed in Jira (state: future) — no creation needed.
> - PM Agent ran in two separate epic passes (`run_sprint6_epic1.py` / `run_sprint6_epic2.py`) to prevent stories from being mixed across epics.
> - All 15 Sprint 6 stories have `customfield_10071` set (no manual correction needed — brief included explicit execution_order values).
> - `main.py` updated: `run_pm_plan_backlog_only()` added for epics with no sprint assignment; Phase 1 story count constraint changed from "4–6 stories" to "ALL stories in the brief".

---

## Sprint 6 Fix PRs (infrastructure, not sprint tickets)

| PR | Branch | What it fixed |
|----|--------|---------------|
| #144 | fix/backend-orchestrator-router-import | `require_auth` → `get_current_user as require_auth` in orchestrator_router (superseded by #145) |
| #145 | fix/backend-orchestrator-router-self-contained | Removed `agents/` imports from `orchestrator_router.py` — caused Railway startup crash |

---

### Sprint 7 — Sprint Lifecycle Management ✅ Complete
Epic SDT1-71. 3 stories, 11 story points. Fix version 10231, native sprint ID 138.

| Exec # | Ticket | Summary | Status | PR |
|--------|--------|---------|--------|----|
| 1 | SDT1-73 | PM Agent starts Jira sprint on approval | ✅ Done | #154 |
| 2 | SDT1-74 | Control Centre shows current sprint status | ✅ Done | #160 |
| 3 | SDT1-72 | Control Centre Complete Sprint button | ✅ Done | #162 |

**Fix PRs opened during Sprint 7 (infrastructure, not sprint tickets):**

| PR | Branch | What it fixed |
|----|--------|---------------|
| #155 | fix/ci-dev-agent-create-pr-guard | Guard against multiple `create_pr` calls in `ci_dev_agent.py` |
| #156 | fix/auto-review-concurrency-guard | Add concurrency guard to `auto-review.yml` to prevent overlapping review runs |
| #157 | fix/remove-sonarcloud-from-ci | Remove SonarCloud from CI pipeline |
| #159 | fix/split-claude-md | Split `CLAUDE.md` to reduce file size (sprint history moved to `CLAUDE_HISTORY.md`) |
| #161 | fix/document-ci-dev-agent-system-prompt | Document `ci_dev_agent` system prompt rules in `PROJECT_CONTEXT.md` |

---

## Sprint 6 Lessons Learned

### 1. `uat/backend/` self-containment is a recurring blind spot
`orchestrator_router.py` was generated with `sys.path.insert` to import from `agents/` — the exact same mistake as `manager_agent_router.py` in Sprint 5. Added as a Hard Rule and as AD-22. The fix pattern is always: inline the logic as local helpers.

### 2. Auth function name drift causes silent router failures
The auth dependency was called `require_auth` in the Dev Agent's mental model but `get_current_user` in the actual `auth.py`. Routers compiled without error but crashed with 500 on every authenticated endpoint. The new Hard Rule requires reading `auth.py` before writing any router.

### 3. Test isolation must be explicit for environment-variable-gated tests
`test_init_without_token` passed locally (`RAILWAY_API_TOKEN` not set) but failed in CI (it is a GitHub secret exposed to the runner). Fix: `monkeypatch.delenv("RAILWAY_API_TOKEN", raising=False)`. Always explicitly clear env vars that tests assert are absent.

### 4. Multiple retriggers per ticket are normal but expensive
Many Sprint 6 tickets required 2–3 Auto Implement retriggers. The Manager Agent retrigger cap (SDT1-60, PR #128) now limits this to 3 attempts before requiring manual intervention.

### 5. Security hardening needs Railway variable changes documented upfront
SDT1-56 and SDT1-63 produced correct code changes that were ineffective until Railway env vars were updated. The next sprint's security tickets must include Railway variable changes in acceptance criteria.

### 6. Never run two Claude Code instances simultaneously
Running parallel sessions caused race conditions on GitHub (duplicate branches, conflicting PR states) and Jira (tickets transitioned twice). Now a Hard Rule.


---

### Sprint 8 — Bug Fixes ✅ Complete
Fix version 10264, native sprint ID 171. Epic SDT1-78.

| Exec # | Ticket | Summary | Status | PR |
|--------|--------|---------|--------|----|
| 1 | SDT1-79 | Replace ci_manager_agent with rule-based auto-merger | ✅ Done | #167 |
| 2 | SDT1-80 | Disable auto-implement.yml automatic trigger | ✅ Done | #168 |
| 3 | SDT1-83 | Remove PM Agent Claude API calls from backend | ✅ Done | #169 |
| 4 | SDT1-82 | Audit and revert SDT1-74 unrequested additions | ✅ Done | #170 |
| 5 | SDT1-81 | Fix Complete Sprint button returns Unknown error | ✅ Done | #171 |

**Fix PRs opened during Sprint 8 (infrastructure, not sprint tickets):**

| PR | Branch | What it fixed |
|----|--------|---------------|
| #164 | fix/remove-slack-from-ci | Remove Slack notification from CI pipeline |
| #165 | fix/remove-railway-health-check-from-ci | Remove Railway health check from CI pipeline |
| #166 | fix/add-sprint8-jira-ids | Add Sprint 8 Jira IDs to CLAUDE.md and PROJECT_CONTEXT.md |

---

## Sprint 8 Lessons Learned

### 1. Rule-based merger eliminates Claude API dependency for PR merging
`ci_manager_agent.py` was replaced with a deterministic rule-based auto-merger (SDT1-79, PR #167). All future PRs self-merge on CI pass without Claude API calls. This removes API cost and latency from the merge path and eliminates the class of failures where Claude disagreed with the merge criteria.

### 2. Dev Agent scope discipline: changes must match acceptance criteria only
SDT1-82 (PR #170) audited the SDT1-74 merge and confirmed the PR was clean. The scope creep that prompted the audit originated from SDT1-67 (PR #136), not SDT1-74. Going forward: always verify that files changed match only what the acceptance criteria require — nothing extra.

### 3. `deploy_railway_validated.py` blocks CI for 10+ minutes when Railway is slow
The Railway health-check validation script introduced in SDT1-67 (PR #136) caused CI to hang when Railway was slow to respond. It was removed (PR #165); restoration of the simple GraphQL `serviceInstanceRedeploy` mutation per AD-21 was not completed in Sprint 8.

### 4. CLAUDE_HISTORY.md should only be updated at sprint closeout, not mid-sprint
Partial in-progress updates to sprint tables (with `#TBD` PR numbers) create inconsistent history. Sprint history entries should be written once, completely, at closeout time.

---

### Sprint 9 — Multi-Product Support ✅ Complete
Fix version 10297, native sprint ID 204.

| Exec # | Ticket | Summary | Status | PR |
|--------|--------|---------|--------|----|
| 1 | SDT1-95 | Multi-product: configurable Jira, GitHub, Railway per product | ✅ Done | #176 |

**Fix PRs opened during Sprint 9 (infrastructure, not sprint tickets):**

| PR | Branch | What it fixed |
|----|--------|---------------|
| #174 | fix/ci-restore-graphql-deploy | Restore simple GraphQL deploy mutation in CI per AD-21 |
| #177 | fix/alembic-requirements | Add alembic to uat/backend/requirements.txt |
| #178 | fix/alembic-migration-001-idempotent | Make initial Alembic migration idempotent with if_not_exists |

---

## Sprint 9 Lessons Learned

### 1. Alembic must be in requirements.txt to be available in Railway pre-deploy commands
The `alembic` package was missing from `uat/backend/requirements.txt`, causing the Railway pre-deploy `alembic upgrade head` command to fail with `ModuleNotFoundError`. Added in fix PR #177. Any tool that runs in the Railway build/deploy context must be an explicit dependency.

### 2. Brownfield Alembic adoption requires `alembic stamp head` to initialise migration history on existing databases
When Alembic is introduced to an existing database (tables already created by SQLAlchemy directly), running `alembic upgrade head` fails because the `alembic_version` table does not exist. The correct sequence is: `alembic stamp head` (marks existing schema as at the current revision without running DDL), then future migrations apply normally. This is a one-time operation per environment.

### 3. All future migrations will run automatically via Railway pre-deploy command `alembic upgrade head`
The Railway service pre-deploy command is set to `alembic upgrade head`. New migration files committed to the repo will be picked up and applied automatically on the next deploy — no manual intervention required.

### 4. Migration files exist only on GitHub — no local equivalent needed, Claude Code reads them via API
Alembic migration files live in `uat/backend/alembic/versions/` in the GitHub repo. Claude Code reads and modifies them via the GitHub Contents API (no local checkout required). This is consistent with AD-2 (no git CLI dependency).

---

### Sprint 10 — Multi-Product Control Centre & Environment Pipeline ✅ Complete
Fix version 10330, native sprint ID 237.

| Exec # | Ticket | Summary | Status | PR |
|--------|--------|---------|--------|----|
| 1 | SDT1-96 | Multi-product: product selector in Control Centre | ✅ Done | #181 |
| 2 | SDT1-97 | Environments: three-environment pipeline DEV/TEST/PROD | ✅ Done | #182 |

**Fix PRs opened during Sprint 10 (infrastructure, not sprint tickets):**

| PR | Branch | What it fixed |
|----|--------|---------------|
| #180 | fix/add-sprint10-jira-ids | Add Sprint 10 Jira IDs to CLAUDE.md and PROJECT_CONTEXT.md |

---

## Sprint 10 Lessons Learned

### 1. New Control Centre components live in control-centre/src/components/ and control-centre/src/contexts/
Claude Code reads Control Centre source from GitHub via the Contents API when the `control-centre/` directory is not present locally. Any new component or context provider must be placed in these directories — the CI Dev Agent's `CC_KEYWORDS` detection targets `control-centre/` as the output root.

### 2. Environment pipeline requires Railway env vars set manually before TEST/PROD stages activate
SDT1-97 introduced `RAILWAY_TEST_SERVICE_NAME` and `RAILWAY_PROD_SERVICE_NAME` environment variables. The pipeline code is correct immediately after merge, but TEST and PROD stage buttons in the Control Centre remain inactive until these variables are set in the Railway dashboard for the backend service. Document new Railway variables in acceptance criteria (per Hard Rule on security hardening tickets).

### 3. Product selector uses localStorage for persistence — no backend session required
SDT1-96 stores the selected product in `localStorage` on the browser. No backend endpoint or database table is needed to remember the selection across page loads. This keeps the feature self-contained in the Control Centre frontend and avoids a new API dependency.


---

### Sprint 11 — Multi-Product & Control Centre Auth ✅ Complete
Fix version 10363, native sprint ID 270.

| Exec # | Ticket | Summary | Status | PR |
|--------|--------|---------|--------|----|
| 1 | SDT1-98 | Environments: Railway service per environment per product | ✅ Done | #185 |
| 2 | SDT1-99 | Environments: separate databases per product per environment | ✅ Done | #190 |
| 3 | SDT1-103 | Control Centre: Products admin tab | ✅ Done | #191 |
| 4 | SDT1-104 | Control Centre: Add login page using existing UAT backend auth | ✅ Done | #192 |

**Fix PRs opened during Sprint 11 (infrastructure, not sprint tickets):**

| PR | Branch | What it fixed |
|----|--------|---------------|
| #184 | fix/add-sprint11-jira-ids | Add Sprint 11 Jira IDs to CLAUDE.md and PROJECT_CONTEXT.md |
| #186 | fix/migration-003-idempotent | Make migration 003 idempotent — skip if products table absent |
| #187 | fix/sprint-11-cors-products-localhost | Fix: CORS on products, localhost URL in railwayApi, remove Orchestrator tab |
| #188 | fix/sprint-11-cors-and-pipeline-auth | Fix: CORS wildcard and pipeline status auth |
| #189 | fix/alembic-migrations-002-004-idempotent | Fix: make migrations 002 and 004 idempotent |

---

## Sprint 11 Lessons Learned

### 1. Products table was never created by Alembic — stamp had marked all migrations as applied without running them
The Alembic stamp operation marked all migrations as applied without actually running any DDL. This meant the `products` table existed (created by SQLAlchemy `create_all()`) but migration 002's `op.create_table()` would crash on `alembic upgrade head` because the table already existed, blocking the entire chain. Fix: `alembic stamp 001 && alembic upgrade head` to reset the revision pointer to before the products migrations and replay them from the correct baseline. All migration 002+ `upgrade()` functions must now be idempotent.

### 2. CORS wildcard (FRONTEND_URL=*) requires allow_credentials=False
When `FRONTEND_URL=*`, setting `allow_credentials=True` in the CORS middleware violates the CORS spec — browsers reject responses with both `Access-Control-Allow-Origin: *` and `Access-Control-Allow-Credentials: true`. Fix in `config.py`: `allow_credentials = "*" not in origins`. Bearer-token auth (`Authorization: Bearer ...`) works correctly without `allow_credentials=True` because the header is not a credential in the CORS sense.

### 3. Control Centre and UAT frontend were built as separate services but the intended architecture is one frontend per product
The Control Centre IS the frontend. The separate `Virtual-Dev-Team-UAT-Frontend` Railway service duplicates authentication and creates UX confusion. Sprint 12 will consolidate them: all UAT frontend pages (Login, Register, Dashboard, Profile, Notifications) will be merged into the Control Centre, and the UAT frontend Railway service will be decommissioned. See AD-23.

### 4. Product selector only appears when at least one product record exists
`ProductSelector.jsx` returns `null` when `products.length === 0`. An empty products table means no dropdown appears in the header. This is by design but confused initial testing — seed at least one product record before testing the product selector feature.

### 5. Control Centre needs authentication to call protected backend endpoints
The Control Centre had no login flow, causing product CRUD operations to return 401. Added a Login page (SDT1-104, PR #192) calling the existing `/auth/login` endpoint. Token stored under key `token` in localStorage, consistent with the UAT frontend storage key.

---

### Sprint 12 — Frontend Consolidation ✅ Complete
Fix version 10396, native sprint ID 303.

| Exec # | Ticket | Summary | Status | PR |
|--------|--------|---------|--------|----|
| 1 | SDT1-107 | Merge UAT frontend pages into Control Centre | ✅ Done | #195 |
| 2 | SDT1-108 | Decommission UAT frontend and update backend CORS | ✅ Done | #196 |

**Fix PRs opened during Sprint 12 (infrastructure, not sprint tickets):**

| PR | Branch | What it fixed |
|----|--------|---------------|
| #194 | fix/add-sprint12-jira-ids | Add Sprint 12 Jira IDs to CLAUDE.md and PROJECT_CONTEXT.md |

**Backlog bug tickets opened during Sprint 12:**

- **SDT1-109** — Fix: `/profile` endpoint returns 404 from Control Centre (backlog)
- **SDT1-110** — Fix: `/notifications/` endpoint returns 404 from Control Centre (backlog)
- **SDT1-113** — Fix: Switch email delivery from SMTP to Resend API (backlog)

---

## Sprint 12 Lessons Learned

### 1. Railway blocks outbound SMTP on ports 587 and 465
Password reset email delivery via SMTP failed silently because Railway blocks outbound traffic on the standard SMTP ports. Transactional email providers that deliver over HTTPS (Resend, SendGrid) are required for any email flow on Railway. Added as Sprint 13 backlog item (SDT1-111).

### 2. SMTP env var names must match exactly what the code reads
The code reads `SMTP_USERNAME` and `SMTP_FROM_EMAIL`; Railway initially had `SMTP_USER` and `FROM_EMAIL` set, causing silent auth failures with no visible error. Always verify env var names against the actual source before declaring an env-driven feature working.

### 3. Control Centre frontend service does not auto-redeploy when backend changes
The Control Centre Railway service only redeploys when its own source changes. Backend-only PRs that affect frontend behaviour (CORS, new endpoints) require a manual Control Centre redeploy. This is the inverse of the backend, which auto-deploys via the GraphQL `serviceInstanceRedeploy` mutation in `ci.yml` on every merge to `main`.

### 4. Frontend consolidation (AD-23) complete
All UAT frontend pages (Login, Register, Dashboard, Profile, Notifications) merged into the Control Centre. The separate `Virtual-Dev-Team-UAT-Frontend` Railway service was decommissioned. The Control Centre is now the single product frontend per AD-23.

---

### Sprint 13 — Bug Fixes & CI Hardening ✅ Complete
Epic SDT1-112. Fix version 10429, native sprint ID 336.

| Exec # | Ticket | Summary | Status | PR |
|--------|--------|---------|--------|----|
| 1 | SDT1-102 | Fix: Remove decommissioned UAT frontend from CI deploy job | ✅ Done | #201 |
| 2 | SDT1-109 | Fix: `/profile` endpoint returns 404 from Control Centre | ✅ Done | #203 |
| 3 | SDT1-110 | Fix: `/notifications/` endpoint returns 404 from Control Centre | ✅ Done | #204 |
| 4 | SDT1-113 | Fix: Switch email delivery from SMTP to Resend API | ✅ Done | #205 |

**Fix PRs opened during Sprint 13 (infrastructure, not sprint tickets):**

| PR | Branch | What it fixed |
|----|--------|---------------|
| #198 | fix/add-sprint13-jira-ids | Add Sprint 13 Jira IDs to CLAUDE.md and PROJECT_CONTEXT.md |
| #199 | fix/correct-sdt1-113-key-in-history | Correct SDT1-113 ticket key in CLAUDE_HISTORY.md Sprint 12 backlog |
| #200 | fix/hard-rule-resolve-discrepancies | Add Hard Rule: resolve Claude Code discrepancies in current action |
| #202 | fix/move-ad-bodies-to-project-context | Move AD bodies to PROJECT_CONTEXT.md to reduce CLAUDE.md below 40k |
| #206 | fix/control-centre-password-reset-token-link | Fix: handle password reset token from email link in Control Centre |

**Backlog bug tickets opened during Sprint 13:**

- **SDT1-114** — Fix: Sprint selector in Sprint Status tab not scrollable and does not default to active sprint (backlog)

---

## Sprint 13 Lessons Learned

### 1. Always verify backlog ticket current state before including it in a sprint
SDT1-102 was included in Sprint 13 based on its ticket description, but the underlying fix had already been implemented in Sprint 9 (PR #174). Going forward: before adding any backlog ticket to a sprint, verify the current state of the code against the ticket's acceptance criteria rather than assuming the description still reflects reality.

### 2. Execution order must be infrastructure-first
CI/pipeline fixes must always be exec order 1 so every subsequent PR in the sprint benefits from the corrected pipeline. Sprint 13 followed this pattern (SDT1-102 first) and the remaining tickets merged cleanly through the fixed CI.

### 3. Railway blocks outbound SMTP on all ports — Resend API over HTTPS is the correct solution
SMTP-based email delivery is fundamentally unsupported on Railway (confirmed across ports 25, 465, 587, 2525). The Resend API delivers over HTTPS, sidestepping the block entirely. Domain verification for `contact.synproconsulting.co` via Namecheap DNS completed in under 15 minutes — Resend's verification flow is fast once the registrar is identified.

### 4. Gmail addresses cannot be used as Resend sender addresses
Resend rejects free-mail-provider domains (gmail.com, yahoo.com, outlook.com) as sender addresses. A verified owned domain is mandatory. Sprint 13 used `noreply@contact.synproconsulting.co` after verifying the apex domain.

### 5. Control Centre has no URL router — deep links require mount-time query parsing
The password reset email link delivers a token as a query string parameter, but the Control Centre is a single-page React app with no router. Handling deep links requires mount-time `URLSearchParams` parsing in `App.jsx` to extract the token and route the user into the reset flow. Adding a router was out of scope for SDT1-113; the query-string parser was the minimum viable fix (PR #206).

### 6. Resolve Claude Code discrepancies in the current action — never defer
When Claude Code flags a discrepancy (corrected ticket key, wrong ID, file-size limit breach) at the end of its output, the correction must be folded into the same PR. Deferring to a follow-up PR creates inconsistent intermediate states in the docs. Added as a Hard Rule (PR #200) after the SDT1-113 ticket-key correction had to be done as a separate follow-up (PR #199) instead of being included in PR #198.

### 7. CLAUDE.md size matters — keep under 40 000 characters
Claude Code performance degrades when CLAUDE.md exceeds ~40 000 characters. Sprint 13 moved the full AD bodies (Decision / Why / Consequence / Do not) into PROJECT_CONTEXT.md Section 12, leaving one-line summaries in CLAUDE.md with cross-references (PR #202). Reference content that is not needed at every session start belongs in PROJECT_CONTEXT.md.

---

### Sprint 14 — Multi-Product Credentials & Product-Scoped Control Centre ✅ Complete
Epic SDT1-116. Fix version 10462, native sprint ID 369.

| Exec # | Ticket | Summary | Status | PR |
|--------|--------|---------|--------|----|
| 1 | SDT1-117 | Fix: Add Product returns missing or invalid Authorization header | ✅ Done | #209 |
| 2 | SDT1-118 | Redesign products table schema — per-product credentials and environment model | ✅ Done | #210 |
| 3 | SDT1-119 | Redesign Products tab UI — grouped sections and masked secret fields | ✅ Done | #211 |
| 4 | SDT1-120 | Seed SynPro VSDC as first product record | ✅ Done | #213 |
| 5 | SDT1-121 | Product-scoped Control Centre — all tabs filter by selected product | ✅ Done | #214 |
| 6 | SDT1-114 | Fix: Sprint selector scrollable and defaults to active sprint | ✅ Done | #216 |

**Fix PRs opened during Sprint 14 (infrastructure, not sprint tickets):**

| PR | Branch | What it fixed |
|----|--------|---------------|
| #208 | fix/add-sprint14-jira-ids | Add Sprint 14 Jira IDs to CLAUDE.md and PROJECT_CONTEXT.md |
| #212 | fix/sdt1-119-secret-fields-change-pattern | Secret fields in edit mode use Change pattern instead of empty input |
| #215 | fix/sdt1-121-overview-tab-product-scoped | Scope Overview tab to selected product |
| #217 | fix/sdt1-114-sprint-selector-fixes | Sprint selector scroll, order, mouse wheel and overlap fixes |
| #218 | fix/sdt1-121-proxy-jira-project-key | Jira proxy endpoints respect jira_project_key parameter |
| #219 | fix/sdt1-121-sprints-no-board-fallback | Remove hardcoded board/34 fallback from sprints endpoint |
| #220 | fix/sdt1-121-jira-board-id-per-product | Add jira_board_id per product and restore active sprint state |
| #221 | fix/sdt1-121-product-form-jira-board-id | Add Jira Board ID field to Product form |

**Backlog bug tickets opened during Sprint 14:**

- **SDT1-122** — Fix: Remove +Add button from product selector dropdown in header (backlog)
- **SDT1-123** — Fix: Request logging middleware throws ValueError in log formatter (backlog)

---

## Sprint 14 Lessons Learned

### 1. Verify the localStorage JWT key matches across all components
SDT1-117 root cause was `AddProductModal.jsx` reading `"authToken"` while `LoginPage` stored under `"token"`. Mismatched keys cause silent auth failures with no obvious error — the request goes out without an Authorization header and the backend returns 401. Always grep for every read of `localStorage.getItem(...)` against the canonical write site before debugging "missing or invalid Authorization header" symptoms.

### 2. Secret fields in edit forms must use a Change pattern, not empty inputs
An empty password input in an edit form gives no indication whether a value is already saved and provides no safe way to update it intentionally — typing into it could either set a new value or accidentally overwrite the existing one with garbage. The Change pattern (locked display showing `........` plus a Change button that swaps in an unlocked input) makes the state explicit and the action deliberate (PR #212).

### 3. Per-product credentials require encryption at rest with a stable key
The `SECRET_ENCRYPTION_KEY` Fernet key must be generated and set in Railway **before** migration 006 runs. Once set it must never change — rotating the key makes every stored credential unreadable, with no recovery path short of manual re-entry of every secret. Store a copy of the Fernet key in a password manager immediately after generating it.

### 4. `product_id=None` is wrong as the default-product signal once products are real DB rows
SynPro VSDC is a regular `products` row with a UUID, not a null sentinel. Any backend logic that uses `product_id is None` as a special case for the default product will silently fail once the frontend ProductContext always passes a real UUID — the "default" branch becomes unreachable. PR #219 fell into this trap and PR #220 had to undo it. Trace the actual value the frontend sends before writing backend fallback logic.

### 5. Hardcoded board IDs must be per-product from the start
The hardcoded `/board/34/sprint` assumption for native sprint metadata caused cross-product sprint bleed (FPRM showed SDT1 sprints) and required three fix PRs to resolve cleanly (#218 → #219 → #220 → #221). Whenever a Jira resource (board, project, version) is referenced from the proxy, it must be a per-product column from the outset, with an optional env-var fallback for the operator to set during the migration window.

### 6. Proxy endpoint fallback chains must be explicit and tested per caller
PR #219 assumed `product_id=None` was the SynPro VSDC signal, but the frontend never sends null — the dashboard gates rendering on `productCredentials` being non-null, so every call carries a UUID. Always trace what the frontend actually sends (read the API client, not the spec) before writing a backend fallback chain. The three-level resolution (product row → env var → None) introduced in PR #220 documents each layer explicitly so the dead branch problem doesn't recur.

### 7. New schema columns must be reflected in the UI form in the same PR
`jira_board_id` was added to the backend in PR #220 but the Products form wasn't updated until PR #221, leaving operators unable to set the field via the UI for one deploy cycle. When adding a column the user is expected to populate via the Products tab, the form update belongs in the same PR — otherwise the column is unreachable from the UI until the follow-up lands.

### 8. Set safety-net env vars in Railway whenever a board ID is operationally required
The three-level resolution chain (product row → env var → None) means the `JIRA_BOARD_ID` env var acts as a safety net during the window between migration and product record update. Setting it in Railway alongside the column rollout means SynPro VSDC keeps working even if the operator forgets to fill in the new field on the existing product row.

---

### Sprint 15 — Control Centre UX Polish & Process Hardening ✅ Complete
**Dates:** 14 May 2026 – 20 May 2026.
**Native sprint ID 402, fix version 10495.**
12 tickets, 27 story points, all merged.

| Exec # | Ticket | Type | Summary | Points | Status | PR |
|--------|--------|------|---------|--------|--------|----|
| 1 | SDT1-123 | Bug | Fix: Request logging middleware throws ValueError in log formatter | 1 | ✅ Done | #224 |
| 2 | SDT1-122 | Bug | Fix: Remove +Add button from product selector dropdown in header | 1 | ✅ Done | #225 |
| 3 | SDT1-91  | Story | Control Centre: Merge Workflows into Sprint Status tab | 5 | ✅ Done | #226 |
| 4 | SDT1-88  | Bug | Control Centre: PRs show linked Jira issue | 3 | ✅ Done | #227 |
| 5 | SDT1-89  | Story | Control Centre: Show closed PRs in PR list | 2 | ✅ Done | #229 |
| 6 | SDT1-90  | Story | Control Centre: Workflows show PR and Jira issue references | 3 | ✅ Done | #233 |
| 7 | SDT1-92  | Story | Control Centre: Text filter on Sprint Status tab | 3 | ✅ Done | #235 |
| 8 | SDT1-93  | Story | Control Centre: CSV download for any list view | 3 | ✅ Done | #237 |
| 9 | SDT1-126 | Bug | Fix: PR ticketKey regex fails on conventional commit titles and digit-bearing project keys | 2 | ✅ Done | #230 |
| 10 | SDT1-127 | Bug | Fix: Workflows sub-tab count shows 0 until tab is first clicked | 1 | ✅ Done | #230 |
| 11 | SDT1-128 | Bug | Fix: sprint selector shows wrong product's sprints when jira_board_id is null | 2 | ✅ Done | #234 |
| 12 | SDT1-130 | Bug | Fix: text filter search box background too dark — hard to see | 1 | ✅ Done | #236 |

**All PRs opened during Sprint 15 (#223–#237 — all merged):**

| PR | Branch | Title | Status |
|----|--------|-------|--------|
| #223 | fix/sprint-15-setup | docs: Sprint 15 setup + retire agent hard rules | ✅ Merged |
| #224 | feature/SDT1-123-fix-logging-middleware-valueerror | fix(SDT1-123): fix malformed log format string in request logging middleware | ✅ Merged |
| #225 | feature/SDT1-122-remove-add-button-header-dropdown | fix(SDT1-122): remove +Add button from product selector dropdown in header | ✅ Merged |
| #226 | feature/SDT1-91-merge-workflows-into-sprint-status | feat(SDT1-91): merge Workflows into Sprint Status tab | ✅ Merged |
| #227 | feature/SDT1-88-pr-list-show-linked-jira-issue | feat(SDT1-88): show linked Jira issue key on each open PR card | ✅ Merged |
| #228 | fix/jira-lifecycle-hard-rule | docs: correct Jira ticket lifecycle hard rule — Done on merge not on PR open | ✅ Merged |
| #229 | feature/SDT1-89-show-closed-prs-with-filters | feat(SDT1-89): show closed PRs with All/Open/Merged/Failed/Closed filter pills | ✅ Merged |
| #230 | fix/pr-annotation-regex-and-workflow-count | fix: correct PR ticketKey regex for conventional commits and prime workflow count (SDT1-126 + SDT1-127) | ✅ Merged |
| #231 | fix/hard-rule-bug-ticket-required-for-fix-prs | docs: hard rule — Jira bug ticket required before any fix PR | ✅ Merged |
| #232 | fix/hard-rule-one-pr-at-a-time | docs: hard rule — one PR at a time, no exceptions | ✅ Merged |
| #233 | feature/SDT1-90-workflows-show-pr-and-jira-references | feat(SDT1-90): show linked PR number and Jira ticket on workflow run cards | ✅ Merged |
| #234 | fix/SDT1-128-sprint-board-bleed-null-board-id | fix(SDT1-128): prevent sprint board bleed when product jira_board_id is null | ✅ Merged |
| #235 | feature/SDT1-92-text-filter-sprint-status | feat(SDT1-92): add text filter to Sprint Status tab across all sub-tabs | ✅ Merged |
| #236 | fix/SDT1-130-search-input-background | fix(SDT1-130): lighten search input background for visibility | ✅ Merged |
| #237 | feature/SDT1-93-csv-download-all-list-views | feat(SDT1-93): add CSV download to all Sprint Status list views | ✅ Merged |

**Bug tickets opened mid-sprint and resolved in-sprint (root causes):**

- **SDT1-126** — PR-title regex in `annotatePr` was anchored to `[SDT1-XX]` bracket form only; conventional-commit titles `feat(SDT1-89): …` weren't matched, so the SDT1-88 ticket badge was missing on most PRs. Regex extended to capture both `(SDT1-89)` and `[SDT1-89]` plus made case-insensitive. Sibling bug: branch-name regex used `[a-zA-Z]+-\d+` which couldn't match project keys ending in a digit like `SDT1`. PR #230.
- **SDT1-127** — Workflows tab badge stuck at `0` until the tab was first opened, because `GitHubWorkflowMonitor` only reported its count via `onRunsChange` after its own fetch fired, and the fetch only fired when the tab mounted. Reworked: the count fallback in `SprintDashboard` now uses `globalData.runs.length` until the monitor reports. PR #230.
- **SDT1-128** — `_get_product_jira_board_id` fell through to the `JIRA_BOARD_ID` env var when a product row's column was `NULL`, silently substituting board 34 (SDT1) for products like Fracttal PRM that had no board configured. The endpoint then dumped SDT1 sprints into Fracttal's response via the native-sprint fallback. Fix: when `product_id` is supplied, return `None` instead of env-var fallback; data fix on Fracttal PRM to set `jira_board_id = 67`. PR #234.
- **SDT1-130** — Search input from SDT1-92 used `background: var(--bg)` which is identical to the page body, making the input invisible. Changed to `var(--bg-hover)`, the established "subtle elevation" tone already used for `cc-nav-btn:hover` etc. PR #236.

**Hard rules added during Sprint 15:**

1. **Agent retirement** (PR #223) — Claude Code is the Dev Agent: don't invoke `agents/dev_agent.py` or dispatch `auto-implement.yml` programmatically. The rule-based auto-merger in `ci.yml` is the Manager Agent: don't invoke `agents/manager_agent.py` or `ci_manager_agent.py` directly. Sprint setup is performed by direct Jira REST calls from Claude Code: don't invoke `agents/pm_agent.py` for planning.
2. **Jira ticket lifecycle — Done on merge, not on PR open** (PR #228) — Transition to In Progress before starting; leave In Progress when the PR opens; Done only after the auto-merger merges to `main`. Premature transitions to Done caused Sprint 15 tickets to look complete while their PRs were still in CI.
3. **Bug ticket required before any fix PR** (PR #231) — Before opening a fix PR for a bug discovered mid-sprint, create a Jira bug ticket in the current sprint first. PR title must reference the ticket key: `fix(SDT1-XX): …`. No fix PR may be opened without a corresponding ticket.
4. **One PR at a time — no exceptions** (PR #232) — Before opening any PR, verify zero PRs are currently open in the repo via the GitHub API. Wait for the current one to merge before opening the next. Applies to feature, fix, and docs PRs without exception.

**Backlog items raised during Sprint 15:**

- **SDT1-125** — Auto-merger: transition Jira ticket to Done on PR merge via Jira API. (Story, To Do — the gap the lifecycle hard rule documents as a manual responsibility until automated.)
- **SDT1-129** — Control Centre: filter Workflows sub-tab by selected sprint. (Story, To Do — surfaced while implementing SDT1-90; Workflows currently shows all recent runs regardless of selected sprint.)

---

## Sprint 15 Lessons Learned

### 1. Per-product config columns must never fall through to a shared env-var default
SDT1-128 root cause was the `_get_product_jira_board_id` resolution chain treating `JIRA_BOARD_ID` env var as a fallback when *any* product row had `NULL` for `jira_board_id`. The intent was always *"a per-product `NULL` means no board for that product"*, but the env-var fallback silently inherited another product's board. The fix: when `product_id` is supplied, only consult that product's row — env-var fallback applies only to the `product_id is None` legacy path. Anytime a per-product column has an env-var "default" sibling, the resolution function must distinguish *"caller didn't specify a product"* from *"caller specified a product but its column is null"* — the second case must never inherit the env-var default.

### 2. Tab-badge counts are also state — they must reflect query filters too
SDT1-92's text filter narrowed the visible rows in every sub-tab, but until the badge counts also updated, the user got a misleading "Pull Requests (12)" when only 3 were visible. The filter, the rendered list, and the badge all need to read from the same filtered source. The same pattern applied to the Workflows tab where the monitor manages its own data: the parent passes `filterQuery` down and the monitor reports the post-filter count back via `onRunsChange`, so the badge tracks the query even though the data lives elsewhere.

### 3. CSS variables that share a value with the page body are invisible as control backgrounds
The SDT1-92 input used `var(--bg)` for its background, identical to the page body — there was nothing to distinguish the input from the surrounding tab bar. The established "subtle elevation" tone in this codebase is `var(--bg-hover)` (used for nav-button hover and the user dropdown button). Whenever an interactive control needs to read as a control, it must use a tone *different from* its immediate parent, not from "the dark theme generally". SDT1-130 was the one-line fix.

### 4. Add a Jira bug ticket the moment a bug is discovered — not "later"
Three bugs were discovered while implementing Sprint 15 stories (SDT1-126/127 during SDT1-88 work, SDT1-128 during SDT1-91 work, SDT1-130 immediately after SDT1-92 merged). The new hard rule (PR #231) requires the bug ticket to be created *before* the fix PR opens — not after. Bundling two unrelated tickets into one PR (SDT1-126 + SDT1-127 in PR #230) muddies the audit trail; the hard rule was deliberately tightened mid-sprint to prevent that pattern recurring.

### 5. "Done on PR open" was a quiet rule violation hiding in plain sight
Until PR #228, the convention was to mark Jira tickets Done when the PR opened, on the implicit assumption the auto-merger would always succeed. This collapses two distinct states (work submitted vs. work shipped) and made Sprint 15's progress look healthier than it was when several PRs were sitting in CI. Until SDT1-125 automates the Jira transition on merge, the operator (or a follow-up Claude Code session) is responsible for the Done transition — and it must happen *after* merge confirmation, never on PR open. Every Sprint 15 ticket left "In Progress" through PR open was correctly transitioned to Done at sprint closeout, not when the PR was raised.

### 6. Duplicated tiny helpers beat a new module for genuinely small scopes
SDT1-93 added a 15-line `downloadCsv` helper plus a 4-line `csvFilename` helper to four files. The instinct to extract them into a shared module was deliberately resisted — the helpers are dependency-free, semantically obvious, and the spec called out *"no new files, no new dependencies"*. The duplication tax is one place to remember to update if the CSV escaping ever needs to change; the cost saved is one more cross-file import path and one more module in the tree. For trivially-small genuinely-shared logic, duplication is the right call. Reach for extraction when the helper grows non-trivial or starts attracting variants.

### 7. Sprint setup IDs landing in the same PR as the rule changes works well
PR #223 combined "set up Sprint 15 Jira IDs" with "add agent retirement hard rules" in one closeout-style commit. Mixing rules + data in one PR is usually a smell, but for sprint kickoff it worked: both were docs-only, both were prerequisites for the sprint, and bundling them avoided two near-identical opening PRs that nobody would have reviewed independently. The pattern is: kickoff docs PRs can bundle related rule additions; mid-sprint rule additions stay in their own PRs (as #228, #231, #232 did).