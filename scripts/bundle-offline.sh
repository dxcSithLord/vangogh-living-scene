#!/usr/bin/env bash
# scripts/bundle-offline.sh — Van Gogh Living Scene offline bundle builder
#
# Creates a self-contained tar archive with all artifacts needed to run
# install.sh on an air-gapped Raspberry Pi Zero 2W. Run on a connected
# machine, transfer the archive to the Pi via USB or local network.
#
# apt packages are NOT bundled — they must be installed while online
# before the Pi goes air-gapped. See docs/plan/install.md.
#
# Standards:
#   NIST SI-7  (Software, Firmware, and Information Integrity)
#   OWASP A08  (Software and Data Integrity Failures)
#   FIPS 140-3 (SHA-256 build-time integrity verification)
#   CIS L2     (Hardened script defaults)
#   DISA-STIG V-222602 (Input validation)
#
# Usage:
#   scripts/bundle-offline.sh [--output <path>]
#
# Output:
#   vangogh-offline-bundle.tar.gz (default) containing:
#     pip-packages/   — aarch64 wheel cache
#     models/         — TFLite + rembg ONNX models
#     SHA256SUMS      — manifest of all bundle contents
#
# Exit codes:
#   0  Bundle created successfully.
#   1  Error (download failure, checksum mismatch, missing tool).

set -euo pipefail
umask 0077

# ---------------------------------------------------------------------------
# Constants — model URLs and checksums (keep in sync with install.sh)
# ---------------------------------------------------------------------------
PREDICT_URL="https://storage.googleapis.com/download.tensorflow.org/models/tflite/task_library/style_transfer/android/magenta_arbitrary-image-stylization-v1-256_int8_prediction_1.tflite"
TRANSFORM_URL="https://storage.googleapis.com/download.tensorflow.org/models/tflite/task_library/style_transfer/android/magenta_arbitrary-image-stylization-v1-256_int8_transfer_1.tflite"

# SEC-01: SHA-256 checksums for model integrity (NIST SI-7, FIPS 140-3)
PREDICT_SHA256="af6ad4b2e7aeba0675f32636082ab915ced5375229a3f8aff7e714c6213f5ed2"
TRANSFORM_SHA256="7a1550643cf034a4d813c0aa276976cd15da4141b4f1ec3631db1d0d9c8e2cd1"

# RG-04: rembg model — best-effort hash (no upstream pinning available).
REMBG_URL="https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net_human_seg.onnx"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
OUTPUT_PATH="${REPO_ROOT}/vangogh-offline-bundle.tar.gz"

# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------
usage() {
    cat <<'EOF'
Usage: scripts/bundle-offline.sh [OPTIONS]

Creates an offline installation bundle for the Van Gogh Living Scene.
Run on a connected machine; transfer the resulting tar to the Pi.

Options:
  --output <path>  Output tar.gz path (default: vangogh-offline-bundle.tar.gz)
  --help           Show this help message and exit.
EOF
}

# ---------------------------------------------------------------------------
# Argument parsing (DISA-STIG V-222602: validate inputs)
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "${1}" in
        --output)
            if [[ $# -lt 2 ]]; then
                printf 'ERROR: --output requires a path argument.\n' >&2
                exit 1
            fi
            OUTPUT_PATH="${2}"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            printf 'ERROR: Unknown option: %s\n' "${1}" >&2
            usage >&2
            exit 1
            ;;
    esac
done

# Validate output path is writable
OUTPUT_DIR="$(dirname "${OUTPUT_PATH}")"
if [[ ! -d "${OUTPUT_DIR}" ]]; then
    printf 'ERROR: Output directory does not exist: %s\n' "${OUTPUT_DIR}" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Prerequisite checks
# ---------------------------------------------------------------------------
for cmd in pip curl sha256sum tar; do
    if ! command -v "${cmd}" >/dev/null 2>&1; then
        printf 'ERROR: Required command not found: %s\n' "${cmd}" >&2
        exit 1
    fi
done

if [[ ! -f "${REPO_ROOT}/requirements.lock" ]]; then
    printf 'ERROR: requirements.lock not found at %s\n' "${REPO_ROOT}" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Architecture detection
# ---------------------------------------------------------------------------
ARCH="$(uname -m)"
printf 'INFO: Detected architecture: %s\n' "${ARCH}"

# ---------------------------------------------------------------------------
# Create staging directory (cleaned up on exit)
# ---------------------------------------------------------------------------
STAGING="$(mktemp -d)"
trap 'rm -rf "${STAGING}"' EXIT

mkdir -p "${STAGING}/pip-packages"
mkdir -p "${STAGING}/models"

# ---------------------------------------------------------------------------
# Checksum verification helper (NIST SI-7, FIPS 140-3)
# ---------------------------------------------------------------------------
verify_checksum() {
    local file="${1}"
    local expected="${2}"
    local actual
    actual="$(sha256sum "${file}" | awk '{print $1}')"
    if [[ "${actual}" != "${expected}" ]]; then
        printf 'CRITICAL: Checksum mismatch for %s\n' "${file}" >&2
        printf '  Expected: %s\n' "${expected}" >&2
        printf '  Actual:   %s\n' "${actual}" >&2
        rm -f "${file}"
        return 1
    fi
    printf 'Checksum verified: %s\n' "${file}"
}

# ---------------------------------------------------------------------------
# 1. Download pip packages (SEC-04: hash-pinned, OWASP A08)
# ---------------------------------------------------------------------------
printf '\n=== Downloading pip packages ===\n'

PIP_ARGS=(
    download
    --require-hashes
    --extra-index-url "https://www.piwheels.org/simple"
    -r "${REPO_ROOT}/requirements.lock"
    -d "${STAGING}/pip-packages"
)

if [[ "${ARCH}" != "aarch64" ]]; then
    printf 'INFO: Cross-platform download for aarch64 (running on %s)\n' "${ARCH}"
    printf 'WARNING: --only-binary=:all: is set. Packages without aarch64 wheels will fail.\n'
    PIP_ARGS+=(
        --platform "linux_aarch64"
        --python-version "3.13"
        --implementation "cp"
        --abi "cp313"
        --only-binary=":all:"
    )
else
    printf 'INFO: Native aarch64 download\n'
    PIP_ARGS+=(
        --python-version "3.13"
        --implementation "cp"
        --abi "cp313"
    )
fi

pip "${PIP_ARGS[@]}"

# ---------------------------------------------------------------------------
# 2. Download TFLite models (SEC-01: checksum verified)
# ---------------------------------------------------------------------------
printf '\n=== Downloading TFLite models ===\n'

curl -fL --retry 3 --retry-delay 5 "${PREDICT_URL}" \
    -o "${STAGING}/models/style_predict_int8.tflite"
verify_checksum "${STAGING}/models/style_predict_int8.tflite" "${PREDICT_SHA256}"

curl -fL --retry 3 --retry-delay 5 "${TRANSFORM_URL}" \
    -o "${STAGING}/models/style_transform_int8.tflite"
verify_checksum "${STAGING}/models/style_transform_int8.tflite" "${TRANSFORM_SHA256}"

# ---------------------------------------------------------------------------
# 3. Download rembg model (RG-04: best-effort, no upstream hash pinning)
# ---------------------------------------------------------------------------
printf '\n=== Downloading rembg model (RG-04: best-effort integrity) ===\n'

curl -fL --retry 3 --retry-delay 5 "${REMBG_URL}" \
    -o "${STAGING}/models/u2net_human_seg.onnx"

if [[ ! -s "${STAGING}/models/u2net_human_seg.onnx" ]]; then
    printf 'ERROR: rembg model download failed or is empty.\n' >&2
    printf 'Verify URL: %s\n' "${REMBG_URL}" >&2
    exit 1
fi

printf 'Downloaded rembg model: %s bytes\n' "$(stat -c%s "${STAGING}/models/u2net_human_seg.onnx")"

# ---------------------------------------------------------------------------
# 4. Generate SHA-256 manifest (NIST SI-7)
# ---------------------------------------------------------------------------
printf '\n=== Generating SHA256SUMS manifest ===\n'

(cd "${STAGING}" && find . -type f ! -name 'SHA256SUMS' -exec sha256sum {} + > SHA256SUMS)

MANIFEST_COUNT="$(wc -l < "${STAGING}/SHA256SUMS")"
printf 'Manifest contains %s entries\n' "${MANIFEST_COUNT}"

# ---------------------------------------------------------------------------
# 5. Create tar archive
# ---------------------------------------------------------------------------
printf '\n=== Creating bundle archive ===\n'

tar -czf "${OUTPUT_PATH}" -C "${STAGING}" .

BUNDLE_SIZE="$(stat -c%s "${OUTPUT_PATH}")"
BUNDLE_SHA256="$(sha256sum "${OUTPUT_PATH}" | awk '{print $1}')"

printf '\n=== Bundle created successfully ===\n'
printf 'File:     %s\n' "${OUTPUT_PATH}"
printf 'Size:     %s bytes (%.0f MB)\n' "${BUNDLE_SIZE}" "$(echo "${BUNDLE_SIZE} / 1048576" | bc)"
printf 'SHA-256:  %s\n' "${BUNDLE_SHA256}"
printf '\nVerify after transfer: sha256sum %s\n' "$(basename "${OUTPUT_PATH}")"
printf 'Expected: %s\n' "${BUNDLE_SHA256}"
