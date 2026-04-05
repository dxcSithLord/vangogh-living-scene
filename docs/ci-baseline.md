# CI Baseline — Van Gogh Living Scene

Captured:    2026-04-05 13:49 UTC
Commit:      `4b49174a9f9d3e9b1342e285a62430dbb906ff1a` (main)
Captured on: Linux 6.12.75+rpt-rpi-2712 aarch64 (Raspberry Pi, local `.venv`)

This document is a frozen snapshot of every CI tool's findings count
against `main`, taken with the tools pinned in `requirements-dev.txt`.
Sprint 6 triage cards (T1–T5) each own a subset of these findings;
T6 (flip `continue-on-error` → `false`) runs after the counts reach zero.

---

## Summary

| Tool | Count | Notes |
|------|------:|-------|
| ruff format | **11 files** | All in `src/` and `tests/` |
| ruff lint | **45 findings** | 15 rule codes; top rule = `PLC0415` (20 hits) |
| mypy strict | **23 errors** in 10 files | Many are missing stubs for hardware deps (`numpy`, `PIL`) |
| bandit (medium+) | **0** | — |
| pip-audit | **0 CVEs** | `requirements-ci.txt` clean |
| yamllint | **0** warnings | `.github/`, `config/`, `.yamllint` all clean |
| actionlint | **not run locally** | Not installed in `.venv`; covered by `security.yml` CI step |
| pytest (not hardware) | **blocked** | Pending #25 (E2) — test collection fails without hardware-dep stubs |
| pytest (hardware) | **blocked** | Same as above |
| test functions (static grep) | **47** | Across 8 test files — see detail below |

**Totals to triage in Sprint 6: 79 issues** (45 ruff + 23 mypy + 11 format files).

---

## Per-tool detail

### ruff format — 11 files

```
src/camera.py
src/compositor.py
src/config_validator.py
src/display.py
src/isolator.py
src/main.py
src/presence.py
src/slots.py
src/styler.py
tests/test_compositor.py
tests/test_slots.py
```

Fix mechanically: `ruff format .`.

### ruff lint — 45 findings (15 rules)

Grouped by rule code (descending):

| Count | Rule | Description |
|------:|------|-------------|
| 20 | PLC0415 | import-outside-top-level |
| 8  | F401    | unused-import *(autofix)* |
| 3  | I001    | unsorted-imports *(autofix)* |
| 2  | PLR0912 | too-many-branches |
| 2  | RUF001  | ambiguous-unicode (en-dash in strings) |
| 1  | B905    | zip-without-explicit-strict |
| 1  | E402    | module-import-not-at-top |
| 1  | E501    | line-too-long |
| 1  | PLR0915 | too-many-statements |
| 1  | PLR2004 | magic-value-comparison |
| 1  | RUF059  | unused-unpacked-variable |
| 1  | RUF100  | unused-noqa *(autofix)* |
| 1  | S110    | try-except-pass |
| 1  | T201    | `print` found |
| 1  | UP035   | deprecated-import *(autofix)* |

13 findings are ruff-autofixable (`--fix`), 3 more with `--unsafe-fixes`.

Findings by file (descending):

```
 6  tests/test_integration.py
 6  src/camera.py
 5  src/presence.py
 4  src/styler.py
 4  src/compositor.py
 3  tools/define_slots.py
 3  tests/test_camera.py
 2  tests/test_isolator.py
 2  tests/test_compositor.py
 2  src/main.py
 2  src/isolator.py
 2  src/display.py
 2  src/config_validator.py
 1  tests/test_config_validator.py
 1  tests/conftest.py
```

### mypy strict — 23 errors in 10 files

| Count | File |
|------:|------|
| 8 | src/display.py |
| 4 | src/camera.py |
| 2 | tools/define_slots.py |
| 2 | src/styler.py |
| 2 | src/presence.py |
| 2 | src/compositor.py |
| 1 | src/slots.py |
| 1 | src/main.py |
| 1 | src/isolator.py |
| 1 | src/config_validator.py |

Many errors are `import-not-found` for `numpy`, `PIL`, and other deps
that aren't in the dev-tool `.venv`. After #25 (E2) lands, reassess —
conftest stubs don't affect mypy, so these will still need `mypy.ini`
stub overrides. `mypy.ini` also reports unused sections
(`[mypy-tflite_runtime.*]`, `[mypy-tests.*]`) — clean up as part of T3.

### bandit — 0 findings (medium severity × medium confidence)

1,469 lines of code scanned across `src/` and `tools/`. Config
loaded from `.bandit` (YAML format since PR #23).

### pip-audit — 0 CVEs

`pip-audit -r requirements-ci.txt` returns "No known vulnerabilities".
Recapture when `requirements-ci.txt` or `requirements.lock` changes.

### yamllint — 0 warnings

Files scanned: all `.github/workflows/*.yml`, `.github/dependabot.yml`,
`config/*.yaml`, `.yamllint`. All clean.

### actionlint — not installed locally

`actionlint` is a Go binary, intentionally outside `requirements-dev.txt`
(per PR #23 rationale). CI coverage via `security.yml`'s `Actionlint
workflow check` step using pinned v1.7.12 binary + SHA256 verification.

### pytest — collection blocked

```
pytest tests/ --collect-only -m "not hardware"
  → collection errors (src/*.py imports hardware deps at module level)
```

This matches the known limitation documented in PR #22 and tracked
as issue #25 (E2). Test counts below come from static `grep -c
"def test_"` instead:

| File | tests |
|------|------:|
| tests/test_config_validator.py | 12 |
| tests/test_slots.py | 8 |
| tests/test_compositor.py | 6 |
| tests/test_integration.py | 6 |
| tests/test_security_log.py | 5 |
| tests/test_camera.py | 4 |
| tests/test_isolator.py | 3 |
| tests/test_styler.py | 3 |
| **Total** | **47** |

Recapture after #25 merges so real pytest collection counts and
coverage % land here.

> **Note:** `pytest` is not installed in `.venv` — it lives in
> `requirements-ci.txt`, not `requirements-dev.txt`. Intentional:
> dev `.venv` carries only lint/type/SAST tooling.

---

## Ancillary finding: ruff.toml `extend-exclude` gap

During capture, `ruff` over-counted findings 3× because it traversed
into `.claude/worktrees/*` (Claude Code agent worktrees). Current
`ruff.toml` excludes are:

```
extend-exclude = [ "venv", ".venv", "models", "assets" ]
```

Add `".claude"` to that list as part of T1 (or a separate tiny PR)
to prevent future double-counting. Affects bandit/mypy/yamllint
similarly if worktrees contain `src/`, `tools/`, `tests/` copies.

---

## How Sprint 6 uses this baseline

- **T1** — `ruff format .` + `ruff check --fix` → clears 11 format files + 13 autofixable lint findings (24 total).
- **T2** — ruff lint non-autofix → 32 remaining findings, split by rule family across small PRs.
- **T3** — mypy → 23 errors, split by module. Also clean up unused `mypy.ini` sections.
- **T4** — bandit → already clean, no work.
- **T5** — pip-audit → already clean, no work.
- **T6** — flip `continue-on-error: false` once T1–T3 drain to zero.

---

## Recapture

Run the command set below after any bulk src change, dep bump,
or new PR that adds/removes findings.

```bash
source .venv/bin/activate
git rev-parse HEAD
ruff format --check src tools tests
ruff check src tools tests --statistics
mypy src tools
bandit -c .bandit -r src tools --severity-level medium --confidence-level medium
pip-audit -r requirements-ci.txt
yamllint .github config .yamllint
# actionlint (if installed)
# pytest --collect-only -m "not hardware" (after #25 merges)
```
