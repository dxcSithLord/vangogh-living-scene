# Module Responsibilities

## `config.yaml` / config loading

Single source of truth for all tuneable values. Loaded once at startup and
passed as a dataclass or dict to all modules. No module reads the file
directly after startup.

## `camera.py`

- Owns the `picamera2` + `IMX500` lifecycle.
- Fires detection callbacks when the IMX500 returns bounding boxes above
  confidence threshold.
- Crops the subject from the full frame using the bounding box.
- Puts `(label, confidence, crop_image)` tuples onto a `queue.Queue`.
- Does **not** make any decisions about presence state.

## `presence.py`

- Consumes the crop queue from `camera.py`.
- Implements the state machine: ABSENT → ENTERING → PRESENT → EXITING → ABSENT.
- Emits `ENTERED(crop)` and `EXITED()` events to `main.py`.
- Maintains a TTL-based cache of the last styled figure for ghost re-entry.
- Does **not** do any image processing.

**State definitions:**
- `ABSENT` — no detection in current window
- `ENTERING` — detected in last N consecutive frames, not yet confirmed
- `PRESENT` — figure is currently shown on the display
- `EXITING` — subject not seen for M frames; grace period before removal
- (back to `ABSENT` after timeout)

## `isolator.py`

- Wraps rembg.
- Input: PIL Image (the subject crop, any size).
- Output: RGBA PIL Image with background removed.
- Session is passed in (created at startup in `main.py`).
- No state of its own.

## `styler.py`

- Wraps the two-stage Magenta TFLite pipeline.
- At startup: accepts a style image path and computes the style bottleneck
  (cached; only run once).
- Per-subject: accepts an RGBA PIL Image → returns styled RGBA PIL Image.
- Creates and destroys the TFLite transform interpreter per call.
- Preserves the alpha channel (pass through; style is applied to RGB only).

## `compositor.py`

- Owns the current scene state: background image + dict of active figures
  keyed by slot ID.
- `add_figure(slot_id, rgba_image)` → updates scene.
- `remove_figure(slot_id)` → updates scene.
- `render()` → returns a PIL Image of the full composited scene (1600×1200).

## `slots.py`

- Loads `slots.json` for the current background.
- Validates slot coordinates are within image bounds.
- Provides `assign_slot()` → returns the next free slot ID.
- Provides `release_slot(slot_id)`.
- Slot schema: `{"id": "left_table", "x": 420, "y": 680, "width": 160, "height": 200}`

## `display.py`

- Thin wrapper around the `inky` library.
- `show(pil_image)` → converts to display palette and sends to Inky.
- Handles the 7-colour palette quantisation via `inky`'s built-in dithering.
- Logs refresh start and completion times.

## `main.py`

- Entry point. Loads config. Wires all modules together.
- Starts camera loop in a background thread.
- Main thread runs the event loop consuming ENTERED/EXITED events.
- Handles graceful shutdown (SIGTERM, SIGINT).

## `tools/define_slots.py`

- Standalone CLI tool. Can run on any machine with PIL (not Pi-specific).
- Invoked directly: `python tools/define_slots.py path/to/background.png`
  (no `__init__.py` needed — `tools/` is not a Python package).
- Opens the image, prints coordinates as user clicks, writes JSON.
- Slots are named interactively.
- Stores output next to the background file as `<name>_slots.json`.
