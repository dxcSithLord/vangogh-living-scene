# Plan History — Van Gogh Living Scene

> Append-only archive of completed work. Not loaded by default.
> Current status lives in `PROJECT_PLAN.md` and `docs/plan/kanban.md`.

---

## Merged PRs

| PR | Title | Merged | Closes |
|---|---|---|---|
| #29 | ci: pin workflow actions to commit SHAs + add Dependabot (PR-4) | 2026-04-05 | #24 |
| #28 | docs: restructure plan to kanban model + add README | 2026-04-05 | — |
| #23 | ci: add security workflow (PR-3) | 2026-04-05 | — (Related #17) |
| #22 | ci: add lint and test workflows (PR-2) | 2026-04-05 | — (Related #17) |
| #21 | ci: add per-tool configs (PR-1) | 2026-04-05 | #16 |
| #17 (issue) | [D15] No GitHub Actions workflows committed | closed 2026-04-05 | via #21+#22+#23 |
| #2 | add gitkeep for empty directory | 2026-04-04 | — |
| #1 | Configure Mend Bolt for GitHub | 2026-04-02 | — |

---

## Sprint 1–4 + 2.5 module delivery (archived 2026-04-05)

All modules below reached **Done** status prior to the CI initiative.

| Module | Sprint | Status |
|--------|--------|--------|
| `config.yaml` | 1 | Done |
| `src/slots.py` | 1 | Done |
| `src/display.py` | 1 | Done |
| `src/compositor.py` | 1 | Done |
| `tools/define_slots.py` | 1 | Done |
| `src/camera.py` | 2 | Done |
| `src/presence.py` | 2 | Done |
| `install.sh` (SHA-256 checksums, core dump, permissions) | 2.5 | Done |
| `requirements.txt` (Py 3.13 upgrade, hash pinning) | 2.5 | Done |
| `requirements.lock` (SHA-256 hashed deps) | 2.5 | Done |
| `src/config_validator.py` (new) | 2.5 | Done |
| `src/camera.py` (error loop cap) | 2.5 | Done |
| `src/slots.py` (JSON size check) | 2.5 | Done |
| `src/compositor.py` (pixel limit, magic byte check) | 2.5 | Done |
| `tools/define_slots.py` (input validation) | 2.5 | Done |
| All `.py` (PEP 604 type hints, path sanitisation) | 2.5 | Done |
| `src/isolator.py` | 3 | Done |
| `src/styler.py` | 3 | Done |
| `src/security_log.py` (new) | 3 | Done |
| `tests/*` (new) | 3 | Done |
| `src/main.py` | 4 | Done |
| `vangogh_scene.service` (hardened) | 4 | Done |
| `tests/test_integration.py` (new) | 4 | Done |

Sprint definitions and test criteria remain in `docs/plan/sprints.md`.
