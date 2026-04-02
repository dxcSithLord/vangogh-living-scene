"""Slot management for the Van Gogh Living Scene.

Loads slot definitions from JSON, validates against image dimensions,
and provides assign/release operations for placing figures in the scene.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# SEC-12: Maximum JSON file size to prevent resource exhaustion (OWASP A04)
_MAX_SLOTS_FILE_BYTES: int = 1_048_576  # 1 MB


@dataclass
class Slot:
    """A named position in the background where a figure can be placed."""

    id: str
    x: int
    y: int
    width: int
    height: int
    occupied: bool = False


class SlotManager:
    """Loads, validates, and manages slot assignments."""

    def __init__(self, slots_path: Path, image_width: int, image_height: int) -> None:
        self._slots: dict[str, Slot] = {}
        self._image_width = image_width
        self._image_height = image_height
        self._load(slots_path)

    def _load(self, slots_path: Path) -> None:
        """Load slot definitions from JSON and validate each one."""
        if not slots_path.is_file():
            raise FileNotFoundError(f"Slots file not found: {slots_path.name}")

        file_size = slots_path.stat().st_size
        if file_size > _MAX_SLOTS_FILE_BYTES:
            raise ValueError(
                f"Slots file exceeds size limit ({file_size} > {_MAX_SLOTS_FILE_BYTES} bytes)"
            )

        with slots_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("Slots JSON must be a list of slot objects")

        for entry in data:
            slot = self._parse_slot(entry)
            self._validate_bounds(slot)
            self._slots[slot.id] = slot
            logger.debug("Loaded slot '%s' at (%d, %d) %dx%d", slot.id, slot.x, slot.y,
                         slot.width, slot.height)

        logger.info("Loaded %d slot(s) from %s", len(self._slots), slots_path.name)

    @staticmethod
    def _parse_slot(entry: dict) -> Slot:
        """Parse a single slot entry, validating required fields."""
        required = ("id", "x", "y", "width", "height")
        for field in required:
            if field not in entry:
                raise ValueError(f"Slot entry missing required field: {field}")

        return Slot(
            id=str(entry["id"]),
            x=int(entry["x"]),
            y=int(entry["y"]),
            width=int(entry["width"]),
            height=int(entry["height"]),
        )

    def _validate_bounds(self, slot: Slot) -> None:
        """Ensure the slot rectangle fits within the background image."""
        if slot.x < 0 or slot.y < 0:
            raise ValueError(f"Slot '{slot.id}' has negative coordinates")
        if slot.width <= 0 or slot.height <= 0:
            raise ValueError(f"Slot '{slot.id}' has non-positive dimensions")
        if slot.x + slot.width > self._image_width:
            raise ValueError(
                f"Slot '{slot.id}' exceeds image width "
                f"({slot.x + slot.width} > {self._image_width})"
            )
        if slot.y + slot.height > self._image_height:
            raise ValueError(
                f"Slot '{slot.id}' exceeds image height "
                f"({slot.y + slot.height} > {self._image_height})"
            )

    def assign_slot(self) -> Slot | None:
        """Return the first free slot, marking it occupied. None if all full."""
        for slot in self._slots.values():
            if not slot.occupied:
                slot.occupied = True
                logger.info("Assigned slot '%s'", slot.id)
                return slot
        logger.warning("No free slots available")
        return None

    def release_slot(self, slot_id: str) -> None:
        """Mark a slot as free."""
        if slot_id not in self._slots:
            logger.error("Cannot release unknown slot '%s'", slot_id)
            return
        self._slots[slot_id].occupied = False
        logger.info("Released slot '%s'", slot_id)

    def get_slot(self, slot_id: str) -> Slot | None:
        """Return a slot by ID, or None if not found."""
        return self._slots.get(slot_id)

    @property
    def all_slots(self) -> list[Slot]:
        """Return all slots (both free and occupied)."""
        return list(self._slots.values())

    @property
    def free_count(self) -> int:
        """Number of currently unoccupied slots."""
        return sum(1 for s in self._slots.values() if not s.occupied)
