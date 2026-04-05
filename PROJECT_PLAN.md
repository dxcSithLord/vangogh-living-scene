# Van Gogh Living Scene — Project Plan

> **Single source of truth for current status.**
> Active work → `docs/plan/kanban.md`.
> Completed work → `PLAN_HISTORY.md`.
> Sprint definitions → `docs/plan/sprints.md`.

Version: 3.0
Last reviewed: 2026-04-05

---

## Current sprint

**Sprint 5 — CI completion** — blocker cleared, 3 cards in flight

E1 (#24) merged as #29 on 2026-04-05. E2, E3, E4 are now unblocked and
runnable in parallel branches.

Top of kanban (snapshot — authoritative copy in `docs/plan/kanban.md`):

| Status | ID | Title | Issues |
|---|---|---|---|
| Todo | E2 | conftest.py hardware-dep stubs | #25 |
| Todo | E3 | scripts/compliance-check.sh | #26 |
| Todo | E4 | Capture CI baselines | #27 |
| Done (recent) | E1 | Pin GH Actions to SHAs + Dependabot | #24 → PR #29 |

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
