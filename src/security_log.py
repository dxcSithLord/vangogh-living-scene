"""Security audit logging for the Van Gogh Living Scene.

Dedicated security event logger that emits structured events to both
the standard logging system (journald via systemd) and an optional
log file. Each event includes a severity, event type, and detail message.

Standards: OWASP A09 (Security Logging), NIST AU-3 (Content of Audit Records).
"""

import logging
from enum import Enum
from pathlib import Path
from typing import Any


class SecurityEvent(Enum):
    """Recognised security event types."""

    CONFIG_VALIDATION_FAIL = "CONFIG_VALIDATION_FAIL"
    CHECKSUM_MISMATCH = "CHECKSUM_MISMATCH"
    ERROR_THRESHOLD_BREACH = "ERROR_THRESHOLD_BREACH"
    BOUNDS_VIOLATION = "BOUNDS_VIOLATION"
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    FILE_SIZE_EXCEEDED = "FILE_SIZE_EXCEEDED"


# Map each event to its default logging severity.
_EVENT_SEVERITY: dict[SecurityEvent, int] = {
    SecurityEvent.CONFIG_VALIDATION_FAIL: logging.ERROR,
    SecurityEvent.CHECKSUM_MISMATCH: logging.CRITICAL,
    SecurityEvent.ERROR_THRESHOLD_BREACH: logging.WARNING,
    SecurityEvent.BOUNDS_VIOLATION: logging.WARNING,
    SecurityEvent.INVALID_FILE_TYPE: logging.WARNING,
    SecurityEvent.FILE_SIZE_EXCEEDED: logging.WARNING,
}

# Singleton logger name used across the application.
_LOGGER_NAME = "security"

logger = logging.getLogger(_LOGGER_NAME)


def init_security_logger(
    log_file: Path | None = None,
    level: int = logging.WARNING,
) -> logging.Logger:
    """Initialise the security logger.

    Adds a StreamHandler (for journald/stderr) and optionally a FileHandler.
    Safe to call multiple times — each handler type is added at most once.
    A bootstrap call (no log_file) followed by a full call (with log_file)
    will attach the file handler on the second call.

    Args:
        log_file: Optional path to a dedicated security log file.
        level: Minimum logging level for the security logger.

    Returns:
        The configured security logger instance.
    """
    logger.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s %(name)s %(levelname)s [%(event_type)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    # Add StreamHandler once (console / journald).
    # Use exact type check: FileHandler is a StreamHandler subclass.
    has_stream = any(type(h) is logging.StreamHandler for h in logger.handlers)
    if not has_stream:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    # Add FileHandler once, when a log file is configured.
    if log_file is not None:
        has_file = any(isinstance(h, logging.FileHandler) for h in logger.handlers)
        if not has_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


def log_security_event(
    event: SecurityEvent,
    detail: str,
    extra: dict[str, Any] | None = None,
) -> None:
    """Emit a structured security event.

    Args:
        event: The security event type.
        detail: Human-readable description of the event.
        extra: Optional additional context (included in the log record).
    """
    severity = _EVENT_SEVERITY.get(event, logging.WARNING)
    log_extra: dict[str, Any] = {"event_type": event.value}
    if extra:
        log_extra.update(extra)
    logger.log(severity, detail, extra=log_extra)
