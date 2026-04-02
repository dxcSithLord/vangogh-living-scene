"""Tests for src/security_log.py."""

import logging
from pathlib import Path

from src.security_log import (
    SecurityEvent,
    init_security_logger,
    log_security_event,
    logger,
)


class TestSecurityLogger:
    """Security logger should initialise and emit structured events."""

    def setup_method(self) -> None:
        """Reset the security logger handlers before each test."""
        logger.handlers.clear()

    def test_init_adds_stream_handler(self) -> None:
        init_security_logger()
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_init_adds_file_handler(self, tmp_dir: Path) -> None:
        log_file = tmp_dir / "security.log"
        init_security_logger(log_file=log_file)
        assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)
        assert log_file.exists()

    def test_init_idempotent(self) -> None:
        init_security_logger()
        count = len(logger.handlers)
        init_security_logger()
        assert len(logger.handlers) == count

    def test_log_event_writes_to_file(self, tmp_dir: Path) -> None:
        log_file = tmp_dir / "security.log"
        init_security_logger(log_file=log_file, level=logging.DEBUG)
        log_security_event(SecurityEvent.BOUNDS_VIOLATION, "Slot X out of range")
        # Flush handlers
        for h in logger.handlers:
            h.flush()
        content = log_file.read_text(encoding="utf-8")
        assert "BOUNDS_VIOLATION" in content
        assert "Slot X out of range" in content


class TestSecurityEventEnum:
    """All expected security events should be defined."""

    def test_all_events_defined(self) -> None:
        expected = {
            "CONFIG_VALIDATION_FAIL",
            "CHECKSUM_MISMATCH",
            "ERROR_THRESHOLD_BREACH",
            "BOUNDS_VIOLATION",
            "INVALID_FILE_TYPE",
            "FILE_SIZE_EXCEEDED",
        }
        actual = {e.value for e in SecurityEvent}
        assert expected == actual
