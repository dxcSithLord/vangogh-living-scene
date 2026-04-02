"""Tests for src/styler.py.

TFLite models are not available in CI, so these tests focus on
input validation and constructor checks.
"""

from pathlib import Path

import pytest
from PIL import Image

from src.styler import Styler


class TestConstructorValidation:
    """Styler should fail fast with clear errors on missing files."""

    def test_missing_style_image(self, tmp_dir: Path) -> None:
        with pytest.raises(FileNotFoundError, match="Style image not found"):
            Styler(
                style_image_path=tmp_dir / "nonexistent.jpg",
                predict_model_path=tmp_dir / "predict.tflite",
                transform_model_path=tmp_dir / "transform.tflite",
            )

    def test_missing_predict_model(self, tmp_dir: Path) -> None:
        # Create a style image but no model
        img = Image.new("RGB", (64, 64))
        style_path = tmp_dir / "style.jpg"
        img.save(style_path, format="JPEG")

        with pytest.raises(FileNotFoundError, match="Predict model not found"):
            Styler(
                style_image_path=style_path,
                predict_model_path=tmp_dir / "nonexistent.tflite",
                transform_model_path=tmp_dir / "transform.tflite",
            )


class TestStylizeValidation:
    """stylize() should reject non-RGBA input."""

    def test_rejects_rgb_input(self, tmp_dir: Path) -> None:
        """Cannot test full stylize without models, but can test the mode check
        by creating a Styler with a mocked bottleneck."""
        styler = Styler.__new__(Styler)
        styler._transform_model_path = tmp_dir / "transform.tflite"
        styler._content_size = 384
        styler._num_threads = 4
        styler._rss_warning_mb = 460
        styler._style_bottleneck = None

        rgb = Image.new("RGB", (64, 64))
        with pytest.raises(ValueError, match="Expected RGBA"):
            styler.stylize(rgb)
