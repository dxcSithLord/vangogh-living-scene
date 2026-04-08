# Security Resource Limits

> Centralized reference for all hardcoded resource limits in the codebase.
> See SECURITY-POLICY.md for standards traceability.

## Application-level limits

| Limit | Value | Module | Constant | Standard | Purpose |
|-------|-------|--------|----------|----------|---------|
| Max input image dimension | 2048 px | `isolator.py` | `_MAX_INPUT_DIMENSION` | NIST SI-10 | Prevents memory exhaustion from oversized crops |
| Max image pixels (decompression bomb) | 25,000,000 | `compositor.py` | `Image.MAX_IMAGE_PIXELS` | NIST SI-10, SEC-14 | Pillow decompression bomb guard |
| Max slots JSON file size | 1,048,576 bytes (1 MB) | `slots.py` | `_MAX_SLOTS_FILE_BYTES` | OWASP A04, SEC-12 | Prevents resource exhaustion from oversized JSON |
| Camera consecutive error cap | 50 | `camera.py` | `MAX_CONSECUTIVE_ERRORS` | DISA-STIG V-222659, SEC-08 | Triggers backoff sleep instead of tight error loop |
| Camera backoff sleep | 30 s | `camera.py` | `BACKOFF_SLEEP_SECONDS` | DISA-STIG V-222659 | Cooldown after hitting error cap |

## Memory limits

| Limit | Value | Source | Purpose |
|-------|-------|--------|---------|
| RSS warning threshold | Configurable (`memory.rss_warning_mb`, default 460) | `config.yaml` | `_check_rss()` emits WARNING + security event on breach |
| Systemd `MemoryHigh` | 460 MB | `vangogh_scene.service` | Kernel memory pressure signal |
| Systemd `MemoryMax` | 500 MB | `vangogh_scene.service` | Hard OOM kill boundary |
| Core dump size | 0 | `vangogh_scene.service` (`LimitCORE=0`) | CIS L2: no core dumps to disk |

## Systemd resource controls

| Directive | Value | Standard |
|-----------|-------|----------|
| `MemoryMax` | 500M | CIS L2 |
| `MemoryHigh` | 460M | CIS L2 |
| `LimitCORE` | 0 | CIS L2 |
| `SystemCallArchitectures` | native | DISA-STIG |
| `DevicePolicy` | closed | DISA-STIG |
| `PrivateNetwork` | yes | CIS L2 |
| `WatchdogSec` | 300 | — |
| `RestartSec` | 10 | — |
| `StartLimitBurst` | 5 (in 300 s) | — |

## Journald limits

| Limit | Value | Source | Purpose |
|-------|-------|--------|---------|
| `SystemMaxUse` | 50 MB | `install.sh` (journald config) | Prevents SD card fill from logs (RG-07) |
