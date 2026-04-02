# Security Policy — Van Gogh Living Scene

> Living document. Updated each sprint alongside ARCHITECTURE.md.

## Scope

This system is an **offline embedded IoT device** (Raspberry Pi Zero 2W).
It has no network connectivity at runtime, no user authentication, and no
cryptographic operations during normal operation. The attack surface is
limited to:

- **Build time**: model downloads, pip package installation
- **Physical access**: SD card, GPIO, CSI camera port
- **Input data**: camera frames (untrusted), config files (trusted), slot
  JSON (trusted)

---

## Applicable standards

| Standard | Controls applied |
|----------|-----------------|
| NIST SP 800-53 Rev 5 | SI-7, CM-6, AU-3, SA-11, SC-28, SI-10 |
| OWASP Top 10 (2021) | A04, A05, A06, A08, A09 |
| CIS Benchmark Level 2 (Debian) | Core dump restriction, systemd hardening |
| DISA-STIG (Application Security) | V-222577, V-222602, V-222612, V-222659 |
| FIPS 140-3 | Build-time integrity only (see below) |
| PEP 604 | Type hint consistency (code quality) |

---

## FIPS 140-3 applicability statement

This system contains **no cryptographic modules at runtime**. FIPS 140-3
applicability is limited to build-time integrity verification:

| Area | FIPS 140-3 status | Detail |
|------|-------------------|--------|
| Model download integrity | **Applicable** | SHA-256 checksums in `install.sh` (SEC-01) |
| Package integrity | **Applicable** | pip `--require-hashes` with SHA-256 (SEC-04) |
| Data at rest encryption | **N/A** | No sensitive data stored. Device is offline, single-purpose art display. |
| Swap encryption | **N/A** | Swap contains transient image processing data only. No PII, no credentials. |
| TLS/network encryption | **N/A** | No network connectivity at runtime. |

---

## Traceability matrix

| ID | Finding | Severity | Standard(s) | Sprint | Status |
|----|---------|----------|-------------|--------|--------|
| SEC-01 | Model download integrity — SHA-256 checksum verification | High | NIST SI-7, OWASP A08, FIPS 140-3 | 2.5 | **Done** |
| SEC-02 | Config validation — startup type/range/path checks | High | OWASP A05, NIST CM-6 | 2.5 | **Done** |
| SEC-03 | Systemd service hardening — full sandbox directives | High | CIS L2, DISA-STIG | 4 | **Done** |
| SEC-04 | pip hash pinning — `requirements.lock` with `--require-hashes` | Medium | OWASP A08, FIPS 140-3 | 2.5 | **Done** |
| SEC-05 | Pillow/numpy/deps upgraded for Python 3.13 + CVE fixes | Medium | OWASP A06 | 2.5 | **Done** |
| SEC-06 | Security audit logging — dedicated security event logger | Medium | OWASP A09, NIST AU-3 | 3 | **Done** |
| SEC-07 | Unit tests for Sprint 1–3 modules (39 unit + 8 integration = 47 tests) | Medium | NIST SA-11 | 3–4 | **Done** |
| SEC-08 | Error loop bounded in camera.py `run_loop` (max 50) | Medium | DISA-STIG V-222659 | 2.5 | **Done** |
| SEC-09 | Slot tool validates dimensions (positive, within image) | Medium | DISA-STIG V-222612 | 2.5 | **Done** |
| SEC-10 | Core dumps restricted (`ulimit -c 0`) | Medium | CIS L2 | 2.5 | **Done** |
| SEC-11 | Type hints normalised to `X \| None` (PEP 604) | Low | PEP 604 | 2.5 | **Done** |
| SEC-12 | JSON file size checked before parsing (1 MB limit) | Low | OWASP A04 | 2.5 | **Done** |
| SEC-13 | Config file permissions set to 0640 | Low | NIST SC-28 | 2.5 | **Done** |
| SEC-14 | Image pixel limit set to 25M (`MAX_IMAGE_PIXELS`) | Low | NIST SI-10 | 2.5 | **Done** |
| SEC-15 | Error messages use `.name` instead of absolute paths | Low | DISA-STIG V-222602 | 2.5 | **Done** |
| SEC-16 | Image file type validated via magic bytes (PNG/JPEG) | Low | DISA-STIG V-222577 | 2.5 | **Done** |

---

## Security logging events

Added in Sprint 3 (SEC-06). Emitted to a dedicated `security` logger.

| Event | Trigger | Severity |
|-------|---------|----------|
| `CONFIG_VALIDATION_FAIL` | Malformed or out-of-range config value at startup | ERROR |
| `CHECKSUM_MISMATCH` | Model file fails SHA-256 verification | CRITICAL |
| `ERROR_THRESHOLD_BREACH` | Consecutive error count exceeds cap in camera loop | WARNING |
| `BOUNDS_VIOLATION` | Slot coordinates or dimensions fail validation | WARNING |
| `INVALID_FILE_TYPE` | Image file fails magic byte check | WARNING |
| `FILE_SIZE_EXCEEDED` | JSON or image file exceeds size limit | WARNING |

---

## Residual gaps (accepted risks)

These gaps remain after all 16 findings are addressed. Each is documented
with a rationale for acceptance or deferral.

| # | Gap | Severity | Rationale |
|---|-----|----------|-----------|
| RG-01 | No runtime integrity monitoring (AIDE/tripwire) | Low | Mitigated by future read-only rootfs. Offline device. |
| RG-02 | No secure boot chain (Pi Zero 2W hardware limitation) | Low | Physical access required. Accepted for home art installation. |
| RG-03 | No automatic security updates (device is offline) | Medium | Document manual update procedure below. |
| RG-04 | rembg model downloaded via HuggingFace Hub without hash pinning | Medium | Investigate rembg model hash pinning in future sprint. |
| RG-05 | No fuzz testing of image inputs or config | Low | Unit tests (SEC-07) cover known-bad inputs. Fuzz deferred. |
| RG-06 | No GPIO tamper detection | Low | Accepted. Home art installation, no adversarial environment. |
| RG-07 | Log rotation on constrained SD card storage | Medium | Addressed via journald `SystemMaxUse` in Sprint 4 service. |
| RG-08 | Swap file unencrypted | Low | No sensitive data at rest. FIPS 140-3 N/A documented above. |

---

## Manual update procedure (RG-03)

When security patches are needed:

1. Connect the Pi to a network temporarily
2. `sudo apt update && sudo apt upgrade`
3. `source venv/bin/activate && pip install --upgrade -r requirements.txt`
4. Verify model checksums have not changed (run `install.sh` integrity checks)
5. Disconnect network and restart the service
