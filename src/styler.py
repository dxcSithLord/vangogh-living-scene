"""Style transfer module for the Van Gogh Living Scene.

Two-stage Magenta TFLite pipeline using Google LiteRT (ai-edge-litert):
  1. Style predict — run once at startup to compute a style bottleneck.
  2. Style transform — run per subject to apply the style.

The transform interpreter is created and destroyed per call to control
memory on the 512 MB device. The alpha channel is preserved through
the pipeline (style is applied to RGB only).
"""

import argparse
import gc
import logging
import resource
import sys
from pathlib import Path

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def _rss_mb() -> float:
    """Return current RSS in megabytes."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_maxrss / 1024.0


class Styler:
    """Applies Van Gogh brushstroke style to RGBA figures."""

    def __init__(
        self,
        style_image_path: Path,
        predict_model_path: Path,
        transform_model_path: Path,
        predict_size: int = 256,
        content_size: int = 384,
        num_threads: int = 4,
        rss_warning_mb: int = 460,
    ) -> None:
        self._transform_model_path = transform_model_path
        self._content_size = content_size
        self._num_threads = num_threads
        self._rss_warning_mb = rss_warning_mb

        self._style_bottleneck = self._compute_bottleneck(
            style_image_path,
            predict_model_path,
            predict_size,
        )

    def _compute_bottleneck(
        self,
        style_image_path: Path,
        predict_model_path: Path,
        predict_size: int,
    ) -> np.ndarray:
        """Load the style image and compute the style bottleneck vector.

        The predict interpreter is created, used once, and immediately freed.
        """
        from ai_edge_litert.interpreter import Interpreter

        if not style_image_path.is_file():
            raise FileNotFoundError(f"Style image not found: {style_image_path.name}")
        if not predict_model_path.is_file():
            raise FileNotFoundError(f"Predict model not found: {predict_model_path.name}")

        logger.info("Computing style bottleneck from '%s'", style_image_path.name)

        style_img = Image.open(style_image_path).convert("RGB")
        style_img = style_img.resize((predict_size, predict_size), Image.Resampling.LANCZOS)
        style_array = np.array(style_img, dtype=np.float32)[np.newaxis] / 255.0

        interpreter = Interpreter(
            model_path=str(predict_model_path),
            num_threads=self._num_threads,
        )
        interpreter.allocate_tensors()

        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()

        interpreter.set_tensor(input_details[0]["index"], style_array)
        interpreter.invoke()
        bottleneck: np.ndarray = interpreter.get_tensor(output_details[0]["index"]).copy()

        del interpreter
        gc.collect()

        logger.info(
            "Style bottleneck computed: shape %s (RSS: %.0f MB)",
            bottleneck.shape,
            _rss_mb(),
        )
        return bottleneck

    def stylize(self, image: Image.Image) -> Image.Image:
        """Apply the cached style to an RGBA figure.

        The alpha channel is separated before styling and re-applied after.
        The transform interpreter is created and destroyed each call.

        Args:
            image: RGBA PIL Image (the isolated figure).

        Returns:
            RGBA PIL Image with Van Gogh style applied to RGB channels.
        """
        if image.mode != "RGBA":
            raise ValueError(f"Expected RGBA image, got {image.mode}")

        from ai_edge_litert.interpreter import Interpreter

        if not self._transform_model_path.is_file():
            raise FileNotFoundError(f"Transform model not found: {self._transform_model_path.name}")

        logger.debug("Styler input: %dx%d (RSS: %.0f MB)", image.width, image.height, _rss_mb())

        # Separate alpha channel
        r, g, b, alpha = image.split()
        rgb = Image.merge("RGB", (r, g, b))

        # Resize to model input size
        original_size = rgb.size
        rgb_resized = rgb.resize(
            (self._content_size, self._content_size),
            Image.Resampling.LANCZOS,
        )
        content_array = np.array(rgb_resized, dtype=np.float32)[np.newaxis] / 255.0

        # Run transform
        interpreter = Interpreter(
            model_path=str(self._transform_model_path),
            num_threads=self._num_threads,
        )
        interpreter.allocate_tensors()

        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()

        interpreter.set_tensor(input_details[0]["index"], content_array)
        interpreter.set_tensor(input_details[1]["index"], self._style_bottleneck)
        interpreter.invoke()

        output = interpreter.get_tensor(output_details[0]["index"])

        # Free interpreter immediately
        del interpreter
        gc.collect()

        rss = _rss_mb()
        if rss > self._rss_warning_mb:
            logger.warning("RSS %.0f MB exceeds warning threshold %d MB", rss, self._rss_warning_mb)

        # Convert output back to PIL
        styled_array = np.squeeze(output)
        styled_array = np.clip(styled_array * 255.0, 0, 255).astype(np.uint8)
        styled_rgb = Image.fromarray(styled_array, mode="RGB")

        # Resize back to original dimensions and re-apply alpha
        styled_rgb = styled_rgb.resize(original_size, Image.Resampling.LANCZOS)
        alpha_resized = alpha.resize(original_size, Image.Resampling.LANCZOS)
        styled_rgba = styled_rgb.copy()
        styled_rgba.putalpha(alpha_resized)

        logger.debug(
            "Styler output: %dx%d RGBA (RSS: %.0f MB)",
            styled_rgba.width,
            styled_rgba.height,
            _rss_mb(),
        )
        return styled_rgba


def _run_standalone(config_path: Path, input_path: Path) -> None:
    """Standalone test: style a single image and save the result."""
    import yaml

    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    project_root = Path(__file__).resolve().parent.parent
    style_cfg = config["style"]
    paths_cfg = config["paths"]

    styler = Styler(
        style_image_path=project_root / paths_cfg["style_image"],
        predict_model_path=project_root / paths_cfg["style_predict_model"],
        transform_model_path=project_root / paths_cfg["style_transform_model"],
        predict_size=style_cfg["predict_size"],
        content_size=style_cfg["content_size"],
        num_threads=style_cfg["num_threads"],
        rss_warning_mb=config["memory"]["rss_warning_mb"],
    )

    input_img = Image.open(input_path).convert("RGBA")
    logger.info(
        "Styling input image: %s (%dx%d)", input_path.name, input_img.width, input_img.height
    )

    styled = styler.stylize(input_img)

    output_path = input_path.with_stem(input_path.stem + "_styled").with_suffix(".png")
    styled.save(output_path)
    logger.info("Saved styled image: %s", output_path.name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Van Gogh style transfer test")
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to input image (RGBA or RGB)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/config.yaml"),
        help="Path to config.yaml (default: config/config.yaml)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(name)s: %(message)s")
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    _run_standalone(args.config, args.input)
