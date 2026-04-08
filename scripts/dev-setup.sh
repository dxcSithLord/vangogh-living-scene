#!/usr/bin/env bash
# scripts/dev-setup.sh — Van Gogh Living Scene developer environment setup
#
# Creates a Python virtual environment with runtime and dev tool dependencies.
# No models, no systemd service, no system user — dev/CI only.
#
# Standards:
#   OWASP A08  (Software and Data Integrity Failures — hash-pinned deps)
#   FIPS 140-3 (SHA-256 build-time integrity)
#   CIS L2     (Hardened script defaults)
#   NIST SC-28 (Protection of Information at Rest — file permissions)
#   DISA-STIG V-222602 (Input validation)
#
# Usage:
#   scripts/dev-setup.sh
#
# Prerequisites:
#   Python 3.13+ with venv module.
#
# Exit codes:
#   0  Environment created successfully.
#   1  Error (missing Python, wrong version, install failure).

set -euo pipefail
umask 0077

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${REPO_ROOT}/.venv"

# ---------------------------------------------------------------------------
# Python version check (DISA-STIG V-222602: validate prerequisites)
# ---------------------------------------------------------------------------
REQUIRED_MAJOR=3
REQUIRED_MINOR=13

if ! command -v python3 >/dev/null 2>&1; then
    printf 'ERROR: python3 not found in PATH.\n' >&2
    exit 1
fi

PY_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
PY_MAJOR="$(echo "${PY_VERSION}" | cut -d. -f1)"
PY_MINOR="$(echo "${PY_VERSION}" | cut -d. -f2)"

if [[ "${PY_MAJOR}" -ne "${REQUIRED_MAJOR}" ]] || \
   [[ "${PY_MINOR}" -ne "${REQUIRED_MINOR}" ]]; then
    printf 'ERROR: Python %d.%d required (exact), found %s\n' \
        "${REQUIRED_MAJOR}" "${REQUIRED_MINOR}" "${PY_VERSION}" >&2
    printf 'Wheels are bundled for cp%d%d only.\n' \
        "${REQUIRED_MAJOR}" "${REQUIRED_MINOR}" >&2
    exit 1
fi

printf 'INFO: Python %s detected\n' "${PY_VERSION}"

# ---------------------------------------------------------------------------
# Check required files exist
# ---------------------------------------------------------------------------
if [[ ! -f "${REPO_ROOT}/requirements.lock" ]]; then
    printf 'ERROR: requirements.lock not found at %s\n' "${REPO_ROOT}" >&2
    exit 1
fi

# Dev tools: prefer hash-pinned lockfile, fall back to unpinned txt
if [[ -f "${REPO_ROOT}/requirements-dev.lock" ]]; then
    DEV_DEPS_FILE="${REPO_ROOT}/requirements-dev.lock"
    DEV_DEPS_HASH_FLAG="--require-hashes"
    printf 'INFO: Using hash-pinned requirements-dev.lock\n'
elif [[ -f "${REPO_ROOT}/requirements-dev.txt" ]]; then
    DEV_DEPS_FILE="${REPO_ROOT}/requirements-dev.txt"
    DEV_DEPS_HASH_FLAG=""
    printf 'WARNING: requirements-dev.lock not found — using requirements-dev.txt without hash verification.\n' >&2
    printf '  Generate with: pip-compile --generate-hashes requirements-dev.txt -o requirements-dev.lock\n' >&2
else
    printf 'ERROR: Neither requirements-dev.lock nor requirements-dev.txt found at %s\n' "${REPO_ROOT}" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Create virtual environment
# ---------------------------------------------------------------------------
if [[ -d "${VENV_DIR}" ]]; then
    printf 'INFO: Existing .venv found — removing and recreating\n'
    rm -rf "${VENV_DIR}"
fi

printf 'INFO: Creating virtual environment at %s\n' "${VENV_DIR}"
python3 -m venv "${VENV_DIR}" --system-site-packages

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

# ---------------------------------------------------------------------------
# Install dependencies (SEC-04: hash-pinned, OWASP A08)
# ---------------------------------------------------------------------------
printf '\n=== Installing runtime dependencies (hash-pinned) ===\n'
python3 -m pip install --require-hashes -r "${REPO_ROOT}/requirements.lock"

printf '\n=== Installing dev tools ===\n'
# shellcheck disable=SC2086
python3 -m pip install ${DEV_DEPS_HASH_FLAG} -r "${DEV_DEPS_FILE}"

# ---------------------------------------------------------------------------
# Restrict venv permissions (NIST SC-28)
# ---------------------------------------------------------------------------
chmod -R u=rwX,g=,o= "${VENV_DIR}"

printf '\n=== Dev environment ready ===\n'
printf 'Activate with: source .venv/bin/activate\n'
printf 'Run tests:     pytest tests/\n'
printf 'Run linters:   ruff check . && mypy src tools\n'
