"""Interactive slot definition tool for Van Gogh Living Scene.

Usage:
    python tools/define_slots.py assets/backgrounds/cafe_terrace.png

Opens the background image in a window. Click to place slot centres,
then enter a name and size for each slot. Saves JSON next to the image
as <image_stem>_slots.json (e.g., cafe_terrace_slots.json into assets/slots/).

Requires: Pillow, tkinter (included in most Python installs).
Can run on any machine — does not require Pi hardware.
"""

import json
import logging
import sys
import tkinter as tk
from pathlib import Path
from tkinter import simpledialog

from PIL import Image, ImageDraw, ImageTk

logger = logging.getLogger(__name__)

DEFAULT_SLOT_WIDTH = 160
DEFAULT_SLOT_HEIGHT = 200


class SlotDefiner:
    """Tkinter-based interactive slot placement tool."""

    def __init__(self, image_path: Path, output_dir: Path) -> None:
        self._image_path = image_path
        self._output_dir = output_dir
        self._slots: list[dict] = []

        self._original = Image.open(image_path)
        self._original.load()
        self._img_width, self._img_height = self._original.size

        # Scale to fit screen while preserving aspect ratio
        self._scale = min(1.0, 1200 / self._img_width, 900 / self._img_height)
        self._display_w = int(self._img_width * self._scale)
        self._display_h = int(self._img_height * self._scale)

        self._root = tk.Tk()
        self._root.title(f"Define Slots — {image_path.name}")
        self._root.resizable(False, False)

        self._canvas = tk.Canvas(self._root, width=self._display_w, height=self._display_h)
        self._canvas.pack()

        self._instructions = tk.Label(
            self._root,
            text="Click to place a slot centre. Press 'S' to save and quit. Press 'U' to undo.",
        )
        self._instructions.pack()

        self._canvas.bind("<Button-1>", self._on_click)
        self._root.bind("<Key-s>", lambda _e: self._save_and_quit())
        self._root.bind("<Key-S>", lambda _e: self._save_and_quit())
        self._root.bind("<Key-u>", lambda _e: self._undo())
        self._root.bind("<Key-U>", lambda _e: self._undo())

        self._redraw()

    def _ask_dimension(self, label: str, default: int, maximum: int) -> int | None:
        """Prompt for a dimension value, validating range. Returns None on cancel."""
        raw = simpledialog.askstring(
            f"Slot {label}",
            f"{label} in pixels (1–{maximum}, default {default}):",
            parent=self._root,
        )
        if not raw:
            return default
        if not raw.isdigit():
            logger.warning("Invalid %s input (not a positive integer): %s", label, raw)
            return None
        value = int(raw)
        if value < 1 or value > maximum:
            logger.warning("%s=%d is out of range (1–%d)", label, value, maximum)
            return None
        return value

    def _redraw(self) -> None:
        """Redraw the image with current slot rectangles overlaid."""
        display = self._original.copy()
        if self._scale != 1.0:
            display = display.resize((self._display_w, self._display_h), Image.LANCZOS)

        draw = ImageDraw.Draw(display)
        for slot in self._slots:
            sx = int(slot["x"] * self._scale)
            sy = int(slot["y"] * self._scale)
            sw = int(slot["width"] * self._scale)
            sh = int(slot["height"] * self._scale)
            draw.rectangle([sx, sy, sx + sw, sy + sh], outline="red", width=2)
            draw.text((sx + 2, sy + 2), slot["id"], fill="red")

        self._tk_image = ImageTk.PhotoImage(display)
        self._canvas.create_image(0, 0, anchor=tk.NW, image=self._tk_image)

    def _on_click(self, event: tk.Event) -> None:
        """Handle a click — prompt for slot name and dimensions."""
        # Convert display coords back to original image coords
        img_x = int(event.x / self._scale)
        img_y = int(event.y / self._scale)

        name = simpledialog.askstring("Slot Name", "Enter a name for this slot:", parent=self._root)
        if not name:
            return

        width = self._ask_dimension("Width", DEFAULT_SLOT_WIDTH, self._img_width)
        if width is None:
            return

        height = self._ask_dimension("Height", DEFAULT_SLOT_HEIGHT, self._img_height)
        if height is None:
            return

        # Centre the slot on the click point
        slot_x = max(0, min(img_x - width // 2, self._img_width - width))
        slot_y = max(0, min(img_y - height // 2, self._img_height - height))

        slot = {"id": name, "x": slot_x, "y": slot_y, "width": width, "height": height}
        self._slots.append(slot)
        logger.info("Added slot '%s' at (%d, %d) %dx%d", name, slot_x, slot_y, width, height)
        self._redraw()

    def _undo(self) -> None:
        """Remove the last placed slot."""
        if self._slots:
            removed = self._slots.pop()
            logger.info("Removed slot '%s'", removed["id"])
            self._redraw()

    def _save_and_quit(self) -> None:
        """Write slots JSON and close the window."""
        if not self._slots:
            logger.warning("No slots defined — nothing to save")
            self._root.destroy()
            return

        self._output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self._output_dir / f"{self._image_path.stem}_slots.json"

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(self._slots, f, indent=2)

        logger.info("Saved %d slot(s) to %s", len(self._slots), output_path)
        print(f"Saved {len(self._slots)} slot(s) to {output_path}")
        self._root.destroy()

    def run(self) -> None:
        """Start the tkinter event loop."""
        self._root.mainloop()


def main() -> None:
    """Entry point for the slot definition tool."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <path/to/background.png>")
        sys.exit(1)

    image_path = Path(sys.argv[1])
    if not image_path.is_file():
        print(f"Error: file not found: {image_path.name}")
        sys.exit(1)

    # Default output to assets/slots/ relative to project root
    project_root = Path(__file__).resolve().parent.parent
    output_dir = project_root / "assets" / "slots"

    definer = SlotDefiner(image_path=image_path, output_dir=output_dir)
    definer.run()


if __name__ == "__main__":
    main()
