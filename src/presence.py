"""Presence state machine for the Van Gogh Living Scene.

Consumes detections from the camera queue and emits clean
ENTERED/EXITED events with debounce logic and ghost re-entry caching.
"""

from __future__ import annotations

import argparse
import enum
import logging
import queue
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PIL import Image

if TYPE_CHECKING:
    from src.camera import Detection

logger = logging.getLogger(__name__)


class State(enum.Enum):
    """Presence states for a single tracked subject."""

    ABSENT = "ABSENT"
    ENTERING = "ENTERING"
    PRESENT = "PRESENT"
    EXITING = "EXITING"


class Event(enum.Enum):
    """Events emitted by the presence state machine."""

    ENTERED = "ENTERED"
    EXITED = "EXITED"


# Type alias for event callbacks: receives (event, optional crop image, ghost_hit flag).
EventCallback = Callable[[Event, Image.Image | None, bool], None]


class _GhostCache:
    """TTL cache for the last crop, enabling fast re-entry without re-processing.

    This cache tracks *raw crops* and gates the ghost_hit signal sent to the
    event callback. The Application class in main.py maintains a separate cache
    of *styled images* (_last_styled) to avoid re-running the expensive
    isolator and styler stages. The two caches work together: presence decides
    whether a re-entry qualifies as a ghost hit; main decides what to display.
    """

    def __init__(self, ttl_seconds: float) -> None:
        self._ttl = ttl_seconds
        self._crop: Image.Image | None = None
        self._timestamp: float = 0.0

    def store(self, crop: Image.Image) -> None:
        """Cache a crop with the current timestamp."""
        self._crop = crop
        self._timestamp = time.monotonic()
        logger.debug("Ghost cache updated (TTL=%.0fs)", self._ttl)

    def retrieve(self) -> Image.Image | None:
        """Return the cached crop if still within TTL, else None."""
        if self._crop is None:
            return None
        age = time.monotonic() - self._timestamp
        if age > self._ttl:
            logger.debug("Ghost cache expired (age=%.1fs)", age)
            self._crop = None
            return None
        logger.debug("Ghost cache hit (age=%.1fs)", age)
        return self._crop

    def clear(self) -> None:
        """Explicitly clear the cache."""
        self._crop = None


class PresenceManager:
    """State machine that debounces raw detections into ENTERED/EXITED events.

    Consumes Detection tuples from the camera queue. Tracks consecutive
    detection/non-detection frames to filter noise. Emits events via
    a callback.

    State transitions:
        ABSENT   ──(detection)──►  ENTERING
        ENTERING ──(N frames)───►  fires ENTERED, goes to PRESENT
        ENTERING ──(gap)────────►  ABSENT
        PRESENT  ──(no detect)──►  EXITING
        EXITING  ──(M frames)───►  fires EXITED, goes to ABSENT
        EXITING  ──(detection)──►  PRESENT  (cancelled exit)
    """

    def __init__(
        self,
        config: dict[str, Any],
        detection_queue: queue.Queue[Detection],
        event_callback: EventCallback,
    ) -> None:
        pres_cfg = config["presence"]
        self._entering_threshold: int = int(pres_cfg["entering_frames"])
        self._exiting_threshold: int = int(pres_cfg["exiting_frames"])
        ghost_ttl: float = float(pres_cfg["ghost_ttl_seconds"])

        self._queue = detection_queue
        self._callback = event_callback
        self._ghost = _GhostCache(ghost_ttl)

        self._state = State.ABSENT
        self._consecutive_detections: int = 0
        self._consecutive_misses: int = 0
        self._last_crop: Image.Image | None = None
        self._running = False

        logger.info(
            "PresenceManager: enter=%d frames, exit=%d frames, ghost_ttl=%.0fs",
            self._entering_threshold,
            self._exiting_threshold,
            ghost_ttl,
        )

    @property
    def state(self) -> State:
        """Current state of the presence machine."""
        return self._state

    def stop(self) -> None:
        """Signal the tick loop to stop."""
        self._running = False

    def run_loop(self, poll_interval: float = 0.2) -> None:
        """Blocking loop: drain the queue and advance state each tick.

        Call from a background thread. Exits when stop() is called.

        Args:
            poll_interval: Seconds between ticks. Default 0.2s = 5 Hz.
        """
        self._running = True
        logger.info("Presence loop started (poll=%.2fs)", poll_interval)

        while self._running:
            try:
                self._tick()
            except Exception:
                logger.exception("Error in presence tick")
            time.sleep(poll_interval)

        logger.info("Presence loop stopped")

    def _tick(self) -> None:
        """Drain the queue and advance the state machine once."""
        detected = False
        latest_crop: Image.Image | None = None

        # Drain all pending detections — keep the last crop
        while True:
            try:
                detection = self._queue.get_nowait()
                detected = True
                latest_crop = detection.crop
            except queue.Empty:
                break

        if latest_crop is not None:
            self._last_crop = latest_crop

        self._advance(detected)

    def _advance(self, detected: bool) -> None:
        """Advance the state machine based on whether a detection occurred."""
        prev = self._state

        if self._state == State.ABSENT:
            if detected:
                self._consecutive_detections = 1
                self._state = State.ENTERING
                logger.debug("ABSENT → ENTERING (1/%d)", self._entering_threshold)

        elif self._state == State.ENTERING:
            if detected:
                self._consecutive_detections += 1
                logger.debug(
                    "ENTERING: %d/%d",
                    self._consecutive_detections,
                    self._entering_threshold,
                )
                if self._consecutive_detections >= self._entering_threshold:
                    self._state = State.PRESENT
                    self._consecutive_misses = 0
                    ghost_hit = self._ghost.retrieve() is not None
                    if ghost_hit:
                        logger.info("Ghost re-entry detected — signalling cache hit")
                    logger.info("ENTERING → PRESENT — firing ENTERED")
                    self._callback(Event.ENTERED, self._last_crop, ghost_hit)
            else:
                # Gap during entering — reset
                self._consecutive_detections = 0
                self._state = State.ABSENT
                logger.debug("ENTERING → ABSENT (gap in detections)")

        elif self._state == State.PRESENT:
            if detected:
                # Still here — keep ghost cache fresh with latest crop
                self._consecutive_misses = 0
                if self._last_crop is not None:
                    self._ghost.store(self._last_crop)
            else:
                self._consecutive_misses = 1
                self._state = State.EXITING
                logger.debug("PRESENT → EXITING (1/%d)", self._exiting_threshold)

        elif self._state == State.EXITING:
            if detected:
                # Subject returned — cancel exit
                self._consecutive_misses = 0
                self._state = State.PRESENT
                logger.debug("EXITING → PRESENT (subject returned)")
            else:
                self._consecutive_misses += 1
                logger.debug(
                    "EXITING: %d/%d",
                    self._consecutive_misses,
                    self._exiting_threshold,
                )
                if self._consecutive_misses >= self._exiting_threshold:
                    # Cache the last crop before clearing
                    if self._last_crop is not None:
                        self._ghost.store(self._last_crop)
                    self._state = State.ABSENT
                    self._last_crop = None
                    self._consecutive_detections = 0
                    logger.info("EXITING → ABSENT — firing EXITED")
                    self._callback(Event.EXITED, None, False)

        if self._state != prev:
            logger.debug("State: %s → %s", prev.value, self._state.value)


def _run_standalone(config_path: Path) -> None:
    """Standalone test with camera: prints ENTERED/EXITED events."""
    import yaml

    from src.camera import Camera

    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    det_queue: queue.Queue[Detection] = queue.Queue(maxsize=50)

    def on_event(event: Event, crop: Image.Image | None, ghost_hit: bool) -> None:
        crop_info = f"{crop.width}x{crop.height}" if crop else "no crop"
        ghost_info = " [ghost]" if ghost_hit else ""
        logger.info("EVENT: %s (%s%s)", event.value, crop_info, ghost_info)

    camera = Camera(config=config, output_queue=det_queue)
    presence = PresenceManager(
        config=config,
        detection_queue=det_queue,
        event_callback=on_event,
    )

    import threading

    try:
        camera.start()

        # Run camera polling in a background thread
        cam_thread = threading.Thread(
            target=camera.run_loop,
            name="camera",
            daemon=True,
        )
        cam_thread.start()

        logger.info("Listening for presence events — Ctrl+C to stop")
        presence.run_loop()
    except KeyboardInterrupt:
        logger.info("Interrupted — shutting down")
    finally:
        presence.stop()
        camera.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Van Gogh presence detection test")
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

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    _run_standalone(args.config)
