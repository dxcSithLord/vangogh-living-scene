# Sprint Plan

## Sprint 1 — Display and slot foundation

**Goal:** Display the background on the Inky. Define and persist slot positions.

**Deliverables:**
- `install.sh` — installs all apt and pip dependencies, downloads models
- `requirements.txt`
- `config/config.yaml`
- `src/display.py` — thin wrapper around `inky` library
- `src/slots.py` — loads slot definitions from JSON; validates against image dimensions
- `src/compositor.py` — loads background, pastes slot overlays for debug view
- `tools/define_slots.py` — interactive CLI: load image, click to place named slots, saves JSON
- `assets/slots/cafe_terrace_slots.json` — initial slot definitions

**Test:** Run `python tools/define_slots.py assets/backgrounds/van_gogh_cafe.jpg`
on a desktop, define 3 slots, verify JSON output. Then SSH to Pi, run
`python src/compositor.py --debug` and confirm background renders on Inky.

**No camera required for this sprint.**

---

## Sprint 2 — Camera and presence state machine

**Goal:** Detect people entering and exiting via IMX500. State machine
produces clean ENTERED/EXITED events.

**Deliverables:**
- `src/camera.py` — `picamera2` + `IMX500` initialisation; detection callback;
  delivers bounding-box crops to a queue
- `src/presence.py` — state machine (ABSENT → ENTERING → PRESENT → EXITING
  → ABSENT); debounce logic; ghost re-entry cache

**Test:** Run `python src/camera.py` on Pi with camera attached. Confirm
`ENTERED` events logged when walking past, `EXITED` events after leaving.
Confirm no false triggers from shadows or brief occlusions.

**Key config parameters to validate:**
- `detection_confidence` (start at 0.6, tune down if missing detections)
- `entering_frames` (start at 8 at 5 fps = 1.6 s confirmation window)
- `exiting_frames` (start at 30 at 5 fps = 6 s grace period)

---

## Sprint 2.5 — Security hardening retrofit

**Goal:** Harden all existing code and build tooling against security audit
findings. No module behaviour changes. Each item is one PR.

**Standards applied:** NIST SP 800-53, OWASP Top 10 (2021), CIS L2,
DISA-STIG, FIPS 140-3, PEP 604. Full traceability in `SECURITY-POLICY.md`.

### User stories

| ID | User story | File(s) | Standard |
|----|-----------|---------|----------|
| SEC-01 | As an operator, I need model checksums verified after download so tampered models cannot load | `install.sh` | NIST SI-7, OWASP A08, FIPS 140-3 |
| SEC-02 | As an operator, I need config validated at startup so malformed values fail fast | new `src/config_validator.py` | OWASP A05, NIST CM-6 |
| SEC-04 | As an operator, I need pip packages hash-pinned so supply chain attacks are blocked | `requirements.txt` | OWASP A08, FIPS 140-3 |
| SEC-05 | As an operator, I need Pillow floor bumped to >=12.0 to exclude known CVEs | `requirements.txt` | OWASP A06 |
| SEC-08 | As an operator, I need error loops bounded so hardware faults don't exhaust resources | `src/camera.py` | DISA-STIG V-222659 |
| SEC-09 | As an operator, I need slot tool input validated so invalid dimensions are rejected | `tools/define_slots.py` | DISA-STIG V-222612 |
| SEC-10 | As an operator, I need core dumps restricted on 512 MB device | `install.sh` | CIS L2 |
| SEC-11 | As a developer, I need type hints consistent (PEP 604) across all modules | All `.py` files | PEP 604 |
| SEC-12 | As an operator, I need JSON file size checked before parsing to prevent resource exhaustion | `src/slots.py` | OWASP A04 |
| SEC-13 | As an operator, I need config file permissions restricted to owner/group | `install.sh` | NIST SC-28 |
| SEC-14 | As an operator, I need image pixel limits explicit to prevent decompression bombs | `src/compositor.py` | NIST SI-10 |
| SEC-15 | As an operator, I need error messages sanitised so internal paths are not exposed | All modules | DISA-STIG V-222602 |
| SEC-16 | As an operator, I need image file type validated before loading | `src/compositor.py` | DISA-STIG V-222577 |

### Test criteria

- `install.sh` with a corrupted model file rejects with checksum error
- `config_validator.py` with invalid config exits with clear error message
- `camera.py` stops tight-looping after 50 consecutive errors
- `define_slots.py` rejects `width=-100` with a clear error
- `slots.py` rejects a JSON file larger than 1 MB
- `compositor.py` rejects a `.txt` file renamed to `.png`

---

## Sprint 3 — Isolation, style transfer, security logging, and tests

**Goal:** Given a crop, produce a styled RGBA figure suitable for compositing.
Add security audit logging and a test suite.

### Original deliverables

- `src/isolator.py` — wraps rembg with `u2net_human_seg`; accepts PIL Image,
  returns RGBA PIL Image
- `src/styler.py` — wraps TFLite two-stage pipeline; accepts RGBA PIL Image
  and pre-computed style bottleneck; returns styled RGBA PIL Image with alpha
  preserved; manages interpreter lifecycle to control RAM

### Security deliverables

| ID | User story | File(s) | Standard |
|----|-----------|---------|----------|
| SEC-06 | As an operator, I need security events logged to a dedicated audit logger | new `src/security_log.py` | OWASP A09, NIST AU-3 |
| SEC-07 | As a developer, I need unit tests for all Sprint 1–2.5 modules | new `tests/` directory | NIST SA-11 |

### Test suite (SEC-07)

- `tests/test_config_validator.py` — valid config, missing keys, bad types,
  bad ranges, missing paths
- `tests/test_slots.py` — valid JSON, oversized JSON, negative coords,
  out-of-bounds slots
- `tests/test_camera.py` — error loop cap (mock camera hardware)
- `tests/test_compositor.py` — magic byte rejection, pixel limit enforcement
- `tests/test_isolator.py` — basic smoke test with small image
- `tests/test_styler.py` — basic smoke test with small image
- `tests/conftest.py` — shared fixtures (sample config, temp directories)

### Test criteria

- `python src/styler.py --input test_photo.jpg` on Pi: measure wall-clock
  time and peak RSS with `/usr/bin/time -v`. Verify styled PNG looks correct.
  Verify memory returns to baseline after completion.
- `pytest tests/` passes with 0 failures
- Security logger emits structured events to both journald and a configurable
  file path
- **RAM safety check:** If peak RSS during combined rembg + TFLite exceeds
  480 MB, switch rembg model to `silueta` and re-test.

---

## Sprint 4 — Integration, service hardening, and final verification

**Goal:** Full end-to-end pipeline running as a hardened systemd service.

### Original deliverables

- `src/main.py` — event loop; wires camera queue → presence state machine →
  pipeline (isolate → style → composite → display); handles ENTERED/EXITED.
  Must call `config_validator` at startup and initialise the security logger.
- `vangogh_scene.service` — systemd unit file
- `ARCHITECTURE.md` — living architecture document (final update)
- Full integration test: walk past camera, verify display updates within
  expected time; walk away, verify display reverts

### Security deliverables

| ID | User story | File(s) | Standard |
|----|-----------|---------|----------|
| SEC-03 | As an operator, I need the systemd service fully sandboxed | `vangogh_scene.service` | CIS L2, DISA-STIG |

### Systemd hardening directives (SEC-03)

```ini
[Service]
User=vangogh
Group=vangogh
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictNamespaces=yes
RestrictRealtime=yes
MemoryDenyWriteExecute=yes
ReadWritePaths=/var/log/vangogh
ReadOnlyPaths=/home/vangogh/vangogh-living-scene
LimitCORE=0
Restart=on-failure
RestartSec=10
WatchdogSec=300
```

**Target:** `systemd-analyze security vangogh_scene.service` score < 4.0

### Additional Sprint 4 tasks

- `install.sh` update: create `vangogh` system user, set directory permissions,
  install service file
- `SECURITY-POLICY.md` — final status update on all SEC-XX items
- `tests/test_integration.py` — end-to-end test with mocked hardware
- Configure journald `SystemMaxUse=50M` to prevent log-driven SD card fill (RG-07)
