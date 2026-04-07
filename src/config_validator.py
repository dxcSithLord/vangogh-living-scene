"""Config validation for the Van Gogh Living Scene.

Validates all config.yaml values at startup: type checks, range checks,
and path existence. Fails fast with a clear error if config is malformed.

Standards: OWASP A05 (Security Misconfiguration), NIST CM-6 (Configuration Settings).
"""

import logging
import sys
from pathlib import Path
from typing import Any

from src.security_log import SecurityEvent, log_security_event

logger = logging.getLogger(__name__)

# --- Validation schema ---
# Each entry: (dotted key path, expected type, optional range/check)

_RANGE_CHECKS: dict[str, tuple[type, float | None, float | None]] = {
    "display.width": (int, 1, 10000),
    "display.height": (int, 1, 10000),
    "display.saturation": (float, 0.0, 1.0),
    "detection.confidence": (float, 0.0, 1.0),
    "presence.entering_frames": (int, 1, 1000),
    "presence.exiting_frames": (int, 1, 1000),
    "presence.ghost_ttl_seconds": (float, 0.0, 86400.0),
    "style.content_size": (int, 1, 4096),
    "style.predict_size": (int, 1, 4096),
    "style.num_threads": (int, 1, 16),
    "memory.rss_warning_mb": (int, 1, 8192),
}

_REQUIRED_STRINGS: list[str] = [
    "detection.model",
    "paths.background",
    "paths.slots",
    "paths.style_predict_model",
    "paths.style_transform_model",
    "paths.style_image",
    "rembg.model_name",
    "logging.level",
]

_REQUIRED_LISTS: list[str] = [
    "detection.labels",
]

_VALID_LOG_LEVELS: set[str] = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def _get_nested(config: dict[str, Any], dotted_key: str) -> Any:
    """Retrieve a value from a nested dict using a dotted key path."""
    keys = dotted_key.split(".")
    current: Any = config
    for key in keys:
        if not isinstance(current, dict):
            raise ValueError(f"Expected dict at '{key}' in path '{dotted_key}'")
        if key not in current:
            raise KeyError(f"Missing required config key: '{dotted_key}'")
        current = current[key]
    return current


def validate_config(config: dict[str, Any], project_root: Path) -> list[str]:
    """Validate all config values. Returns a list of error messages (empty = valid).

    Args:
        config: Parsed config.yaml dict.
        project_root: Project root directory for resolving relative paths.

    Returns:
        List of error strings. Empty list means config is valid.
    """
    errors: list[str] = []

    # Check required string fields
    for key in _REQUIRED_STRINGS:
        try:
            value = _get_nested(config, key)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"'{key}' must be a non-empty string, got: {type(value).__name__}")
        except (KeyError, ValueError) as exc:
            errors.append(str(exc))

    # Check required list fields
    for key in _REQUIRED_LISTS:
        try:
            value = _get_nested(config, key)
            if not isinstance(value, list) or len(value) == 0:
                errors.append(f"'{key}' must be a non-empty list")
        except (KeyError, ValueError) as exc:
            errors.append(str(exc))

    # Check range-constrained numeric fields
    for key, (expected_type, min_val, max_val) in _RANGE_CHECKS.items():
        try:
            value = _get_nested(config, key)
        except (KeyError, ValueError) as exc:
            errors.append(str(exc))
            continue

        # Allow int where float is expected
        if expected_type is float and isinstance(value, int):
            value = float(value)

        if not isinstance(value, expected_type):
            errors.append(f"'{key}' must be {expected_type.__name__}, got: {type(value).__name__}")
            continue

        # Defensive guard for schema drift; do not silently skip validation.
        if not isinstance(value, (int, float)):
            errors.append(
                f"Internal validator schema error for '{key}': "
                f"_RANGE_CHECKS must use numeric types, got {type(value).__name__}"
            )
            continue
        num = float(value)
        if min_val is not None and num < min_val:
            errors.append(f"'{key}' value {value} is below minimum {min_val}")
        if max_val is not None and num > max_val:
            errors.append(f"'{key}' value {value} is above maximum {max_val}")

    # Check logging level
    try:
        log_level = _get_nested(config, "logging.level")
        if isinstance(log_level, str) and log_level.upper() not in _VALID_LOG_LEVELS:
            errors.append(
                f"'logging.level' must be one of {sorted(_VALID_LOG_LEVELS)}, got: '{log_level}'"
            )
    except (KeyError, ValueError):
        pass  # Already caught by _REQUIRED_STRINGS

    # Check that path values point to existing files (relative to project root)
    _PATH_KEYS_MUST_EXIST: list[str] = [
        "paths.background",
        "paths.slots",
        "paths.style_predict_model",
        "paths.style_transform_model",
        "paths.style_image",
    ]
    for key in _PATH_KEYS_MUST_EXIST:
        try:
            value = _get_nested(config, key)
            if isinstance(value, str):
                resolved = project_root / value
                if not resolved.is_file():
                    errors.append(f"'{key}' path does not exist: {resolved.name}")
        except (KeyError, ValueError):
            pass  # Already caught above

    # Check detection model path (absolute path on system)
    try:
        det_model = _get_nested(config, "detection.model")
        if isinstance(det_model, str):
            det_path = Path(det_model)
            if not det_path.is_file():
                errors.append(f"'detection.model' path does not exist: {det_path.name}")
    except (KeyError, ValueError):
        pass

    return errors


def validate_or_exit(config: dict[str, Any], project_root: Path) -> None:
    """Validate config and exit with code 1 if invalid.

    Logs all errors before exiting so the operator can fix them in one pass.
    """
    errors = validate_config(config, project_root)
    if errors:
        logger.error("Config validation failed with %d error(s):", len(errors))
        for err in errors:
            logger.error("  - %s", err)
        log_security_event(
            SecurityEvent.CONFIG_VALIDATION_FAIL,
            f"Config validation failed with {len(errors)} error(s): {'; '.join(errors)}",
        )
        sys.exit(1)
    logger.info("Config validation passed")


if __name__ == "__main__":
    import yaml

    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(name)s: %(message)s")

    config_path = Path("config/config.yaml")
    if not config_path.is_file():
        logger.error("Config file not found: %s", config_path.name)
        sys.exit(1)

    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    project_root = Path(__file__).resolve().parent.parent
    validate_or_exit(config, project_root)
