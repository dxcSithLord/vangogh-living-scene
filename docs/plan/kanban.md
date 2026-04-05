# Kanban — Van Gogh Living Scene

> Canonical backlog. Columns move left→right as work progresses.
> Session restart: read only **this file** plus `PROJECT_PLAN.md`.

Last reviewed: 2026-04-05

---

## Definition of Done (applies to every card)

- [ ] Branch pushed with **signed commits** (GPG, noreply UID)
- [ ] PR opens with `Closes #N` for every issue the card resolves
- [ ] CI workflows green (or report-only findings reviewed)
- [ ] New files include security/standards header comment where applicable
- [ ] Any new GitHub Action pinned to full commit SHA (post-#24)
- [ ] Card moved to `Done` in this file at PR-merge time

---

## Current sprint: **Sprint 5 — CI completion**

### Todo (Sprint 5)

| ID | Title | Issues | Branch | Blocker? | Notes |
|---|---|---|---|---|---|
| **E1** | Pin GH Actions to SHAs + Dependabot | #24 | `ci/pr-4-pin-actions-shas` | **BLOCKER** | Must land first; all later PRs inherit SHA pinning |

### Backlog — Sprint 5 (unblocked after E1 merges)

| ID | Title | Issues | Branch | Parallel? |
|---|---|---|---|---|
| E2 | conftest.py hardware-dep stubs | #25 | `ci/e2-conftest-hw-stubs` | ✅ with E3, E4 |
| E3 | scripts/compliance-check.sh (PR-7) | #26 | `ci/e3-compliance-check-sh` | ✅ with E2, E4 |
| E4 | Capture CI baselines → docs/ci-baseline.md | #27 | `ci/e4-baseline-capture` | ✅ with E2, E3 (but benefits from E2 landing first for pytest counts) |

---

## Sprint 6 — Triage & enforcement (gated on E4)

### Backlog

| ID | Title | Source | Parallel? |
|---|---|---|---|
| T1 | Ruff autofix (format + --fix safe rules) | E4 baseline | ✅ |
| T2 | Ruff lint (non-autofix) — one sub-PR per rule family | E4 baseline | ✅ sub-branches |
| T3 | Mypy strict fixes — per module | E4 baseline | ✅ per module |
| T4 | Bandit findings — by severity/module | E4 baseline | ✅ |
| T5 | Pip-audit CVE dep bumps | E4 baseline | ✅ |
| T6 | Flip continue-on-error → false across all workflows | — | **SERIAL** after T1–T5 |

---

## Sprint 7 — Gap backlog (runnable in parallel with Sprints 5/6)

### Backlog

| ID | Title | Issues combined | Branch | Module(s) |
|---|---|---|---|---|
| G-DOC | Docs cleanup (omnibus or per-issue) | #3 #5 #9 #10 #12 #14 #15 #19 | `gap/g-doc-*` | docs only |
| G-GHOST | Ghost cache refresh + skip logic | #6 #7 | `gap/g-ghost-cache` | `presence.py` |
| G-SLOTS | Missing slots JSON (may block E2) | #4 | `gap/g-slots-json` | `assets/`, `config_validator.py` |
| G-RSS | Enforce `memory.rss_warning_mb` in main | #8 | `gap/g-rss-threshold` | `main.py` |
| G-CONFIG-EVT | Emit `CONFIG_VALIDATION_FAIL` security event | #18 | `gap/g-config-evt` | `config_validator.py`, `security_log.py` |
| G-VERIFY | Verification tasks (read-only, may spawn follow-ups) | #11 #13 #20 | `gap/g-verify-*` | tests + docs |

**Cross-sprint dependency:** G-SLOTS (#4) may unblock E2 integration tests → consider pulling into Sprint 5.

---

## In-progress

_(empty — populate as branches are created)_

---

## Done (recent, last 10)

Full history in `PLAN_HISTORY.md`.

| ID | Title | PR | Merged |
|---|---|---|---|
| CI-3 | security workflow (PR-3) | #23 | 2026-04-05 |
| CI-2 | lint + test workflows (PR-2) | #22 | 2026-04-05 |
| CI-1 | per-tool configs (PR-1) | #21 | 2026-04-05 |

---

## Ops / admin (not PRs)

- [ ] Branch protection on `main`: require signed commits, require PR reviews, require status checks (post-T6)
- [ ] Confirm GPG key with noreply UID is active for all committers
- [ ] Dependabot (pip ecosystem) — follow-up to E1, separate issue when E1 merges
