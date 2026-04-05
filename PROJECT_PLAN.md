# Van Gogh Living Scene — Project Plan

> **Single source of truth for current status.**
> Active work → `docs/plan/kanban.md`.
> Completed work → `PLAN_HISTORY.md`.
> Sprint definitions → `docs/plan/sprints.md`.

Version: 3.1
Last reviewed: 2026-04-06

---

## Current sprint

**Sprint 6 — Triage & enforcement** — in progress, T1/T4/T5 done, T3 draining

Sprint 5 (E1–E4) fully merged on 2026-04-05. Sprint 6 triage started the same
day: T1 (ruff autofix) merged as #37; first T3 slice (define_slots TypedDict,
mypy.ini cleanup, codebase-wide LANCZOS migration, DisplayProtocol, Pillow/numpy
added to dev deps) merged as #38. Second T3 slice (dict/Queue generics) open
as #39.

Top of kanban (snapshot — authoritative copy in `docs/plan/kanban.md`):

| Status | ID | Title | PRs |
|---|---|---|---|
| Done | T1 | Ruff autofix sweep | #37 |
| In progress | T3 | Mypy strict fixes (3 errors remaining) | #38 merged, #39 open |
| Todo | T2 | Ruff lint non-autofix (32 findings) | — |
| Blocked | T6 | Flip continue-on-error → false | waits on T2+T3 |

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
