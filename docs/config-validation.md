# Config Validation Rules

> Reference for all startup validation in `src/config_validator.py`.
> Standards: OWASP A05, NIST CM-6.

## Overview

Config is validated once at startup via `validate_or_exit()`. All errors
are collected and logged before `sys.exit(1)`, so operators can fix
everything in one pass. A `CONFIG_VALIDATION_FAIL` security event is
emitted on failure.

Two public functions:

- `validate_config(config, project_root)` — returns `list[str]` of errors
- `validate_or_exit(config, project_root)` — calls the above, exits on error

## Range-constrained numeric fields

| Key | Type | Min | Max |
|-----|------|-----|-----|
| `display.width` | int | 1 | 10000 |
| `display.height` | int | 1 | 10000 |
| `display.saturation` | float | 0.0 | 1.0 |
| `detection.confidence` | float | 0.0 | 1.0 |
| `presence.entering_frames` | int | 1 | 1000 |
| `presence.exiting_frames` | int | 1 | 1000 |
| `presence.ghost_ttl_seconds` | float | 0.0 | 86400.0 |
| `style.content_size` | int | 1 | 4096 |
| `style.predict_size` | int | 1 | 4096 |
| `style.num_threads` | int | 1 | 16 |
| `memory.rss_warning_mb` | int | 1 | 8192 |

Int values are accepted where float is expected (auto-converted).

## Required non-empty strings

| Key |
|-----|
| `detection.model` |
| `paths.background` |
| `paths.slots` |
| `paths.style_predict_model` |
| `paths.style_transform_model` |
| `paths.style_image` |
| `rembg.model_name` |
| `logging.level` |

## Required non-empty lists

| Key |
|-----|
| `detection.labels` |

## Logging level validation

`logging.level` must be one of: `CRITICAL`, `DEBUG`, `ERROR`, `INFO`, `WARNING`.

## Path existence checks

These paths are resolved relative to the project root and must point to
existing files at startup:

| Key | Typical value |
|-----|---------------|
| `paths.background` | `assets/backgrounds/van_gogh_cafe.jpg` |
| `paths.slots` | `assets/slots/cafe_terrace_slots.json` |
| `paths.style_predict_model` | `models/style/style_predict_int8.tflite` |
| `paths.style_transform_model` | `models/style/style_transform_int8.tflite` |
| `paths.style_image` | (Van Gogh style reference image) |

`detection.model` is checked as an absolute path (system-level `.rpk` file).
