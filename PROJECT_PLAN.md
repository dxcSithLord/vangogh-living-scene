# Van Gogh Living Scene — Project Plan

> **This file is the single source of truth for project status.**
> Sprint deliverables and test criteria: `docs/plan/sprints.md`.
> Architecture and design decisions: `ARCHITECTURE.md`.
> Security standards traceability: `SECURITY-POLICY.md`.

Version: 2.0
Last reviewed: 2026-04-01

Detail for each section lives in `docs/plan/`. Read only the file you need.

---

## Index

| Section | File |
|---------|------|
| Verified hardware/software assumptions (8 items) | `docs/plan/gap-analysis.md` |
| System diagram and memory management sequence | `docs/plan/architecture.md` |
| Sprint 1–4 deliverables and test criteria | `docs/plan/sprints.md` |
| Hardware prerequisites checklist | `docs/plan/prerequisites.md` |
| Install commands (apt, pip, model download) | `docs/plan/install.md` |
| Known risks and mitigations | `docs/plan/risks.md` |
| Security policy and standards traceability | `SECURITY-POLICY.md` |

---

## Current sprint

**Sprint 4 — Integration, service hardening, and final verification** — Done.

See `docs/plan/sprints.md` for deliverables and test criteria.

---

## Module status

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
