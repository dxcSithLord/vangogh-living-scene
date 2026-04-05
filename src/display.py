"""Display module for the Van Gogh Living Scene.

Thin wrapper around the inky library. Handles image conversion
and refresh for the Pimoroni Inky Impression 13.3" 7-colour e-ink.
"""

import logging
import time
from typing import Protocol

from PIL import Image

logger = logging.getLogger(__name__)


class DisplayProtocol(Protocol):
    """Structural subset of the `inky.auto` display used by this module."""

    WHITE: int
    resolution: tuple[int, int]

    def set_border(self, colour: int) -> None: ...
    def set_image(self, image: Image.Image, saturation: float = ...) -> None: ...
    def show(self) -> None: ...


class Display:
    """Manages the Inky Impression e-ink display."""

    def __init__(self, width: int, height: int, saturation: float = 0.5) -> None:
        self._width = width
        self._height = height
        self._saturation = saturation
        self._display: DisplayProtocol | None = None

    def _init_hardware(self) -> None:
        """Lazy-initialise the inky display on first use."""
        if self._display is not None:
            return
        try:
            from inky.auto import auto

            display: DisplayProtocol = auto()
            display.set_border(display.WHITE)
            logger.info(
                "Inky display initialised: %dx%d",
                display.resolution[0],
                display.resolution[1],
            )
            self._display = display
        except ImportError:
            logger.error("inky library not available — display will not function")
            raise
        except RuntimeError as exc:
            logger.error("Failed to initialise Inky hardware: %s", exc)
            raise

    def show(self, image: Image.Image) -> None:
        """Convert image to display palette and send to the Inky.

        Args:
            image: A PIL Image, expected to be the display resolution (1600x1200).
                   Will be resized if dimensions do not match.
        """
        self._init_hardware()

        if image.size != (self._width, self._height):
            logger.warning(
                "Image size %s does not match display %dx%d — resizing",
                image.size,
                self._width,
                self._height,
            )
            image = image.resize((self._width, self._height), Image.Resampling.LANCZOS)

        if image.mode != "RGB":
            image = image.convert("RGB")

        display = self._display
        if display is None:
            raise RuntimeError("Display hardware not initialised after _init_hardware()")

        logger.info("Starting display refresh")
        start = time.monotonic()

        display.set_image(image, saturation=self._saturation)
        display.show()

        elapsed = time.monotonic() - start
        logger.info("Display refresh completed in %.1f seconds", elapsed)
