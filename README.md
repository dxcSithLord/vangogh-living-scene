# Van Gogh Living Scene

[![lint](https://github.com/dxcSithLord/vangogh-living-scene/actions/workflows/lint.yml/badge.svg?branch=main)](https://github.com/dxcSithLord/vangogh-living-scene/actions/workflows/lint.yml)
[![test](https://github.com/dxcSithLord/vangogh-living-scene/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/dxcSithLord/vangogh-living-scene/actions/workflows/test.yml)
[![security](https://github.com/dxcSithLord/vangogh-living-scene/actions/workflows/security.yml/badge.svg?branch=main)](https://github.com/dxcSithLord/vangogh-living-scene/actions/workflows/security.yml)
[![release](https://img.shields.io/badge/release-none-lightgrey)](https://github.com/dxcSithLord/vangogh-living-scene/releases)

A standalone Raspberry Pi Zero 2W application that detects a person or
animal entering a room, isolates them from the background, restyles the
subject as a Van Gogh brushstroke painting, and composites them into a
café-terrace scene on a 13.3" Inky Impression e-ink display.

Runs **fully offline** — no network required at runtime.

---

## How it works

```
IMX500 camera → on-sensor person/animal detection (NPU)
     → rembg (background removal)
     → Magenta Van Gogh style transfer (TFLite INT8)
     → composite onto café-terrace background
     → Inky Impression 13.3" e-ink display
```

Detection runs on the camera's onboard NPU, keeping the Pi Zero 2W's
512 MB of RAM free for the style-transfer pipeline. See
`docs/plan/architecture.md` for the full memory sequence.

## Hardware

| Component | Detail |
|-----------|--------|
| Raspberry Pi Zero 2W | RP3A0, 4× Cortex-A53 @ 1 GHz, 512 MB LPDDR2 |
| Raspberry Pi AI Camera | Sony IMX500, 12.3 MP, onboard NPU |
| Display | Pimoroni Inky Impression 13.3", 1600×1200, 7-colour e-ink |
| OS | Raspberry Pi OS Lite 64-bit (Bookworm), Python 3.13 |

Hardware prerequisites checklist: `docs/plan/prerequisites.md`.

## Status

Sprint 1–4 feature delivery: **complete**. Current focus is CI hardening
and enforcement — see `PROJECT_PLAN.md` for the active sprint and
`docs/plan/kanban.md` for the full backlog.

## Install

See `docs/plan/install.md` for apt/pip commands and model download URLs.
On-Pi full verification (once delivered) will be
`scripts/compliance-check.sh`.

---

## Documentation

**Top-level**

| File | Purpose |
|---|---|
| `PROJECT_PLAN.md` | Current sprint pointer + top-of-kanban snapshot |
| `PLAN_HISTORY.md` | Archive of merged PRs and completed sprint work |
| `ARCHITECTURE.md` | Living architecture document |
| `SECURITY-POLICY.md` | Standards traceability (NIST, OWASP, CIS, FIPS) |
| `CLAUDE.md` | Project coding rules and working agreements |

**`docs/plan/` — planning artefacts**

| File | Purpose |
|---|---|
| `kanban.md` | Canonical backlog, todo, in-progress, done |
| `sprints.md` | Sprint 1–4 definitions and test criteria |
| `architecture.md` | System diagram and memory-management sequence |
| `gap-analysis.md` | Source of gap-analysis issues (#3–#20) |
| `prerequisites.md` | Hardware prerequisites table |
| `install.md` | Install commands and model download URLs |
| `risks.md` | Known risks and mitigations |

**`docs/` — reference material**

| File | Purpose |
|---|---|
| `modules.md` | Per-module responsibilities (all 9 `src/` modules) |
| `models.md` | Model specs (detection, style, rembg) |
| `references.md` | External reference URLs |

---

## License

Not yet specified.
