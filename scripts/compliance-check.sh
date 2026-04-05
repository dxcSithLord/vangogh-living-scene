#!/usr/bin/env bash
# scripts/compliance-check.sh — Van Gogh Living Scene
#
# Full compliance runner for the target Raspberry Pi Zero 2W.
# Runs the complete tool battery that CI workflows cover, plus hardware
# pytest markers that are skipped on GitHub runners.
#
# Standards references:
#   NIST SA-11 (Developer Security Testing and Evaluation)
#   OWASP A04 (Insecure Design), A05 (Security Misconfiguration)
#   OWASP A06 (Vulnerable and Outdated Components)
#
# Usage:
#   scripts/compliance-check.sh [--help] [--report-only]
#
# Environment:
#   VANGOGH_ALLOW_NON_PI=1   Skip Pi hardware detection (developer laptops).
#
# Exit codes:
#   0  All checks passed (or --report-only mode).
#   1  One or more checks failed.

set -euo pipefail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPORT_FILE="${SCRIPT_DIR}/compliance-report.md"
TIMESTAMP="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
COMMIT_SHA="$(git -C "${REPO_ROOT}" rev-parse --short HEAD 2>/dev/null || echo "unknown")"

# Canonical check ordering — single source of truth for summary + report.
CHECK_ORDER=(
    "ruff-format"
    "ruff-lint"
    "mypy"
    "bandit"
    "pip-audit"
    "yamllint"
    "actionlint"
    "pytest"
)

# ---------------------------------------------------------------------------
# Flags
# ---------------------------------------------------------------------------
REPORT_ONLY=0

# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------
usage() {
    cat <<'EOF'
Usage: scripts/compliance-check.sh [OPTIONS]

Full compliance runner for the Van Gogh Living Scene project.
Runs on the target Raspberry Pi Zero 2W post-install.

Checks performed:
  1. ruff format --check .
  2. ruff check . --output-format=concise
  3. mypy src tools
  4. bandit -c .bandit -r src tools --severity-level medium --confidence-level medium
  5. pip-audit -r requirements.lock
  6. yamllint .
  7. actionlint (if installed)
  8. pytest tests/ (ALL markers, including hardware)

Options:
  --help         Show this help message and exit.
  --report-only  Run all checks but exit 0 regardless of results.
                 Useful for developer laptops or baseline assessment.

Environment variables:
  VANGOGH_ALLOW_NON_PI=1   Bypass Pi hardware detection. Use on developer
                            laptops where Pi-specific hardware is absent.

Output:
  Stdout:            ASCII summary table with per-check status and duration.
  scripts/compliance-report.md:  Machine-readable Markdown report with
                                 timestamp, commit SHA, and per-check details.

Standards: NIST SA-11, OWASP A04/A05/A06.
EOF
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
for arg in "$@"; do
    case "${arg}" in
        --help)
            usage
            exit 0
            ;;
        --report-only)
            REPORT_ONLY=1
            ;;
        *)
            printf 'Unknown option: %s\n' "${arg}" >&2
            usage >&2
            exit 1
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Pi detection
# ---------------------------------------------------------------------------
detect_pi() {
    # Check /proc/device-tree/model for "Raspberry Pi".
    if [[ -r /proc/device-tree/model ]]; then
        local model
        model="$(tr -d '\0' < /proc/device-tree/model 2>/dev/null || true)"
        if [[ "${model}" == *"Raspberry Pi"* ]]; then
            return 0
        fi
    fi
    return 1
}

if ! detect_pi; then
    if [[ "${VANGOGH_ALLOW_NON_PI:-0}" != "1" ]]; then
        cat >&2 <<'EOF'
ERROR: This script is intended for the Raspberry Pi Zero 2W target hardware.

  /proc/device-tree/model does not contain "Raspberry Pi".

If you are running on a developer laptop and want to proceed anyway, set:

  VANGOGH_ALLOW_NON_PI=1 bash scripts/compliance-check.sh --report-only

EOF
        exit 1
    fi
    printf 'WARNING: VANGOGH_ALLOW_NON_PI=1 set — skipping Pi detection.\n\n'
fi

# ---------------------------------------------------------------------------
# Activate virtual environment if present
# ---------------------------------------------------------------------------
VENV_PATH="${REPO_ROOT}/.venv"
if [[ -f "${VENV_PATH}/bin/activate" ]]; then
    # shellcheck source=/dev/null
    source "${VENV_PATH}/bin/activate"
    printf 'INFO: Activated virtual environment: %s\n' "${VENV_PATH}"
else
    printf 'INFO: No .venv found at %s; using current PATH.\n' "${VENV_PATH}"
fi

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Log directory preserved after exit so paths in the summary/report stay
# resolvable for debugging. /tmp is cleaned by the OS on reboot.
LOG_DIR="$(mktemp -d)"

# Associative arrays: check name → pass/fail status and duration.
declare -A CHECK_STATUS
declare -A CHECK_DURATION
declare -A CHECK_LOG

# run_check <name> <cmd> [args...]
# Runs the command, captures combined stdout+stderr to a temp log file,
# records pass/fail and wall-clock duration. Never exits early on failure.
run_check() {
    local name="${1}"
    shift
    local log_file="${LOG_DIR}/${name// /_}.log"
    CHECK_LOG["${name}"]="${log_file}"

    printf 'Running: %s ...\n' "${name}"
    local start_ts end_ts elapsed_ms status
    start_ts="$(date +%s%3N)"

    # Run in a subshell so set -e doesn't abort the parent script on failure.
    if "$@" >"${log_file}" 2>&1; then
        status="PASS"
    else
        status="FAIL"
    fi

    end_ts="$(date +%s%3N)"
    elapsed_ms=$(( end_ts - start_ts ))

    CHECK_STATUS["${name}"]="${status}"
    CHECK_DURATION["${name}"]="${elapsed_ms}"
}

# ---------------------------------------------------------------------------
# Change to repo root so relative paths work correctly
# ---------------------------------------------------------------------------
cd "${REPO_ROOT}"

# ---------------------------------------------------------------------------
# Run checks
# ---------------------------------------------------------------------------

# 1. Ruff format check
run_check "ruff-format" ruff format --check .

# 2. Ruff lint
run_check "ruff-lint" ruff check . --output-format=concise

# 3. Mypy strict type check
run_check "mypy" mypy src tools

# 4. Bandit SAST
run_check "bandit" bandit \
    -c .bandit \
    -r src tools \
    --severity-level medium \
    --confidence-level medium \
    -f json \
    -o "${LOG_DIR}/bandit-report.json"

# 5. Pip-audit dependency CVE scan
# Audit the Pi's actual installed manifest (hash-pinned lockfile used by
# install.sh), not the CI subset — hardware deps (picamera2, inky,
# ai-edge-litert, rembg) only live in requirements.lock.
run_check "pip-audit" pip-audit -r requirements.lock

# 6. Yamllint
run_check "yamllint" yamllint .

# 7. Actionlint — required on the target Pi for full compliance. SKIP is
#    only acceptable in --report-only mode or when VANGOGH_ALLOW_NON_PI=1
#    bypasses the Pi gate (e.g. dev laptops without Go binaries installed).
if command -v actionlint >/dev/null 2>&1; then
    # No -color flag: run_check redirects output to a log file, so ANSI
    # escapes would only pollute it.
    run_check "actionlint" actionlint
else
    CHECK_LOG["actionlint"]="${LOG_DIR}/actionlint.log"
    CHECK_DURATION["actionlint"]=0
    if [[ "${REPORT_ONLY}" -eq 1 || "${VANGOGH_ALLOW_NON_PI:-0}" == "1" ]]; then
        CHECK_STATUS["actionlint"]="SKIP"
        printf 'SKIP' > "${CHECK_LOG["actionlint"]}"
        printf 'SKIP: actionlint not installed — skipping (bypass flag set).\n'
    else
        CHECK_STATUS["actionlint"]="FAIL"
        printf 'FAIL: actionlint not installed on target Pi.\n' > "${CHECK_LOG["actionlint"]}"
        printf 'FAIL: actionlint not installed on target Pi — required for full compliance.\n'
    fi
fi

# 8. Pytest — ALL markers (including hardware)
run_check "pytest" pytest tests/ \
    --cov=src \
    --cov=tools \
    --cov-report=xml:"${LOG_DIR}/coverage.xml" \
    --cov-report=term \
    --junitxml="${LOG_DIR}/pytest-report.xml"

# ---------------------------------------------------------------------------
# Determine overall result
# ---------------------------------------------------------------------------
OVERALL_PASS=1
for name in "${!CHECK_STATUS[@]}"; do
    if [[ "${CHECK_STATUS[${name}]}" == "FAIL" ]]; then
        OVERALL_PASS=0
        break
    fi
done

# ---------------------------------------------------------------------------
# Print ASCII summary table to stdout
# ---------------------------------------------------------------------------
print_summary() {
    local col1=22 col2=6 col3=12 col4=50
    local hr
    hr="$(printf '%*s' $(( col1 + col2 + col3 + col4 + 13 )) '' | tr ' ' '-')"

    printf '\n'
    printf '%s\n' "${hr}"
    printf '| %-*s | %-*s | %-*s | %-*s |\n' \
        ${col1} "Check" \
        ${col2} "Status" \
        ${col3} "Duration" \
        ${col4} "Log path"
    printf '%s\n' "${hr}"

    for name in "${CHECK_ORDER[@]}"; do
        local status="${CHECK_STATUS[${name}]:-N/A}"
        local ms="${CHECK_DURATION[${name}]:-0}"
        local log="${CHECK_LOG[${name}]:-}"
        local dur_str
        if [[ "${ms}" -ge 1000 ]]; then
            dur_str="$(( ms / 1000 )).$(( (ms % 1000) / 100 ))s"
        else
            dur_str="${ms}ms"
        fi
        printf '| %-*s | %-*s | %-*s | %-*s |\n' \
            ${col1} "${name}" \
            ${col2} "${status}" \
            ${col3} "${dur_str}" \
            ${col4} "${log}"
    done

    printf '%s\n' "${hr}"

    if [[ "${OVERALL_PASS}" -eq 1 ]]; then
        printf '\nResult: ALL CHECKS PASSED\n\n'
    else
        printf '\nResult: ONE OR MORE CHECKS FAILED\n\n'
    fi

    printf 'Per-check logs preserved at: %s\n\n' "${LOG_DIR}"
}

print_summary

# ---------------------------------------------------------------------------
# Write Markdown report
# ---------------------------------------------------------------------------
write_report() {
    local report="${REPORT_FILE}"

    {
        printf '# Compliance Report — Van Gogh Living Scene\n\n'
        printf '| Field | Value |\n'
        printf '|-------|-------|\n'
        printf '| Timestamp | `%s` |\n' "${TIMESTAMP}"
        printf '| Commit SHA | `%s` |\n' "${COMMIT_SHA}"
        printf '| Host | `%s` |\n' "$(uname -n)"
        printf '| Kernel | `%s` |\n' "$(uname -r)"
        printf '| Pi model | `%s` |\n' "$(tr -d '\0' < /proc/device-tree/model 2>/dev/null || echo 'non-Pi')"
        printf '\n'

        printf '## Check Results\n\n'
        printf '| Check | Status | Duration |\n'
        printf '|-------|--------|----------|\n'

        for name in "${CHECK_ORDER[@]}"; do
            local status="${CHECK_STATUS[${name}]:-N/A}"
            local ms="${CHECK_DURATION[${name}]:-0}"
            local dur_str
            if [[ "${ms}" -ge 1000 ]]; then
                dur_str="$(( ms / 1000 )).$( printf '%03d' $(( ms % 1000 )) | cut -c1-1 )s"
            else
                dur_str="${ms}ms"
            fi
            printf '| `%s` | %s | %s |\n' "${name}" "${status}" "${dur_str}"
        done

        printf '\n'

        if [[ "${OVERALL_PASS}" -eq 1 ]]; then
            printf '## Overall: PASS\n\n'
            printf 'All checks passed.\n\n'
        else
            printf '## Overall: FAIL\n\n'
            printf 'One or more checks failed. Review per-check logs for details.\n\n'

            printf '### Failed check details\n\n'
            for name in "${CHECK_ORDER[@]}"; do
                if [[ "${CHECK_STATUS[${name}]:-}" == "FAIL" ]]; then
                    printf '#### %s\n\n' "${name}"
                    printf '```\n'
                    # Show last 50 lines of log to keep report readable.
                    tail -n 50 "${CHECK_LOG[${name}]}" 2>/dev/null || true
                    printf '```\n\n'
                fi
            done
        fi

        printf '%s\n' '---'
        printf '%s\n' '_Generated by `scripts/compliance-check.sh` — NIST SA-11_'
    } > "${report}"

    printf 'Report written to: %s\n' "${report}"
}

write_report

# ---------------------------------------------------------------------------
# Exit
# ---------------------------------------------------------------------------
if [[ "${REPORT_ONLY}" -eq 1 ]]; then
    printf 'INFO: --report-only mode; exiting 0 regardless of results.\n'
    exit 0
fi

if [[ "${OVERALL_PASS}" -eq 0 ]]; then
    exit 1
fi

exit 0
