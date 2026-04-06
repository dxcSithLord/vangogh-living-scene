# Van Gogh Living Scene — Project Plan

> **Single source of truth for current status.**
> Active work → `docs/plan/kanban.md`.
> Completed work → `PLAN_HISTORY.md`.
> Sprint definitions → `docs/plan/sprints.md`.

Version: 3.1
Last reviewed: 2026-04-06

---

## Current sprint

**Sprint 6 — Triage & enforcement** — Complete

All lint/type findings cleared: ruff format 0, ruff lint 0, mypy strict 0.
All CI checks now blocking (continue-on-error removed).

Top of kanban (snapshot — authoritative copy in `docs/plan/kanban.md`):

| Status | ID | Title | PRs |
|---|---|---|---|
| Done | T1 | Ruff autofix sweep | #37 |
| Done | T2 | Ruff lint non-autofix (all 29 cleared) | #41 |
| Done | T3 | Mypy strict fixes (all 23 cleared) | #38, #39, #40 |
| Done | T4 | Bandit (already clean) | — |
| Done | T5 | Pip-audit (already clean) | ��� |
| Done | T6 | Flip continue-on-error → false | #42 |

---

## Plan structure

| File | Purpose | Loaded every session? |
|---|---|---|
| `PROJECT_PLAN.md` (this file) | Current sprint pointer + top-of-kanban snapshot | yes |
| `docs/plan/kanban.md` | Full backlog + Definition of Done + ops tasks | yes |
| `PLAN_HISTORY.md` | Archive of merged PRs and completed sprint work | no |
| `docs/plan/sprints.md` | Sprint 1–4 historical definitions + test criteria | on demand |
| `docs/plan/architecture.md` | System diagram + memory sequence | on demand |
| `docs/plan/gap-analysis.md` | Source of gap-analysis issues #3–#20 | on demand |
| `docs/plan/risks.md` | Known risks and mitigations | on demand |
| `docs/plan/install.md` | Install commands and model URLs | on demand |
| `docs/plan/prerequisites.md` | Hardware prerequisites | on demand |
| `SECURITY-POLICY.md` | Standards traceability (NIST, OWASP, CIS, FIPS) | on demand |
| `ARCHITECTURE.md` | Living architecture doc | on demand |

---

## Module delivery status

Sprint 1–4 + 2.5 modules: all **Done**. Archived to `PLAN_HISTORY.md`.

Ongoing module-level work is tracked per-card in `docs/plan/kanban.md`.
