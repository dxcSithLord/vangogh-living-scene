# Kanban — Van Gogh Living Scene

> Canonical backlog. Columns move left→right as work progresses.
> Session restart (orientation): read this file plus `PROJECT_PLAN.md`.
> Before making code changes: confirm the sprint matches
> `docs/plan/sprints.md` per CLAUDE.md "Before writing code" rule #3.

Last reviewed: 2026-04-06 (Sprint 6 in progress)

---

## Definition of Done (applies to every card)

- [ ] Branch pushed with **signed commits** (GPG, noreply UID)
- [ ] PR opens with `Closes #N` for every issue the card resolves
- [ ] CI workflows green (or report-only findings reviewed)
- [ ] New files include security/standards header comment where applicable
- [ ] Any new GitHub Action pinned to full commit SHA (post-#24)
- [ ] Card moved to `Done` in this file at PR-merge time

---

## Current sprint: **Sprint 6 — Triage & enforcement**

Sprint 5 complete (E1/E2/E3/E4 all merged). T1–T5 can run in parallel; T6 is serial after.

Running totals against `docs/ci-baseline.md`:

| Check | Baseline | Current | Delta |
|---|---:|---:|---:|
| ruff format files | 11 | 0 | −11 |
| ruff lint findings | 45 | 29 | −16 |
| mypy strict errors | 23 | 3 | −20 |
| bandit (medium+) | 0 | 0 | — |
| pip-audit CVEs | 0 | 0 | — |

### Status

| ID | Title | Status | PRs |
|---|---|---|---|
| T1 | Ruff autofix (format + --fix safe rules) | ✅ Done | #37 |
| T2 | Ruff lint (non-autofix) — one sub-PR per rule family | Todo | — |
| T3 | Mypy strict fixes — per module | 🟡 In progress (3 errors remaining) | #38, #39 merged; final slice next |
| T4 | Bandit findings — by severity/module | ✅ Done (already clean per baseline) | — |
| T5 | Pip-audit CVE dep bumps | ✅ Done (already clean per baseline) | — |
| T6 | Flip continue-on-error → false across all workflows | 🔒 Blocked on T2+T3 | — |

### T3 remaining (3 mypy strict errors)

One 1-file slice per error — can be bundled if trivial:

| File | Error | Error code |
|---|---|---|
| `src/config_validator.py:110` | Argument 1 to `float` has incompatible type | arg-type |
| `src/styler.py:99` | Returning `Any` from typed function | no-any-return |
| `src/compositor.py:56` | Incompatible types in assignment (`Image` → `ImageFile` variable) | assignment |

### T2 scope (29 ruff lint findings, 11 rule codes)

Dominated by `PLC0415` (17 hits remaining — import-outside-top-level, the lazy
hardware-dep pattern). 3 were suppressed in `camera.py` via `# noqa: PLC0415`
as part of T3/#39 review follow-up. Split by rule family across sub-branches:

| Count | Rule | Suggested approach |
|---:|---|---|
| 17 | PLC0415 | Add targeted `# noqa: PLC0415` with justification, or `lint.per-file-ignores` for modules using lazy imports |
| 2 | PLR0912 | Refactor or `# noqa` with justification |
| 2 | RUF001 | Replace en-dash with hyphen in log strings (or allow via config) |
| 1 each | B905, E402, E501, PLR0915, PLR2004, RUF059, S110, T201 | One-line fixes |

---

## Sprint 7 — Gap backlog (runnable in parallel with Sprint 6)

### Backlog

| ID | Title | Issues combined | Branch | Module(s) |
|---|---|---|---|---|
| G-DOC | Docs cleanup (omnibus or per-issue) | #3 #5 #9 #10 #12 #14 #15 #19 | `gap/g-doc-*` | docs only |
| G-GHOST | Ghost cache refresh + skip logic | #6 #7 | `gap/g-ghost-cache` | `presence.py` |
| G-SLOTS | Missing slots JSON (may block E2) | #4 | `gap/g-slots-json` | `assets/`, `config_validator.py` |
| G-RSS | Enforce `memory.rss_warning_mb` in main | #8 | `gap/g-rss-threshold` | `main.py` |
| G-CONFIG-EVT | Emit `CONFIG_VALIDATION_FAIL` security event | #18 | `gap/g-config-evt` | `config_validator.py`, `security_log.py` |
| G-VERIFY | Verification tasks (read-only, may spawn follow-ups) | #11 #13 #20 | `gap/g-verify-*` | tests + docs |
| G-INSTALL-DOC | Refresh `docs/plan/install.md` with confirmed deps | — | `gap/g-install-doc` | docs only |
| G-COMPLY-VERSIONS | Pre-flight tool-version check in `compliance-check.sh` | — | `gap/g-comply-versions` | `scripts/`, `requirements-dev.txt` |

**Cross-sprint dependency:** G-SLOTS (#4) may unblock E2 integration tests → consider pulling into Sprint 5.

**G-COMPLY-VERSIONS scope:** parse `requirements-dev.txt`, compare pinned vs.
installed versions for each tool invoked by `scripts/compliance-check.sh`, log
expected/actual, and exit non-zero on drift (or record versions in the
Markdown report). Deferred from PR #35 (E3) review as a separate concern.

**G-INSTALL-DOC gating:** do not start until all deps are tested and confirmed on-Pi
(post-Sprint 6 + successful `scripts/compliance-check.sh` run). Current `docs/plan/install.md`
is stale: uses `venv` instead of `.venv`, unpinned `pip install`, `tflite-runtime` instead of
`ai_edge_litert`, and `curl -L` without SHA-256 for model downloads. Authoritative sources to
sync against: `install.sh`, `requirements.lock`, `requirements-ci.txt`, and the real imports
in `src/styler.py` / `src/isolator.py`.

---

## In-progress

| ID | Title | Branch | PR |
|---|---|---|---|
| T3 (final slice) | config_validator arg-type + styler no-any-return + compositor assignment | `sprint6/t3-final` | — |

---

## Done (recent, last 10)

Full history in `PLAN_HISTORY.md`.

| ID | Title | PR | Merged |
|---|---|---|---|
| **T3** (slice 2) | dict/Queue generics + `__future__` annotations + camera.py PLC0415 noqa | #39 | 2026-04-06 |
| **T3** (slice 1) | define_slots TypedDict + mypy.ini cleanup + LANCZOS codebase-wide + DisplayProtocol + Pillow/numpy in dev deps | #38 | 2026-04-05 |
| **T1** | Ruff autofix sweep (format + --fix, 45→32 lint) | #37 | 2026-04-05 |
| **E3** | scripts/compliance-check.sh (closes #26) | #35 | 2026-04-05 |
| **E4** | CI baselines → docs/ci-baseline.md (closes #27) | #36 | 2026-04-05 |
| **E2** | conftest.py hardware-dep stubs (closes #25) | #34 | 2026-04-05 |
| **E1** | Pin GH Actions to SHAs + Dependabot (closes #24) | #29 | 2026-04-05 |
| — | docs: kanban restructure + README | #28 | 2026-04-05 |
| CI-3 | security workflow (PR-3) | #23 | 2026-04-05 |
| CI-2 | lint + test workflows (PR-2) | #22 | 2026-04-05 |
| CI-1 | per-tool configs (PR-1) | #21 | 2026-04-05 |

---

## Ops / admin (not PRs)

- [ ] Branch protection on `main`: require signed commits, require PR reviews, require status checks (post-T6)
- [ ] Confirm GPG key with noreply UID is active for all committers
- [ ] Dependabot (pip ecosystem) — follow-up to E1, separate issue when E1 merges
