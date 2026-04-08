# Kanban — Van Gogh Living Scene

> Canonical backlog. Columns move left→right as work progresses.
> Session restart (orientation): read this file plus `PROJECT_PLAN.md`.
> Before making code changes: confirm the sprint matches
> `docs/plan/sprints.md` per CLAUDE.md "Before writing code" rule #3.

Last reviewed: 2026-04-08 (Sprint 7: all P7 doc cards done; G-INSTALL-UMASK remains)

---

## Definition of Done (applies to every card)

- [ ] Branch pushed with **signed commits** (GPG, noreply UID)
- [ ] PR opens with `Closes #N` for every issue the card resolves
- [ ] CI workflows green (all checks are blocking)
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
| ruff lint findings | 45 | 0 | −45 |
| mypy strict errors | 23 | 0 | −23 |
| bandit (medium+) | 0 | 0 | — |
| pip-audit CVEs | 0 | 0 | — |

### Status

| ID | Title | Status | PRs |
|---|---|---|---|
| T1 | Ruff autofix (format + --fix safe rules) | ✅ Done | #37 |
| T2 | Ruff lint (non-autofix) — all 29 findings cleared | ✅ Done | #41 |
| T3 | Mypy strict fixes — per module | ✅ Done | #38, #39, #40 |
| T4 | Bandit findings — by severity/module | ✅ Done (already clean per baseline) | — |
| T5 | Pip-audit CVE dep bumps | ✅ Done (already clean per baseline) | — |
| T6 | Flip continue-on-error → false across all workflows | ✅ Done | #42 |

### T6 scope

Flip `continue-on-error: true` → `false` in all CI workflow steps now that
ruff format (0), ruff lint (0), and mypy strict (0) are all clean.

---

## Current sprint: **Sprint 7 — Gap backlog**

### Priority scheme

| Level | Meaning | Guidance |
|-------|---------|----------|
| **P1** | Startup blocker | App cannot run. Fix before any integration work. |
| **P2** | Runtime bug | Incorrect behaviour affecting correctness or performance. |
| **P3** | Safety / memory | Risk of OOM or resource exhaustion on 512 MB device. |
| **P4** | Security compliance | Audit-required event or control not yet wired up. |
| **P5** | Verification | Read-only investigation; may spawn follow-up cards. |
| **P6** | Tooling hardening | CI/script improvements; no runtime impact. |
| **P7** | Documentation | Docs-only fixes; no code or runtime impact. |
| **P8** | Gated / deferred | Blocked on external prerequisite (e.g. on-Pi run). |

New cards should be assigned a priority level using this scheme.
Cards at the same level can run in parallel; work lower levels after higher.

### Backlog (ordered by priority)

| Pri | ID | Title | Issues | Branch | Module(s) |
|---|---|---|---|---|---|
| ~~P1~~ | ~~G-SLOTS~~ | ~~Missing slots JSON~~ | ~~#4~~ | ✅ Done (#43) | — |
| ~~P2~~ | ~~G-GHOST~~ | ~~Ghost cache refresh + skip logic~~ | ~~#6 #7~~ | ✅ Done (#44) | — |
| ~~P3~~ | ~~G-RSS~~ | ~~Enforce `memory.rss_warning_mb` in main loop~~ | ~~#8~~ | ✅ Done (#45) | — |
| ~~P4~~ | ~~G-CONFIG-EVT~~ | ~~Emit `CONFIG_VALIDATION_FAIL` security event + fix init order~~ | ~~#18~~ | ✅ Done (#46) | — |
| ~~P5~~ | ~~G-VERIFY~~ | ~~Verification tasks (read-only)~~ | ~~#11 #13 #20~~ | ✅ Done (see notes) | — |
| ~~P6~~ | ~~G-COMPLY-VERSIONS~~ | ~~Pre-flight tool-version check~~ | — | ✅ Closed (redundant, see notes) | — |
| ~~P7~~ | ~~G-DOC~~ | ~~Docs cleanup (omnibus or per-issue)~~ | ~~#3 #5 #9 #10 #12 #14 #15 #19~~ | ✅ Done (#49) | — |
| ~~P7~~ | ~~G-DOC-ARCH~~ | ~~Update ARCHITECTURE.md — ghost cache, RSS checks, fast path, error recovery~~ | — | ✅ Done (#50) | — |
| ~~P7~~ | ~~G-DOC-MODULES~~ | ~~Update modules.md — slots API, GhostCache, EventCallback, DisplayProtocol~~ | — | ✅ Done (#51) | — |
| ~~P7~~ | ~~G-DOC-SECURITY~~ | ~~Security reference docs — event catalog, validation rules, resource limits~~ | — | ✅ Done (#52) | — |
| **P6** | G-INSTALL-UMASK | Add `umask 0077` to `install.sh` (CIS L2 compliance) | — | `gap/g-install-umask` | `install.sh` |
| ~~P8~~ | ~~G-INSTALL-DOC~~ | ~~Offline install pipeline + refresh `docs/plan/install.md`~~ | — | ✅ Done (#47) | — |

### Card notes

**G-SLOTS (P1):** `cafe_terrace_slots.json` does not exist. `config_validator.py`
calls `sys.exit(1)` at startup. Complete blocker for any runtime or integration testing.

**G-GHOST (P2):** Two bugs — #6: `_ghost.store()` only fires on EXITING→ABSENT,
so the cached crop is stale if the subject was present for minutes. #7: `main.py`
runs full isolator+styler on cache hit — zero performance benefit from the cache.

**G-RSS (P3):** `main.py` logs RSS at multiple stages but never compares against
the configured 460 MB threshold. Only `styler.py` warns. On a 512 MB device with
~50 MB headroom, the main loop must also enforce the threshold.

**G-CONFIG-EVT (P4):** Two-part fix — (1) `validate_or_exit()` never calls
`log_security_event()`, and (2) security logger initialises *after* config
validation in `main.py`, so the event would fail even if emitted.

**G-VERIFY (P5):** Read-only investigation, 2026-04-07:
- #13: StartLimitBurst=5/300s verified in service file and ARCHITECTURE.md. ✅ Closed.
- #20: SEC-14 (MAX_IMAGE_PIXELS=25M) and SEC-16 (magic-byte validation) both
  confirmed in compositor.py:16–51. ✅ Closed.
- #11: sample_config labels `["person","cat","dog"]` missing `"bird","horse"`
  from production config. Follow-up fix needed (minor, test-only).

**G-COMPLY-VERSIONS (P6):** Closed as redundant. `requirements-dev.txt` header
states dev tools are "Not installed on the target Pi." The compliance script
already validates tool presence implicitly — if a tool is missing its check
fails. A pre-flight version check adds no value: on the Pi the tools aren't
installed; in CI the workflows install them from `requirements-dev.txt`; on dev
machines the checks themselves validate behaviour. The real gap is the offline
install pipeline — folded into G-INSTALL-DOC (see expanded scope below).

**G-DOC-ARCH (P7):** ARCHITECTURE.md has several gaps from recent code changes:
(1) Ghost cache dual-system not explained — `presence.py` maintains `_GhostCache`
(raw crops), `main.py` maintains `_last_styled` (styled images); interaction
between the two is undocumented. (2) `_check_rss()` instrumentation points added
in G-RSS PR #45 not reflected. (3) `ghost_hit` fast path that skips
isolator+styler not documented. (4) Error recovery behaviour (slot release on
pipeline failure) not described. (5) `docs/plan/architecture.md` diagram still
says `tflite-runtime` but code uses `ai_edge_litert`. Also update #9 (D7) note
— RSS is now enforced in main loop, not just styler.

**G-DOC-MODULES (P7):** `docs/modules.md` is behind current code:
(1) `slots.py` section is minimal — missing `free_count`, `get_slot()`,
`all_slots`, occupancy state machine. (2) `_GhostCache` class in `presence.py`
not mentioned — dual-cache architecture needs explanation. (3) `EventCallback`
type alias (includes `ghost_hit` param) not documented. (4) `DisplayProtocol`
structural protocol in `display.py` not documented. (5) `config_validator.py`
has two public functions (`validate_config` returns errors, `validate_or_exit`
calls `sys.exit`) — only `validate_or_exit` is mentioned.

**G-DOC-SECURITY (P7):** Security-relevant details are scattered across code
with no central reference. Create three docs:
(1) `docs/security-events.md` — catalog all 6 `SecurityEvent` enum values
(`CONFIG_VALIDATION_FAIL`, `CHECKSUM_MISMATCH`, `ERROR_THRESHOLD_BREACH`,
`BOUNDS_VIOLATION`, `INVALID_FILE_TYPE`, `FILE_SIZE_EXCEEDED`), when each is
emitted, and severity levels from `_EVENT_SEVERITY`.
(2) `docs/config-validation.md` — document all validation rules from
`config_validator.py` (12 range checks, 6 required strings, 5 path checks,
valid log levels).
(3) `docs/security-limits.md` — centralize resource limits currently scattered:
`isolator.py:_MAX_INPUT_DIMENSION=2048`, `slots.py:_MAX_SLOTS_FILE_BYTES=1MB`,
`compositor.py:MAX_IMAGE_PIXELS=25M`.

**G-INSTALL-DOC (P8):** Expanded scope (absorbs G-COMPLY-VERSIONS rationale).
Gated — do not start until all deps are tested and confirmed on-Pi.

Two parts:
(1) **Offline install pipeline design** — document (and optionally script) the
air-gapped deployment workflow:
  - Connected system: `pip download -r requirements.lock -d ./pkg-cache/`
  - Bundle: tar the package cache + model files + checksums (SHA-256 manifest)
  - Transfer: physical media to the disconnected Pi
  - Verify: validate SHA-256 checksums of the tar contents before install
  - Install: `pip install --no-index --find-links=./pkg-cache/ -r requirements.lock`
  - Same pattern applies for dev tools if compliance runs are needed on-Pi

(2) **Refresh `docs/plan/install.md`** — current doc is stale: uses `venv`
instead of `.venv`, unpinned `pip install`, `tflite-runtime` instead of
`ai_edge_litert`, and `curl -L` without SHA-256 for model downloads.
Authoritative sources to sync against: `install.sh`, `requirements.lock`,
`requirements-ci.txt`, and the real imports in `src/styler.py` /
`src/isolator.py`.

---

## In-progress

(none)

---

## Done (recent, last 10)

Full history in `PLAN_HISTORY.md`.

| ID | Title | PR | Merged |
|---|---|---|---|
| **G-DOC-SECURITY** | Security reference docs — event catalog, validation rules, resource limits | #52 | 2026-04-08 |
| **G-DOC-MODULES** | modules.md refresh — slots API, GhostCache, EventCallback, DisplayProtocol | #51 | 2026-04-08 |
| **G-DOC-ARCH** | ARCHITECTURE.md refresh — ghost cache, RSS, fast path, error recovery | #50 | 2026-04-08 |
| **G-DOC** | Docs cleanup: 8 gap-analysis issues (closes #3,#5,#9,#10,#12,#14,#15,#19) | #49 | 2026-04-08 |
| **G-INSTALL-DOC** | Offline install pipeline + dev setup + docs refresh | #47 | 2026-04-08 |
| **G-COMPLY-VERSIONS** | Closed as redundant — folded into G-INSTALL-DOC | — | 2026-04-07 |
| **G-VERIFY** | Verification tasks: #13 ✅ #20 ✅ closed, #11 spawns follow-up | — | 2026-04-07 |
| **G-CONFIG-EVT** | Emit CONFIG_VALIDATION_FAIL + fix init order (closes #18) | #46 | 2026-04-07 |
| **G-RSS** | Enforce rss_warning_mb threshold in main loop (closes #8) | #45 | 2026-04-07 |
| **G-GHOST** | Ghost cache refresh + skip pipeline on re-entry (closes #6, #7) | #44 | 2026-04-06 |
| **G-SLOTS** | Initial cafe_terrace_slots.json (closes #4) | #43 | 2026-04-06 |
| **T6** | Flip continue-on-error → false across all CI workflows | #42 | 2026-04-06 |
| **T2** | Clear all 29 ruff lint findings (PLC0415 per-file-ignores, PLR thresholds, single-hit fixes) | #41 | 2026-04-06 |
| **T3** (final) | config_validator fail-fast guard + styler ndarray annotation + compositor Image.open split | #40 | 2026-04-06 |
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
