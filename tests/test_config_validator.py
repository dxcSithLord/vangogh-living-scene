"""Tests for src/config_validator.py."""

import copy
from pathlib import Path

import pytest

from src.config_validator import validate_config


class TestValidConfig:
    """Valid config should produce no errors."""

    def test_valid_config_passes(self, sample_config: dict, project_root: Path) -> None:
        errors = validate_config(sample_config, project_root)
        # Only path-existence errors are acceptable (models may not be downloaded in CI)
        non_path_errors = [e for e in errors if "does not exist" not in e]
        assert non_path_errors == []


class TestMissingKeys:
    """Missing required keys should produce clear errors."""

    def test_missing_display_width(self, sample_config: dict, project_root: Path) -> None:
        cfg = copy.deepcopy(sample_config)
        del cfg["display"]["width"]
        errors = validate_config(cfg, project_root)
        assert any("display.width" in e for e in errors)

    def test_missing_paths_background(self, sample_config: dict, project_root: Path) -> None:
        cfg = copy.deepcopy(sample_config)
        del cfg["paths"]["background"]
        errors = validate_config(cfg, project_root)
        assert any("paths.background" in e for e in errors)

    def test_missing_detection_labels(self, sample_config: dict, project_root: Path) -> None:
        cfg = copy.deepcopy(sample_config)
        del cfg["detection"]["labels"]
        errors = validate_config(cfg, project_root)
        assert any("detection.labels" in e for e in errors)

    def test_missing_entire_section(self, sample_config: dict, project_root: Path) -> None:
        cfg = copy.deepcopy(sample_config)
        del cfg["display"]
        errors = validate_config(cfg, project_root)
        assert len(errors) > 0


class TestBadTypes:
    """Wrong types should produce clear errors."""

    def test_width_as_string(self, sample_config: dict, project_root: Path) -> None:
        cfg = copy.deepcopy(sample_config)
        cfg["display"]["width"] = "wide"
        errors = validate_config(cfg, project_root)
        assert any("display.width" in e for e in errors)

    def test_confidence_as_string(self, sample_config: dict, project_root: Path) -> None:
        cfg = copy.deepcopy(sample_config)
        cfg["detection"]["confidence"] = "high"
        errors = validate_config(cfg, project_root)
        assert any("detection.confidence" in e for e in errors)

    def test_labels_as_string(self, sample_config: dict, project_root: Path) -> None:
        cfg = copy.deepcopy(sample_config)
        cfg["detection"]["labels"] = "person"
        errors = validate_config(cfg, project_root)
        assert any("detection.labels" in e for e in errors)


class TestBadRanges:
    """Out-of-range values should produce errors."""

    def test_negative_width(self, sample_config: dict, project_root: Path) -> None:
        cfg = copy.deepcopy(sample_config)
        cfg["display"]["width"] = -1
        errors = validate_config(cfg, project_root)
        assert any("display.width" in e and "below minimum" in e for e in errors)

    def test_saturation_above_one(self, sample_config: dict, project_root: Path) -> None:
        cfg = copy.deepcopy(sample_config)
        cfg["display"]["saturation"] = 1.5
        errors = validate_config(cfg, project_root)
        assert any("display.saturation" in e and "above maximum" in e for e in errors)

    def test_confidence_negative(self, sample_config: dict, project_root: Path) -> None:
        cfg = copy.deepcopy(sample_config)
        cfg["detection"]["confidence"] = -0.1
        errors = validate_config(cfg, project_root)
        assert any("detection.confidence" in e for e in errors)


class TestBadLogLevel:
    """Invalid logging level should produce an error."""

    def test_invalid_log_level(self, sample_config: dict, project_root: Path) -> None:
        cfg = copy.deepcopy(sample_config)
        cfg["logging"]["level"] = "VERBOSE"
        errors = validate_config(cfg, project_root)
        assert any("logging.level" in e for e in errors)
