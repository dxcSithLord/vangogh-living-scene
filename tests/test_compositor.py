"""Tests for src/compositor.py."""

from pathlib import Path

import pytest
from PIL import Image

from src.compositor import Compositor
from src.slots import Slot, SlotManager


class TestMagicByteValidation:
    """Compositor should reject files that fail magic byte checks."""

    def test_rejects_text_file_as_image(self, tmp_dir: Path) -> None:
        fake = tmp_dir / "fake.png"
        fake.write_text("this is not an image", encoding="utf-8")
        slot_mgr = _make_slot_manager(tmp_dir)
        with pytest.raises(ValueError, match="not a recognised image format"):
            Compositor(background_path=fake, slot_manager=slot_mgr)

    def test_rejects_missing_file(self, tmp_dir: Path) -> None:
        slot_mgr = _make_slot_manager(tmp_dir)
        with pytest.raises(FileNotFoundError):
            Compositor(background_path=tmp_dir / "nonexistent.png", slot_manager=slot_mgr)

    def test_accepts_valid_jpeg(self, valid_background: Path, tmp_dir: Path) -> None:
        slot_mgr = _make_slot_manager(tmp_dir)
        comp = Compositor(background_path=valid_background, slot_manager=slot_mgr)
        assert comp.background_size == (1600, 1200)

    def test_accepts_valid_png(self, valid_png_background: Path, tmp_dir: Path) -> None:
        slot_mgr = _make_slot_manager(tmp_dir)
        comp = Compositor(background_path=valid_png_background, slot_manager=slot_mgr)
        assert comp.background_size == (1600, 1200)


class TestCompositing:
    """Compositor should correctly add/remove figures and render."""

    def test_render_empty_scene(self, valid_background: Path, tmp_dir: Path) -> None:
        slot_mgr = _make_slot_manager(tmp_dir)
        comp = Compositor(background_path=valid_background, slot_manager=slot_mgr)
        scene = comp.render()
        assert scene.size == (1600, 1200)
        assert scene.mode == "RGB"

    def test_add_and_remove_figure(self, valid_background: Path, tmp_dir: Path) -> None:
        slot_mgr = _make_slot_manager(tmp_dir)
        comp = Compositor(background_path=valid_background, slot_manager=slot_mgr)
        slot = slot_mgr.all_slots[0]
        figure = Image.new("RGBA", (100, 200), color=(255, 0, 0, 128))
        comp.add_figure(slot, figure)
        scene = comp.render()
        assert scene.size == (1600, 1200)
        comp.remove_figure(slot.id)


def _make_slot_manager(tmp_dir: Path) -> SlotManager:
    """Create a SlotManager with a simple test slot."""
    import json
    slots = [{"id": "test_slot", "x": 0, "y": 0, "width": 200, "height": 300}]
    path = tmp_dir / "slots.json"
    path.write_text(json.dumps(slots), encoding="utf-8")
    return SlotManager(slots_path=path, image_width=1600, image_height=1200)
