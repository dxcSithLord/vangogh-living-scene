"""Isolator module for the Van Gogh Living Scene.

Wraps rembg to remove the background from a subject crop. The rembg
session is created once at startup (in main.py) and passed in to avoid
repeated model loading on the 512 MB device.

Input: PIL Image (RGB crop from the camera).
Output: RGBA PIL Image with background removed.
"""

import gc
import logging
import resource
from typing import Any

from PIL import Image

logger = logging.getLogger(__name__)

# Maximum input dimension to prevent excessive memory use on Zero 2W.
_MAX_INPUT_DIMENSION: int = 2048


def _rss_mb() -> float:
    """Return current RSS in megabytes."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_maxrss / 1024.0


def create_session(model_name: str) -> Any:
    """Create a rembg session. Call once at startup and reuse.

    Args:
        model_name: rembg model identifier (e.g. "u2net_human_seg").

    Returns:
        A rembg session object.
    """
    from rembg import new_session

    logger.info("Creating rembg session with model '%s'", model_name)
    session = new_session(model_name)
    logger.info("rembg session ready (RSS: %.0f MB)", _rss_mb())
    return session


def remove_background(image: Image.Image, session: Any) -> Image.Image:
    """Remove the background from a subject crop.

    Args:
        image: RGB PIL Image (the subject crop).
        session: A rembg session (from create_session).

    Returns:
        RGBA PIL Image with the background removed.

    Raises:
        ValueError: If the input image exceeds maximum dimensions.
    """
    if image.width > _MAX_INPUT_DIMENSION or image.height > _MAX_INPUT_DIMENSION:
        raise ValueError(
            f"Input image too large: {image.width}x{image.height} "
            f"(max {_MAX_INPUT_DIMENSION}x{_MAX_INPUT_DIMENSION})"
        )

    if image.mode != "RGB":
        image = image.convert("RGB")

    logger.debug("Isolator input: %dx%d (RSS: %.0f MB)", image.width, image.height, _rss_mb())

    from rembg import remove

    result: Image.Image = remove(image, session=session)

    if result.mode != "RGBA":
        result = result.convert("RGBA")

    logger.debug(
        "Isolator output: %dx%d RGBA (RSS: %.0f MB)", result.width, result.height, _rss_mb()
    )
    gc.collect()
    return result
