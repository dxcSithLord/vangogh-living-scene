# Van Gogh Living Scene — Project Plan

> **Single source of truth for current status.**
> Active work → `docs/plan/kanban.md`.
> Completed work → `PLAN_HISTORY.md`.
> Sprint definitions → `docs/plan/sprints.md`.

Version: 3.3
Last reviewed: 2026-04-07

---

## Current sprint

**Sprint 7 — Gap backlog** — 11 cards, prioritised P1–P8

Sprint 6 complete (all CI checks blocking). Sprint 7 addresses gap-analysis
findings ordered by runtime impact: startup blockers first, then bugs,
safety, security compliance, verification, tooling, and docs last.
Code review on 2026-04-07 identified 3 additional documentation gaps
(G-DOC-ARCH, G-DOC-MODULES, G-DOC-SECURITY).

Top of kanban (snapshot — authoritative copy in `docs/plan/kanban.md`):

| Pri | ID | Title | Issues |
|---|---|---|---|
| ~~P1~~ | ~~G-SLOTS~~ | ~~Missing slots JSON~~ | ~~#4~~ |
| ~~P2~~ | ~~G-GHOST~~ | ~~Ghost cache refresh + skip logic~~ | ~~#6 #7~~ |
| P3 | G-RSS | Enforce `memory.rss_warning_mb` in main loop | #8 |
| P4 | G-CONFIG-EVT | Emit `CONFIG_VALIDATION_FAIL` + fix init order | #18 |
| P5 | G-VERIFY | Verification tasks (read-only) | #11 #13 #20 |
| P6 | G-COMPLY-VERSIONS | Pre-flight tool-version check | — |
| P7 | G-DOC | Docs cleanup | #3 #5 #9 #10 #12 #14 #15 #19 |
| P7 | G-DOC-ARCH | Update ARCHITECTURE.md — ghost cache, RSS, fast path | — |
| P7 | G-DOC-MODULES | Update modules.md — slots API, GhostCache, protocols | — |
| P7 | G-DOC-SECURITY | Security reference docs — events, validation, limits | — |
| P8 | G-INSTALL-DOC | Refresh install.md (gated on-Pi run) | — |

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
