"""Shared test fixtures for the Van Gogh Living Scene test suite.

Hardware stub preamble
----------------------
The sys.modules stubs below are installed before any src.* import occurs so
that pytest collection succeeds on CI runners (GitHub Actions, ubuntu-latest)
where hardware packages are not installed.

Each stub block is guarded by a try/import: if the real package IS available
(e.g. on the target Pi) it is left untouched and production behaviour is
unchanged.

Packages stubbed and the src module that triggers the need:
  * picamera2, picamera2.devices, picamera2.devices.imx500
      -> src/camera.py  (deferred imports inside Camera.start())
  * inky, inky.auto
      -> src/display.py (deferred import inside Display._init_hardware())
  * rembg
      -> src/isolator.py (deferred imports inside create_session / remove_background)
  * ai_edge_litert, ai_edge_litert.interpreter
      -> src/styler.py  (deferred imports inside Styler methods)
  * systemd, systemd.daemon
      -> src/main.py    (deferred import inside Application._watchdog_loop())
"""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PIL import Image

# ---------------------------------------------------------------------------
# Hardware package stubs — installed only when the real package is absent
# ---------------------------------------------------------------------------

# --- picamera2 (src/camera.py) ---
try:
    import picamera2  # noqa: F401 — side-effect: prove import works or fall through to mock
except ImportError:
    _picamera2 = MagicMock()
    sys.modules["picamera2"] = _picamera2
    sys.modules["picamera2.devices"] = MagicMock()
    sys.modules["picamera2.devices.imx500"] = MagicMock()

# --- inky (src/display.py) ---
try:
    import inky  # noqa: F401 — side-effect: prove import works or fall through to mock
except ImportError:
    _inky = MagicMock()
    sys.modules["inky"] = _inky
    sys.modules["inky.auto"] = MagicMock()

# --- rembg (src/isolator.py) ---
try:
    import rembg  # noqa: F401 — side-effect: prove import works or fall through to mock
except ImportError:
    sys.modules["rembg"] = MagicMock()

# --- ai_edge_litert (src/styler.py) ---
try:
    import ai_edge_litert  # noqa: F401 — side-effect: prove import works or fall through to mock
except ImportError:
    sys.modules["ai_edge_litert"] = MagicMock()
    sys.modules["ai_edge_litert.interpreter"] = MagicMock()

# --- systemd (src/main.py) ---
try:
    import systemd  # noqa: F401 — side-effect: prove import works or fall through to mock
except ImportError:
    sys.modules["systemd"] = MagicMock()
    sys.modules["systemd.daemon"] = MagicMock()

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def sample_config() -> dict:
    """Return a minimal valid config dict for testing."""
    return {
        "display": {"width": 1600, "height": 1200, "saturation": 0.5},
        "paths": {
            "background": "assets/backgrounds/van_gogh_cafe.jpg",
            "slots": "assets/slots/cafe_terrace_slots.json",
            "style_predict_model": "models/style/style_predict_int8.tflite",
            "style_transform_model": "models/style/style_transform_int8.tflite",
            "style_image": "assets/backgrounds/van_gogh_cafe.jpg",
        },
        "detection": {
            "model": "/usr/share/imx500-models/"
            "imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk",
            "confidence": 0.6,
            "labels": ["person", "cat", "dog"],
        },
        "presence": {
            "entering_frames": 8,
            "exiting_frames": 30,
            "ghost_ttl_seconds": 300,
        },
        "rembg": {"model_name": "u2net_human_seg"},
        "style": {"content_size": 384, "predict_size": 256, "num_threads": 4},
        "memory": {"rss_warning_mb": 460},
        "logging": {"level": "INFO"},
    }


@pytest.fixture
def tmp_dir():
    """Provide a temporary directory that is cleaned up after the test."""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def small_rgb_image() -> Image.Image:
    """Return a small 64x64 RGB test image."""
    return Image.new("RGB", (64, 64), color=(128, 64, 32))


@pytest.fixture
def small_rgba_image() -> Image.Image:
    """Return a small 64x64 RGBA test image."""
    return Image.new("RGBA", (64, 64), color=(128, 64, 32, 200))


@pytest.fixture
def valid_slots_json(tmp_dir: Path) -> Path:
    """Write a valid slots JSON file and return its path."""
    slots = [
        {"id": "slot_a", "x": 100, "y": 200, "width": 160, "height": 300},
        {"id": "slot_b", "x": 500, "y": 400, "width": 200, "height": 250},
    ]
    path = tmp_dir / "test_slots.json"
    path.write_text(json.dumps(slots), encoding="utf-8")
    return path


@pytest.fixture
def valid_background(tmp_dir: Path) -> Path:
    """Create a valid 1600x1200 JPEG background image and return its path."""
    img = Image.new("RGB", (1600, 1200), color=(80, 120, 60))
    path = tmp_dir / "test_bg.jpg"
    img.save(path, format="JPEG")
    return path


@pytest.fixture
def valid_png_background(tmp_dir: Path) -> Path:
    """Create a valid 1600x1200 PNG background image and return its path."""
    img = Image.new("RGB", (1600, 1200), color=(80, 120, 60))
    path = tmp_dir / "test_bg.png"
    img.save(path, format="PNG")
    return path
