"""Main entry point for the Van Gogh Living Scene.

Wires all modules together: config validation, security logging,
camera detection, presence state machine, and the image pipeline
(isolate → style → composite → display).

Handles graceful shutdown via SIGTERM and SIGINT.
"""

import gc
import logging
import queue
import resource
import signal
import sys
import threading
from pathlib import Path
from typing import Any

import yaml
from PIL import Image

from src.camera import Camera, Detection
from src.compositor import Compositor
from src.config_validator import validate_or_exit
from src.display import Display
from src.isolator import create_session, remove_background
from src.presence import Event, PresenceManager
from src.security_log import SecurityEvent, init_security_logger, log_security_event
from src.slots import SlotManager
from src.styler import Styler

logger = logging.getLogger(__name__)

# Watchdog notification interval — systemd expects a ping within WatchdogSec.
_WATCHDOG_INTERVAL_SECONDS: float = 120.0


def _rss_mb() -> float:
    """Return current RSS in megabytes."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_maxrss / 1024.0


class Application:
    """Top-level application that owns all module lifecycles."""

    def __init__(self, config: dict[str, Any], project_root: Path) -> None:
        self._config = config
        self._project_root = project_root
        self._shutdown_event = threading.Event()

        # --- Security logger ---
        log_cfg = config.get("security_log", {})
        log_file_str = log_cfg.get("file")
        log_file = Path(log_file_str) if log_file_str else None
        log_level = getattr(logging, config["logging"]["level"].upper(), logging.INFO)
        init_security_logger(log_file=log_file, level=log_level)

        # --- Slots and compositor ---
        display_cfg = config["display"]
        paths_cfg = config["paths"]

        self._slot_manager = SlotManager(
            slots_path=project_root / paths_cfg["slots"],
            image_width=display_cfg["width"],
            image_height=display_cfg["height"],
        )
        self._compositor = Compositor(
            background_path=project_root / paths_cfg["background"],
            slot_manager=self._slot_manager,
        )
        self._display = Display(
            width=display_cfg["width"],
            height=display_cfg["height"],
            saturation=display_cfg.get("saturation", 0.5),
        )

        # --- rembg session (loaded once, kept alive) ---
        rembg_model = config["rembg"]["model_name"]
        self._rembg_session = create_session(rembg_model)
        logger.info("rembg session ready (RSS: %.0f MB)", _rss_mb())

        # --- Styler (computes bottleneck once) ---
        style_cfg = config["style"]
        self._styler = Styler(
            style_image_path=project_root / paths_cfg["style_image"],
            predict_model_path=project_root / paths_cfg["style_predict_model"],
            transform_model_path=project_root / paths_cfg["style_transform_model"],
            predict_size=style_cfg["predict_size"],
            content_size=style_cfg["content_size"],
            num_threads=style_cfg["num_threads"],
            rss_warning_mb=config["memory"]["rss_warning_mb"],
        )
        logger.info("Styler ready (RSS: %.0f MB)", _rss_mb())

        # --- Camera and presence ---
        self._det_queue: queue.Queue[Detection] = queue.Queue(maxsize=50)
        self._camera = Camera(config=config, output_queue=self._det_queue)
        self._presence = PresenceManager(
            config=config,
            detection_queue=self._det_queue,
            event_callback=self._on_presence_event,
        )

        # Track which slot is currently occupied (single-subject for now).
        self._active_slot_id: str | None = None

    def _on_presence_event(self, event: Event, crop: Image.Image | None) -> None:
        """Handle ENTERED/EXITED events from the presence state machine."""
        if event == Event.ENTERED and crop is not None:
            self._handle_entered(crop)
        elif event == Event.EXITED:
            self._handle_exited()

    def _handle_entered(self, crop: Image.Image) -> None:
        """Process a new subject: isolate → style → composite → display."""
        slot = self._slot_manager.assign_slot()
        if slot is None:
            logger.warning("No free slots — ignoring ENTERED event")
            return

        self._active_slot_id = slot.id
        logger.info("Processing subject for slot '%s' (RSS: %.0f MB)", slot.id, _rss_mb())

        try:
            # 1. Remove background
            isolated = remove_background(crop, session=self._rembg_session)
            logger.info("Isolation complete (RSS: %.0f MB)", _rss_mb())

            # 2. Apply style
            styled = self._styler.stylize(isolated)
            logger.info("Style transfer complete (RSS: %.0f MB)", _rss_mb())

            # Free intermediate images
            del isolated
            gc.collect()

            # 3. Composite into scene
            self._compositor.add_figure(slot, styled)
            scene = self._compositor.render()
            logger.info("Compositing complete (RSS: %.0f MB)", _rss_mb())

            # 4. Display
            self._display.show(scene)
            logger.info("Display updated with subject in slot '%s'", slot.id)

            # Free scene image
            del scene, styled
            gc.collect()

        except Exception:
            logger.exception("Pipeline error for slot '%s'", slot.id)
            log_security_event(
                SecurityEvent.ERROR_THRESHOLD_BREACH,
                f"Pipeline failed for slot '{slot.id}'",
            )
            # Release the slot so it can be reused
            self._slot_manager.release_slot(slot.id)
            self._active_slot_id = None

    def _handle_exited(self) -> None:
        """Remove the subject from the scene and refresh the display."""
        if self._active_slot_id is None:
            return

        slot_id = self._active_slot_id
        self._compositor.remove_figure(slot_id)
        self._slot_manager.release_slot(slot_id)
        self._active_slot_id = None

        scene = self._compositor.render()
        self._display.show(scene)
        logger.info("Subject removed from slot '%s' — display refreshed", slot_id)

        del scene
        gc.collect()

    def run(self) -> None:
        """Start the camera and presence loops. Blocks until shutdown."""
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        self._camera.start()

        cam_thread = threading.Thread(
            target=self._camera.run_loop,
            name="camera",
            daemon=True,
        )
        presence_thread = threading.Thread(
            target=self._presence.run_loop,
            name="presence",
            daemon=True,
        )

        cam_thread.start()
        presence_thread.start()

        logger.info("Van Gogh Living Scene running — waiting for subjects")

        # Main thread: send systemd watchdog pings and wait for shutdown.
        self._watchdog_loop()

        # Shutdown sequence
        logger.info("Shutting down")
        self._presence.stop()
        self._camera.stop()

        presence_thread.join(timeout=5.0)
        cam_thread.join(timeout=5.0)
        logger.info("Shutdown complete")

    def _watchdog_loop(self) -> None:
        """Send systemd watchdog notifications until shutdown is requested."""
        try:
            from systemd.daemon import notify

            has_systemd = True
        except ImportError:
            has_systemd = False

        while not self._shutdown_event.wait(timeout=_WATCHDOG_INTERVAL_SECONDS):
            if has_systemd:
                notify("WATCHDOG=1")
            logger.debug("Watchdog ping (RSS: %.0f MB)", _rss_mb())

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle SIGTERM/SIGINT by signalling the shutdown event."""
        sig_name = signal.Signals(signum).name
        logger.info("Received %s — initiating shutdown", sig_name)
        self._shutdown_event.set()


def main() -> None:
    """Load config, validate, and start the application."""
    project_root = Path(__file__).resolve().parent.parent
    config_path = project_root / "config" / "config.yaml"

    if not config_path.is_file():
        print(f"Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Configure logging
    log_level = config.get("logging", {}).get("level", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    # Validate config — exits on failure
    validate_or_exit(config, project_root)

    app = Application(config=config, project_root=project_root)
    app.run()


if __name__ == "__main__":
    main()
