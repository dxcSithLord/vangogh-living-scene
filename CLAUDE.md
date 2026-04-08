# CLAUDE.md — Van Gogh Living Scene

## What this project is

A standalone Python application on a Raspberry Pi Zero 2W that detects people
or animals entering a room (Sony IMX500 onboard NPU), removes their background
(rembg), applies Van Gogh brushstroke style (Magenta TFLite INT8), composites
them into a café background, and displays the result on a Pimoroni Inky
Impression 13.3" e-ink display. Runs **offline, no network required at runtime**.

---

## Hardware

| Component | Detail |
|-----------|--------|
| Raspberry Pi Zero 2W | RP3A0, 4× Cortex-A53 @ 1 GHz, 512 MB LPDDR2 |
| Raspberry Pi AI Camera | Sony IMX500, 12.3 MP, onboard NPU |
| CSI cable | 22-pin to 15-pin adapter (required for Zero 2W) |
| Display | Pimoroni Inky Impression 13.3", 1600×1200, 7-colour e-ink |
| OS | Raspberry Pi OS Lite 64-bit (Bookworm) |

---

## Repository structure

```
VanGaugh/
├── CLAUDE.md                    ← this file
├── ARCHITECTURE.md              ← living architecture doc (update each sprint)
├── SECURITY-POLICY.md           ← standards traceability (NIST, OWASP, CIS, FIPS)
├── PROJECT_PLAN.md              ← index — see docs/plan/ for detail
├── README.md
├── requirements.txt             ← human-readable dependency pins
├── requirements.in              ← source pins for pip-compile
├── requirements.lock            ← SHA-256 hash-pinned lockfile
├── install.sh                   ← production installer (online + offline modes)
├── vangogh_scene.service
├── config/
│   └── config.yaml
├── assets/
│   ├── backgrounds/
│   │   └── cafe_terrace.png     ← 1600×1200, user-supplied
│   └── slots/
│       └── cafe_terrace_slots.json
├── models/
│   └── style/
│       ├── style_predict_int8.tflite
│       └── style_transform_int8.tflite
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── camera.py
│   ├── isolator.py
│   ├── styler.py
│   ├── compositor.py
│   ├── display.py
│   ├── presence.py
│   ├── slots.py
│   └── config_validator.py
├── scripts/
│   ├── bundle-offline.sh        ← offline bundle builder (air-gapped deploy)
│   ├── dev-setup.sh             ← developer environment setup
│   └── compliance-check.sh      ← CI/dev compliance runner
├── tools/
│   └── define_slots.py
└── docs/
    ├── modules.md               ← module responsibilities (all 9 modules)
    ├── models.md                ← model specs (detection, style, rembg)
    ├── references.md            ← external reference URLs
    └── plan/
        ├── gap-analysis.md      ← 8 verified assumptions from research
        ├── architecture.md      ← system diagram + memory sequence
        ├── sprints.md           ← Sprint 1–4 deliverables and test criteria
        ├── prerequisites.md     ← hardware prerequisites table
        ├── install.md           ← apt/pip commands, model download URLs
        └── risks.md             ← known risks table
```

---

## Where to find details

| Topic | File |
|-------|------|
| Module responsibilities (what each .py does) | `docs/modules.md` |
| Model specs (input shapes, sizes, run frequency) | `docs/models.md` |
| External reference URLs | `docs/references.md` |
| Verified hardware/software assumptions | `docs/plan/gap-analysis.md` |
| System diagram and memory management sequence | `docs/plan/architecture.md` |
| Sprint deliverables and test criteria | `docs/plan/sprints.md` |
| Hardware prerequisites checklist | `docs/plan/prerequisites.md` |
| Install process (online, offline, dev) and model URLs | `docs/plan/install.md` |
| Known risks and mitigations | `docs/plan/risks.md` |
| Security policy and standards traceability | `SECURITY-POLICY.md` |

---

## Working rules — read before touching any file

### Before writing code

1. Read the file you are about to change. Never modify a file you have not
   opened and read in the current session.
2. Check ARCHITECTURE.md for the current state of the module you are changing.
3. Confirm the sprint you are working on matches the plan in `docs/plan/sprints.md`.
4. If a change touches more than one module, state the plan and wait for
   confirmation before writing code.

### Code standards

- Python 3.13+. Type hints on all function signatures. Use `X | None` (PEP 604),
  not `Optional[X]`.
- Line length: 100 characters.
- Formatting: Black-compatible (4-space indent, no trailing whitespace).
- Imports: stdlib → third-party → local, separated by blank lines.
- No bare `except:` clauses. Catch specific exceptions.
- All file I/O uses `pathlib.Path`, not string concatenation.
- Config values are never hardcoded. All tuneable values come from `config.yaml`
  via the config object passed into each module.
- Logging via the standard `logging` module. No `print()` in production paths.
  Log level is configurable.

### Security and defensive coding

- Validate all config values at startup (type, range, path existence). Fail
  fast with a clear error if config is malformed.
- No shell=True in subprocess calls.
- Image inputs are validated (format, dimensions) before processing.
- Temporary files use `tempfile` and are cleaned up in `finally` blocks.

### Bash script standards

All bash scripts (`install.sh`, `scripts/*.sh`) should comply with
(tracked in kanban — `install.sh` `umask 0077` outstanding):

- `set -euo pipefail` and `umask 0077` (CIS L2)
- Input validation on all arguments and paths (DISA-STIG V-222602)
- SHA-256 checksum verification for all downloaded/transferred artifacts
  (NIST SI-7, FIPS 140-3)
- No `eval`, no unquoted expansions, no `shell=True` equivalents
- `curl` calls must use `--fail` (`-f`) to abort on HTTP errors
- `pip install` must use `--require-hashes` from lockfiles — never
  `pip install --upgrade pip` in hash-pinned environments (OWASP A08)
- All scripts must pass `shellcheck` with no warnings
- Standards header comment referencing applicable controls

### Memory management (critical on 512 MB device)

- rembg session is loaded once at startup and kept open (reloading costs 5–10s).
- TFLite interpreter is created per-inference and explicitly deleted afterward
  with `gc.collect()`. Do not keep it alive between subjects.
- Log RSS after each major stage in debug mode to track memory.
- If RSS approaches 460 MB, log a WARNING. The system has ~50 MB headroom
  before OOM.

### Simplicity rule

Make every change as small as possible. One concern per PR. If a change is
getting large, stop and ask for a plan review. Complexity is the enemy on
constrained hardware.

---

## Current sprint

See `PROJECT_PLAN.md` for current sprint and module status.
