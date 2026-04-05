"""Compositor module for the Van Gogh Living Scene.

Manages the scene: loads a background image, composites styled figures
into assigned slots, and renders the final image for display.
"""

import argparse
import logging
import sys
from pathlib import Path

from PIL import Image

# SEC-14: Explicit pixel limit to prevent decompression bombs (NIST SI-10).
# 25 million pixels allows up to ~5000x5000 — well above 1600x1200 display.
Image.MAX_IMAGE_PIXELS = 25_000_000

# SEC-16: Accepted magic bytes for image validation (DISA-STIG V-222577).
_IMAGE_MAGIC: dict[str, bytes] = {
    "PNG": b"\x89PNG\r\n\x1a\n",
    "JPEG": b"\xff\xd8\xff",
}

# Allow running as script from project root
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.slots import Slot, SlotManager

logger = logging.getLogger(__name__)


class Compositor:
    """Composites styled figures onto a background image."""

    def __init__(self, background_path: Path, slot_manager: SlotManager) -> None:
        self._background = self._load_background(background_path)
        self._slot_manager = slot_manager
        self._figures: dict[str, Image.Image] = {}

    @staticmethod
    def _load_background(path: Path) -> Image.Image:
        """Load and validate the background image."""
        if not path.is_file():
            raise FileNotFoundError(f"Background image not found: {path.name}")

        # SEC-16: Validate file type via magic bytes before loading
        with path.open("rb") as raw:
            header = raw.read(8)
        if not any(header.startswith(magic) for magic in _IMAGE_MAGIC.values()):
            raise ValueError(f"File is not a recognised image format: {path.name}")

        image = Image.open(path)
        image.load()  # force full decode
        if image.mode != "RGB":
            image = image.convert("RGB")

        logger.info("Loaded background: %s (%dx%d)", path.name, image.width, image.height)
        return image

    def add_figure(self, slot: Slot, figure: Image.Image) -> None:
        """Place a styled RGBA figure into the given slot.

        The figure is resized to fit the slot dimensions.
        """
        if figure.mode != "RGBA":
            logger.warning("Figure is not RGBA — converting")
            figure = figure.convert("RGBA")

        resized = figure.resize((slot.width, slot.height), Image.LANCZOS)
        self._figures[slot.id] = resized
        logger.info("Added figure to slot '%s'", slot.id)

    def remove_figure(self, slot_id: str) -> None:
        """Remove a figure from the scene."""
        if slot_id in self._figures:
            del self._figures[slot_id]
            logger.info("Removed figure from slot '%s'", slot_id)

    def render(self) -> Image.Image:
        """Composite all active figures onto the background and return the result."""
        scene = self._background.copy()

        for slot_id, figure in self._figures.items():
            slot = self._slot_manager.get_slot(slot_id)
            if slot is None:
                logger.warning("Figure references unknown slot '%s' — skipping", slot_id)
                continue
            # Paste using alpha channel as mask for transparency
            scene.paste(figure, (slot.x, slot.y), mask=figure)
            logger.debug("Composited slot '%s' at (%d, %d)", slot_id, slot.x, slot.y)

        logger.info("Rendered scene with %d figure(s)", len(self._figures))
        return scene

    @property
    def background_size(self) -> tuple[int, int]:
        """Return (width, height) of the background image."""
        return self._background.size


def _run_debug(config_path: Path) -> None:
    """Debug mode: load background, render with slot outlines, display on Inky."""
    import yaml

    from src.display import Display

    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    project_root = Path(__file__).resolve().parent.parent
    bg_path = project_root / config["paths"]["background"]
    slots_path = project_root / config["paths"]["slots"]
    display_cfg = config["display"]

    slot_manager = SlotManager(
        slots_path=slots_path,
        image_width=display_cfg["width"],
        image_height=display_cfg["height"],
    )

    compositor = Compositor(background_path=bg_path, slot_manager=slot_manager)

    # Draw slot outlines for debug visualisation
    scene = compositor.render()
    from PIL import ImageDraw

    draw = ImageDraw.Draw(scene)
    for slot in slot_manager.all_slots:
        draw.rectangle(
            [slot.x, slot.y, slot.x + slot.width, slot.y + slot.height],
            outline="red",
            width=3,
        )
        draw.text((slot.x + 4, slot.y + 4), slot.id, fill="red")

    logger.info("Debug: rendering scene with slot outlines on display")
    display = Display(
        width=display_cfg["width"],
        height=display_cfg["height"],
        saturation=display_cfg.get("saturation", 0.5),
    )
    display.show(scene)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Van Gogh compositor debug view")
    parser.add_argument(
        "--debug", action="store_true", help="Render background with slot outlines on Inky"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/config.yaml"),
        help="Path to config.yaml (default: config/config.yaml)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(name)s: %(message)s")

    if args.debug:
        _run_debug(args.config)
    else:
        parser.print_help()
