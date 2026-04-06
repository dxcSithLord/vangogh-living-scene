"""Tests for src/isolator.py.

rembg is not available in CI without the model download, so these tests
focus on input validation. The smoke test requires rembg and is marked
with pytest.mark.slow.
"""

import pytest
from PIL import Image

from src.isolator import _MAX_INPUT_DIMENSION, remove_background


class TestInputValidation:
    """Isolator should reject oversized inputs."""

    def test_rejects_oversized_image(self) -> None:
        huge = Image.new("RGB", (_MAX_INPUT_DIMENSION + 1, 100))
        with pytest.raises(ValueError, match="too large"):
            remove_background(huge, session=None)

    def test_rejects_oversized_height(self) -> None:
        huge = Image.new("RGB", (100, _MAX_INPUT_DIMENSION + 1))
        with pytest.raises(ValueError, match="too large"):
            remove_background(huge, session=None)


class TestBoundaryDimension:
    """Isolator should accept images at exactly the dimension limit."""

    def test_accepts_dimensions_at_limit(self) -> None:
        """Image at exactly the limit should pass the size check (not raise ValueError)."""
        img = Image.new("RGB", (_MAX_INPUT_DIMENSION, _MAX_INPUT_DIMENSION))
        # Will fail downstream (no valid session), but should not raise ValueError
        try:
            remove_background(img, session=None)
        except ValueError as exc:
            assert "too large" not in str(exc), "Should not reject image at exact limit"
        except Exception:  # noqa: S110 — expected: no rembg session in CI
            pass
