"""Tests for src/camera.py.

Camera hardware is not available in CI, so these tests focus on
the error loop cap (SEC-08) and detection parsing logic using mocks.
"""

import queue
from unittest.mock import MagicMock, patch

import numpy as np

from src.camera import MAX_CONSECUTIVE_ERRORS, Camera, Detection


class TestErrorLoopCap:
    """The camera run_loop should back off after MAX_CONSECUTIVE_ERRORS."""

    def test_backs_off_after_max_errors(self, sample_config: dict) -> None:
        det_queue: queue.Queue[Detection] = queue.Queue(maxsize=10)
        camera = Camera(config=sample_config, output_queue=det_queue)

        # Pretend camera is started
        camera._picam2 = MagicMock()
        camera._running = True
        call_count = 0

        def failing_poll() -> None:
            nonlocal call_count
            call_count += 1
            if call_count >= MAX_CONSECUTIVE_ERRORS + 5:
                camera._running = False
            raise RuntimeError("Simulated hardware fault")

        camera._poll_once = failing_poll

        with patch("src.camera.time.sleep"):
            camera.run_loop()

        # Should have hit the backoff at least once
        assert call_count >= MAX_CONSECUTIVE_ERRORS


class TestCropDetection:
    """Static crop method should handle edge cases."""

    def test_valid_crop(self) -> None:
        array = np.zeros((480, 640, 3), dtype=np.uint8)
        crop = Camera._crop_detection(array, (10, 10, 100, 100), 640, 480)
        assert crop is not None
        assert crop.size == (100, 100)

    def test_degenerate_crop_returns_none(self) -> None:
        array = np.zeros((480, 640, 3), dtype=np.uint8)
        crop = Camera._crop_detection(array, (10, 10, 0, 0), 640, 480)
        assert crop is None

    def test_out_of_bounds_clamped(self) -> None:
        array = np.zeros((480, 640, 3), dtype=np.uint8)
        crop = Camera._crop_detection(array, (600, 440, 100, 100), 640, 480)
        assert crop is not None
        assert crop.size == (40, 40)
