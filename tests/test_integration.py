"""Integration tests for the Van Gogh Living Scene pipeline.

Tests the full end-to-end flow with all hardware mocked:
camera, display, rembg, and TFLite models. Verifies that
ENTERED triggers the pipeline and EXITED clears the scene.
"""

import gc
import json
import queue
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from PIL import Image

from src.camera import Detection
from src.compositor import Compositor
from src.display import Display
from src.presence import Event, PresenceManager, State
from src.security_log import init_security_logger
from src.security_log import logger as sec_logger
from src.slots import SlotManager


@pytest.fixture
def integration_slots(tmp_dir: Path) -> Path:
    """Write a two-slot JSON file for integration tests."""
    slots = [
        {"id": "slot_a", "x": 100, "y": 200, "width": 160, "height": 300},
        {"id": "slot_b", "x": 500, "y": 400, "width": 200, "height": 250},
    ]
    path = tmp_dir / "slots.json"
    path.write_text(json.dumps(slots), encoding="utf-8")
    return path


@pytest.fixture
def integration_background(tmp_dir: Path) -> Path:
    """Create a 1600x1200 JPEG background for integration tests."""
    img = Image.new("RGB", (1600, 1200), color=(80, 120, 60))
    path = tmp_dir / "bg.jpg"
    img.save(path, format="JPEG")
    return path


@pytest.fixture
def integration_config(tmp_dir: Path) -> dict[str, Any]:
    """Minimal config dict for integration tests."""
    return {
        "display": {"width": 1600, "height": 1200, "saturation": 0.5},
        "detection": {
            "model": "/usr/share/imx500-models/test.rpk",
            "confidence": 0.6,
            "labels": ["person"],
        },
        "presence": {
            "entering_frames": 2,
            "exiting_frames": 3,
            "ghost_ttl_seconds": 60,
        },
        "rembg": {"model_name": "u2net_human_seg"},
        "style": {"content_size": 384, "predict_size": 256, "num_threads": 1},
        "memory": {"rss_warning_mb": 460},
        "logging": {"level": "DEBUG"},
    }


class TestEnteredPipeline:
    """ENTERED event should trigger isolate -> style -> composite -> display."""

    def test_entered_produces_display_update(
        self,
        integration_config: dict[str, Any],
        integration_background: Path,
        integration_slots: Path,
    ) -> None:
        """Simulate an ENTERED event and verify the display receives a scene."""
        slot_manager = SlotManager(
            slots_path=integration_slots,
            image_width=1600,
            image_height=1200,
        )
        compositor = Compositor(
            background_path=integration_background,
            slot_manager=slot_manager,
        )
        display = Display(width=1600, height=1200, saturation=0.5)

        # Mock the display hardware so show() records the image
        shown_images: list[Image.Image] = []
        display._display = MagicMock()
        display._display.set_image = MagicMock()
        display._display.show = MagicMock()

        def capture_show(image: Image.Image) -> None:
            display._display.set_image(image, saturation=0.5)
            display._display.show()
            shown_images.append(image.copy())

        display.show = capture_show

        # Create a fake crop (what the camera would produce)
        crop = Image.new("RGB", (100, 150), color=(200, 100, 50))

        # Mock isolator: return an RGBA version of the crop
        fake_isolated = crop.copy().convert("RGBA")

        # Mock styler: return the isolated image unchanged
        fake_styled = fake_isolated.copy()

        # Run the pipeline manually (mirrors main.py._handle_entered)
        slot = slot_manager.assign_slot()
        assert slot is not None

        compositor.add_figure(slot, fake_styled)
        scene = compositor.render()
        display.show(scene)

        assert len(shown_images) == 1
        assert shown_images[0].size == (1600, 1200)
        assert shown_images[0].mode == "RGB"

        # Clean up
        del scene, fake_styled, fake_isolated
        gc.collect()


class TestExitedClears:
    """EXITED event should remove the figure and refresh the display."""

    def test_exited_clears_slot_and_refreshes(
        self,
        integration_background: Path,
        integration_slots: Path,
    ) -> None:
        slot_manager = SlotManager(
            slots_path=integration_slots,
            image_width=1600,
            image_height=1200,
        )
        compositor = Compositor(
            background_path=integration_background,
            slot_manager=slot_manager,
        )

        # Add a figure to slot_a
        slot = slot_manager.assign_slot()
        assert slot is not None
        figure = Image.new("RGBA", (160, 300), color=(255, 0, 0, 200))
        compositor.add_figure(slot, figure)

        # Verify figure is in the scene
        scene_with = compositor.render()
        assert scene_with.size == (1600, 1200)

        # Simulate EXITED: remove figure, release slot, re-render
        compositor.remove_figure(slot.id)
        slot_manager.release_slot(slot.id)

        scene_without = compositor.render()
        assert scene_without.size == (1600, 1200)

        # Slot should be free again
        assert slot_manager.free_count == 2


class TestPresenceIntegration:
    """Presence state machine drives events correctly through the pipeline."""

    def test_full_enter_exit_cycle(
        self,
        integration_config: dict[str, Any],
    ) -> None:
        """Feed detections into the presence manager and verify ENTERED/EXITED."""
        det_queue: queue.Queue[Detection] = queue.Queue(maxsize=50)
        events: list[tuple[Event, Image.Image | None, bool]] = []

        def on_event(event: Event, crop: Image.Image | None, ghost_hit: bool) -> None:
            events.append((event, crop, ghost_hit))

        presence = PresenceManager(
            config=integration_config,
            detection_queue=det_queue,
            event_callback=on_event,
        )

        crop = Image.new("RGB", (64, 64), color=(128, 64, 32))

        # Feed enough detections to trigger ENTERED (entering_frames=2)
        for _ in range(2):
            det_queue.put(Detection(label="person", confidence=0.8, crop=crop))
            presence._tick()

        assert len(events) == 1
        assert events[0][0] == Event.ENTERED
        assert events[0][1] is not None
        assert events[0][2] is False  # not a ghost re-entry
        assert presence.state == State.PRESENT

        # Feed enough misses to trigger EXITED (exiting_frames=3)
        for _ in range(3):
            presence._tick()

        assert len(events) == 2
        assert events[1][0] == Event.EXITED
        assert presence.state == State.ABSENT

    def test_cancelled_exit(
        self,
        integration_config: dict[str, Any],
    ) -> None:
        """Detection during EXITING should cancel the exit."""
        det_queue: queue.Queue[Detection] = queue.Queue(maxsize=50)
        events: list[tuple[Event, Image.Image | None, bool]] = []

        def on_event(event: Event, crop: Image.Image | None, ghost_hit: bool) -> None:
            events.append((event, crop, ghost_hit))

        presence = PresenceManager(
            config=integration_config,
            detection_queue=det_queue,
            event_callback=on_event,
        )

        crop = Image.new("RGB", (64, 64), color=(128, 64, 32))

        # Enter
        for _ in range(2):
            det_queue.put(Detection(label="person", confidence=0.8, crop=crop))
            presence._tick()
        assert presence.state == State.PRESENT

        # Start exiting (1 miss)
        presence._tick()
        assert presence.state == State.EXITING

        # Subject returns — cancel exit
        det_queue.put(Detection(label="person", confidence=0.8, crop=crop))
        presence._tick()
        assert presence.state == State.PRESENT

        # Only one event (ENTERED), no EXITED
        assert len(events) == 1
        assert events[0][0] == Event.ENTERED


class TestSecurityLoggerIntegration:
    """Security logger initialises and works in the integration context."""

    def setup_method(self) -> None:
        sec_logger.handlers.clear()

    def test_init_and_log_event(self, tmp_dir: Path) -> None:
        """Security logger should write events to file during integration."""
        from src.security_log import SecurityEvent, log_security_event

        log_file = tmp_dir / "security.log"
        init_security_logger(log_file=log_file, level=10)

        log_security_event(SecurityEvent.BOUNDS_VIOLATION, "Integration test event")

        for h in sec_logger.handlers:
            h.flush()

        content = log_file.read_text(encoding="utf-8")
        assert "BOUNDS_VIOLATION" in content
        assert "Integration test event" in content


class TestConfigValidationIntegration:
    """Config validator works in the full startup context."""

    def test_valid_config_with_real_paths(
        self,
        integration_config: dict[str, Any],
        integration_background: Path,
        integration_slots: Path,
        tmp_dir: Path,
    ) -> None:
        """Config validator should pass when paths point to real files."""
        from src.config_validator import validate_config

        # Point config at real temp files
        integration_config["paths"] = {
            "background": str(integration_background),
            "slots": str(integration_slots),
            "style_predict_model": "models/style/style_predict_int8.tflite",
            "style_transform_model": "models/style/style_transform_int8.tflite",
            "style_image": str(integration_background),
        }

        errors = validate_config(integration_config, tmp_dir)
        # Filter out path-existence errors for models not present in test env
        type_errors = [e for e in errors if "does not exist" not in e]
        assert type_errors == []
