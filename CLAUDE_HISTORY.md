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
| #172 | fix/restore-simple-graphql-deploy | Restore simple GraphQL deploy mutation in CI per AD-21 |

---

## Sprint 8 Lessons Learned

### 1. Rule-based merger eliminates Claude API dependency for PR merging
`ci_manager_agent.py` was replaced with a deterministic rule-based auto-merger (SDT1-79, PR #167). All future PRs self-merge on CI pass without Claude API calls. This removes API cost and latency from the merge path and eliminates the class of failures where Claude disagreed with the merge criteria.

### 2. Dev Agent scope discipline: changes must match acceptance criteria only
SDT1-82 (PR #170) audited the SDT1-74 merge and confirmed the PR was clean. The scope creep that prompted the audit originated from SDT1-67 (PR #136), not SDT1-74. Going forward: always verify that files changed match only what the acceptance criteria require — nothing extra.

### 3. `deploy_railway_validated.py` blocks CI for 10+ minutes when Railway is slow
The Railway health-check validation script introduced in SDT1-67 (PR #136) caused CI to hang when Railway was slow to respond. It was removed (PR #165) and the CI deploy step was restored to the simple GraphQL `serviceInstanceRedeploy` mutation per AD-21 (PR #172).

### 4. CLAUDE_HISTORY.md should only be updated at sprint closeout, not mid-sprint
Partial in-progress updates to sprint tables (with `#TBD` PR numbers) create inconsistent history. Sprint history entries should be written once, completely, at closeout time.