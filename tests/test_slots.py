"""Tests for src/slots.py."""

import json
from pathlib import Path

import pytest

from src.slots import SlotManager


class TestValidSlots:
    """Valid slot JSON should load and function correctly."""

    def test_loads_valid_slots(self, valid_slots_json: Path) -> None:
        sm = SlotManager(slots_path=valid_slots_json, image_width=1600, image_height=1200)
        assert len(sm.all_slots) == 2

    def test_assign_and_release(self, valid_slots_json: Path) -> None:
        sm = SlotManager(slots_path=valid_slots_json, image_width=1600, image_height=1200)
        slot = sm.assign_slot()
        assert slot is not None
        assert slot.occupied is True
        sm.release_slot(slot.id)
        assert sm.get_slot(slot.id).occupied is False

    def test_all_slots_occupied(self, valid_slots_json: Path) -> None:
        sm = SlotManager(slots_path=valid_slots_json, image_width=1600, image_height=1200)
        sm.assign_slot()
        sm.assign_slot()
        assert sm.assign_slot() is None
        assert sm.free_count == 0


class TestOversizedJSON:
    """JSON files exceeding size limit should be rejected."""

    def test_rejects_oversized_json(self, tmp_dir: Path) -> None:
        path = tmp_dir / "big.json"
        # Write > 1 MB of valid JSON
        data = [{"id": f"s{i}", "x": 0, "y": 0, "width": 10, "height": 10}
                for i in range(50_000)]
        path.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(ValueError, match="size limit"):
            SlotManager(slots_path=path, image_width=1600, image_height=1200)


class TestNegativeCoords:
    """Slots with negative coordinates should be rejected."""

    def test_rejects_negative_x(self, tmp_dir: Path) -> None:
        slots = [{"id": "bad", "x": -10, "y": 100, "width": 50, "height": 50}]
        path = tmp_dir / "neg.json"
        path.write_text(json.dumps(slots), encoding="utf-8")
        with pytest.raises(ValueError, match="negative"):
            SlotManager(slots_path=path, image_width=1600, image_height=1200)


class TestOutOfBounds:
    """Slots extending beyond image bounds should be rejected."""

    def test_rejects_slot_beyond_width(self, tmp_dir: Path) -> None:
        slots = [{"id": "wide", "x": 1500, "y": 0, "width": 200, "height": 100}]
        path = tmp_dir / "oob.json"
        path.write_text(json.dumps(slots), encoding="utf-8")
        with pytest.raises(ValueError, match="exceeds image width"):
            SlotManager(slots_path=path, image_width=1600, image_height=1200)

    def test_rejects_slot_beyond_height(self, tmp_dir: Path) -> None:
        slots = [{"id": "tall", "x": 0, "y": 1100, "width": 100, "height": 200}]
        path = tmp_dir / "oob.json"
        path.write_text(json.dumps(slots), encoding="utf-8")
        with pytest.raises(ValueError, match="exceeds image height"):
            SlotManager(slots_path=path, image_width=1600, image_height=1200)


class TestMissingFields:
    """Slots missing required fields should raise ValueError."""

    def test_missing_id(self, tmp_dir: Path) -> None:
        slots = [{"x": 0, "y": 0, "width": 50, "height": 50}]
        path = tmp_dir / "noid.json"
        path.write_text(json.dumps(slots), encoding="utf-8")
        with pytest.raises(ValueError, match="missing required field"):
            SlotManager(slots_path=path, image_width=1600, image_height=1200)
