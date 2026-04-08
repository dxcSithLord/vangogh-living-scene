# Installation Guide — Van Gogh Living Scene

## Prerequisites

- Raspberry Pi Zero 2W with Pi OS Lite 64-bit (Bookworm)
- Python 3.13+
- Internet access for initial apt package installation (see Offline Install
  for air-gapped deployment after apt setup)

## Online install (default)

Run on a Pi with network connectivity:

```bash
./install.sh
```

This performs all steps automatically:

1. **System packages** — `apt install` of `imx500-all`, `imx500-models`,
   `python3-picamera2`, `python3-pip`, `python3-venv`, `git`
2. **Python venv** — created with `--system-site-packages` (required to
   access apt-installed `picamera2`)
3. **Python packages** — hash-pinned install from `requirements.lock` using
   `pip install --require-hashes` (SEC-04, OWASP A08, FIPS 140-3)
4. **System user** — creates unprivileged `vangogh` user with `nologin` shell
5. **TFLite models** — downloaded with SHA-256 checksum verification (SEC-01)
6. **rembg model** — `u2net_human_seg` pre-downloaded (~176 MB, RG-04)
7. **Swap** — 512 MB swap file for memory pressure during style transfer
8. **Permissions** — config.yaml set to 0640, project dirs owned by `vangogh`
9. **systemd service** — installed and enabled (not auto-started)
10. **journald** — `SystemMaxUse=50M` to prevent SD card fill (RG-07)

Runtime dependencies are defined in `requirements.in` and compiled to
`requirements.lock` via `pip-compile --generate-hashes`. Key packages:

| Package | Version | Notes |
|---------|---------|-------|
| `ai-edge-litert` | >=2.1.3 | Successor to `tflite-runtime` |
| `rembg[cpu]` | >=2.0.74 | Background removal (ONNX, CPU-only) |
| `Pillow` | >=12.0 | Python 3.13 wheels + CVE fixes |
| `inky` | >=2.0 | Pimoroni e-ink display driver |
| `numpy` | >=2.2 | Required for Python 3.13 |
| `PyYAML` | >=6.0 | Config file parsing |

---

## Offline install (air-gapped Pi)

For deployment to a Pi with no network access after initial setup.

### Step 1: Install apt packages (requires network, one-time)

Before going air-gapped, the Pi must have system packages installed:

```bash
sudo apt update
sudo apt install -y \
    imx500-all imx500-models python3-picamera2 \
    python3-pip python3-venv git
```

### Step 2: Build the offline bundle (connected machine)

On any machine with internet access (x86_64 or aarch64):

```bash
scripts/bundle-offline.sh --output vangogh-offline-bundle.tar.gz
```

This downloads:
- All pip wheels for aarch64 from PyPI and piwheels
- TFLite style predict and transform models (SHA-256 verified)
- rembg `u2net_human_seg.onnx` model (RG-04: best-effort)
- Generates a `SHA256SUMS` manifest of all bundle contents

The script prints the tar archive's SHA-256 checksum for transfer verification.

**Cross-platform note:** When building on x86_64, the script uses
`pip download --platform linux_aarch64 --only-binary=:all:`. If any package
lacks a pre-built aarch64 wheel, the download fails with a clear error.
Building on an aarch64 machine avoids this limitation.

### Step 3: Transfer to the Pi

Copy the tar to the Pi via USB stick, SD card, or local network:

```bash
# Verify checksum after transfer
sha256sum vangogh-offline-bundle.tar.gz
# Compare with the checksum printed by bundle-offline.sh
```

### Step 4: Extract and install

On the Pi:

```bash
cd <checkout-dir>            # e.g. /home/vangogh/vangogh-living-scene
mkdir -p offline-bundle
tar xzf vangogh-offline-bundle.tar.gz -C offline-bundle/
./install.sh
```

`install.sh` auto-detects `offline-bundle/SHA256SUMS` and switches to offline
mode: verifies the bundle manifest, installs pip packages from local wheels
(`--no-index --find-links`), copies models from the bundle, and validates all
checksums. Apt packages are verified as present (not installed).

The bundle directory can also be specified via environment variable:

```bash
VANGOGH_OFFLINE_BUNDLE=/path/to/bundle ./install.sh
```

---

## Developer environment

For local development and running the compliance test suite:

```bash
scripts/dev-setup.sh
```

This creates a `.venv` with both runtime dependencies (hash-pinned from
`requirements.lock`) and dev tools (`requirements-dev.txt`). No models,
no systemd service, no system user.

After setup:

```bash
source .venv/bin/activate
pytest tests/                    # run tests
ruff check . && mypy src tools   # lint + type check
scripts/compliance-check.sh --report-only  # full compliance run
```

Dev tools (from `requirements-dev.txt`):

| Tool | Purpose |
|------|---------|
| `ruff` | Format + lint |
| `mypy` | Strict type checking |
| `bandit` | SAST security scanning |
| `pip-audit` | CVE dependency scanning |
| `yamllint` | YAML validation |
| `cyclonedx-bom` | SBOM generation |

---

## Security controls

| ID | Control | Mechanism |
|----|---------|-----------|
| SEC-01 | Model integrity | SHA-256 checksums verified on download and install |
| SEC-04 | Supply chain integrity | `pip install --require-hashes` from `requirements.lock` |
| SEC-10 | Core dump restriction | `ulimit -c 0` in `install.sh` (CIS L2) |
| SEC-13 | Config file permissions | `chmod 640 config/config.yaml` (NIST SC-28) |
| RG-04 | rembg model integrity | Best-effort — no upstream hash pinning available |

See `SECURITY-POLICY.md` for the full traceability matrix.

---

## Known issues

- **venv naming:** `install.sh` and `vangogh_scene.service` use `venv`;
  `compliance-check.sh` and `dev-setup.sh` use `.venv`. These are separate
  environments (production vs dev). A future card should align naming.
