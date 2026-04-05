"""Camera module for the Van Gogh Living Scene.

Initialises picamera2 with the IMX500 AI Camera, parses detections
from the on-sensor NPU, and delivers bounding-box crops to a queue.
"""

import argparse
import logging
import queue
import sys
import time
from pathlib import Path
from typing import Any, NamedTuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# SEC-08: Cap consecutive errors to prevent tight spin on hardware faults
# (DISA-STIG V-222659). After this many consecutive errors the loop sleeps
# for BACKOFF_SLEEP_SECONDS before retrying.
MAX_CONSECUTIVE_ERRORS: int = 50
BACKOFF_SLEEP_SECONDS: float = 30.0

# COCO label map — only the indices we care about are named.
COCO_LABELS: dict[int, str] = {
    0: "person",
    14: "bird",
    15: "cat",
    16: "dog",
    17: "horse",
}


class Detection(NamedTuple):
    """A single detection from the IMX500 NPU."""

    label: str
    confidence: float
    crop: Image.Image


class Camera:
    """Wraps picamera2 + IMX500 for headless object detection.

    Detections above the confidence threshold and matching the allowed
    labels are cropped from the frame and placed onto the output queue
    as Detection named-tuples.
    """

    def __init__(
        self,
        config: dict[str, Any],
        output_queue: queue.Queue[Detection],
    ) -> None:
        det_cfg = config["detection"]
        self._model_path: str = det_cfg["model"]
        self._confidence: float = float(det_cfg["confidence"])
        self._allowed_labels: set[str] = set(det_cfg["labels"])
        self._queue = output_queue
        self._running = False

        # Initialised in start()
        self._imx500: Any = None
        self._picam2: Any = None
        self._intrinsics: Any = None

    def start(self) -> None:
        """Load firmware onto IMX500 and start the camera stream."""
        from picamera2 import Picamera2
        from picamera2.devices import IMX500
        from picamera2.devices.imx500 import NetworkIntrinsics

        logger.info("Loading IMX500 firmware: %s", self._model_path)
        self._imx500 = IMX500(self._model_path)
        self._imx500.show_network_fw_progress_bar()

        self._intrinsics = self._imx500.network_intrinsics
        if not self._intrinsics:
            self._intrinsics = NetworkIntrinsics()
            self._intrinsics.task = "object detection"
        self._intrinsics.update_with_defaults()

        self._picam2 = Picamera2(self._imx500.camera_num)
        cam_config = self._picam2.create_preview_configuration(
            controls={"FrameRate": self._intrinsics.inference_rate},
            buffer_count=12,
        )
        self._picam2.start(cam_config, show_preview=False)

        if self._intrinsics.preserve_aspect_ratio:
            self._imx500.set_auto_aspect_ratio()

        self._running = True
        logger.info("Camera started — streaming detections")

    def stop(self) -> None:
        """Stop the camera stream and release resources."""
        self._running = False
        if self._picam2 is not None:
            self._picam2.stop()
            self._picam2.close()
            logger.info("Camera stopped")

    def run_loop(self) -> None:
        """Blocking loop: poll for detections and enqueue crops.

        Call this from a background thread. Exits when stop() is called.
        """
        if self._picam2 is None:
            raise RuntimeError("Camera not started — call start() first")

        consecutive_errors = 0
        while self._running:
            try:
                self._poll_once()
                consecutive_errors = 0
            except Exception:
                consecutive_errors += 1
                logger.exception("Error during camera poll (%d consecutive)", consecutive_errors)
                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    logger.critical(
                        "Reached %d consecutive errors — backing off %.0fs",
                        consecutive_errors,
                        BACKOFF_SLEEP_SECONDS,
                    )
                    time.sleep(BACKOFF_SLEEP_SECONDS)
                    consecutive_errors = 0
                else:
                    time.sleep(0.5)

    def _poll_once(self) -> None:
        """Capture one frame, parse detections, and enqueue any valid crops."""
        with self._picam2.captured_request() as request:
            metadata = request.get_metadata()
            np_outputs = self._imx500.get_outputs(metadata, add_batch=True)
            if np_outputs is None:
                return

            detections = self._parse_detections(np_outputs, metadata)
            if not detections:
                return

            array = request.make_array("main")
            frame_h, frame_w = array.shape[:2]

            for box, label, conf in detections:
                crop = self._crop_detection(array, box, frame_w, frame_h)
                if crop is not None:
                    self._queue.put(Detection(label=label, confidence=conf, crop=crop))
                    logger.debug("Queued detection: %s (%.2f)", label, conf)

    def _parse_detections(
        self,
        np_outputs: list[np.ndarray],
        metadata: dict[str, Any],
    ) -> list[tuple[tuple[int, int, int, int], str, float]]:
        """Extract valid detections from NPU output tensors.

        Returns a list of (box, label, confidence) tuples where box is
        (x, y, w, h) in frame pixel coordinates.
        """
        boxes = np_outputs[0][0]
        scores = np_outputs[1][0]
        classes = np_outputs[2][0]

        input_w, input_h = self._imx500.get_input_size()

        if getattr(self._intrinsics, "bbox_normalization", False):
            boxes = boxes / input_h

        if getattr(self._intrinsics, "bbox_order", "yx") == "xy":
            boxes = boxes[:, [1, 0, 3, 2]]

        results: list[tuple[tuple[int, int, int, int], str, float]] = []

        for box, score, cls_id in zip(boxes, scores, classes):
            score_f = float(score)
            if score_f < self._confidence:
                continue

            cls_int = int(cls_id)
            label = COCO_LABELS.get(cls_int)
            if label is None or label not in self._allowed_labels:
                continue

            converted = self._imx500.convert_inference_coords(box, metadata, self._picam2)
            x, y, w, h = (int(v) for v in converted)
            results.append(((x, y, w, h), label, score_f))

        return results

    @staticmethod
    def _crop_detection(
        array: np.ndarray,
        box: tuple[int, int, int, int],
        frame_w: int,
        frame_h: int,
    ) -> Image.Image | None:
        """Crop the bounding box from the frame array.

        Returns None if the box is degenerate or fully out of bounds.
        """
        x, y, w, h = box

        # Clamp to frame boundaries
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(frame_w, x + w)
        y1 = min(frame_h, y + h)

        if x1 <= x0 or y1 <= y0:
            logger.debug("Skipping degenerate crop: (%d,%d,%d,%d)", x, y, w, h)
            return None

        cropped = array[y0:y1, x0:x1]
        return Image.fromarray(cropped)


def _run_standalone(config_path: Path) -> None:
    """Standalone test: print detections to console."""
    import yaml

    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    det_queue: queue.Queue[Detection] = queue.Queue(maxsize=50)
    camera = Camera(config=config, output_queue=det_queue)

    try:
        camera.start()
        logger.info("Listening for detections — Ctrl+C to stop")
        start_time = time.monotonic()

        while True:
            try:
                camera._poll_once()
            except Exception:
                logger.exception("Poll error")
                time.sleep(0.5)
                continue

            while not det_queue.empty():
                det = det_queue.get_nowait()
                elapsed = time.monotonic() - start_time
                logger.info(
                    "[%.1fs] %s (%.2f) crop=%dx%d",
                    elapsed,
                    det.label,
                    det.confidence,
                    det.crop.width,
                    det.crop.height,
                )
    except KeyboardInterrupt:
        logger.info("Interrupted — shutting down")
    finally:
        camera.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Van Gogh camera detection test")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/config.yaml"),
        help="Path to config.yaml (default: config/config.yaml)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s %(name)s: %(message)s",
    )

    # Allow running from project root
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    _run_standalone(args.config)
