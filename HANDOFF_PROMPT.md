# Claude Code handoff prompt — Van Gogh Living Scene

Copy and paste this as your first message when starting a Claude Code session
on this project. It gives Claude Code everything it needs to pick up where
the planning left off.

---

## Paste this into Claude Code:

```
I am continuing development of the "vangogh-living-scene" project.
Please read CLAUDE.md and PROJECT_PLAN.md before doing anything else.

Project summary: A Raspberry Pi Zero 2W application that uses a Raspberry Pi
AI Camera (Sony IMX500) to detect people or animals entering a room, applies
Van Gogh brushstroke style transfer to their isolated image, and composites
them into a Van Gogh café scene displayed on a Pimoroni Inky Impression 13.3"
e-ink display. When subjects leave, they are removed from the scene.

Key constraints:
- Pi Zero 2W: 4× ARM Cortex-A53, 512 MB RAM — memory management is critical
- All processing offline, no network required at runtime
- Detection is free (runs on IMX500 NPU, not Pi CPU)
- Style transfer uses Google Magenta INT8 TFLite models (two-stage pipeline)
- Background removal uses rembg with u2net_human_seg ONNX model
- Display refresh takes 20–25 seconds — latency is acceptable

Current status: [UPDATE THIS LINE — e.g. "Sprint 1 not started" or
"Sprint 2 in progress, camera.py complete, presence.py pending"]

Please start by reading CLAUDE.md and PROJECT_PLAN.md. Then tell me:
1. What you understand the current task to be
2. Which files you need to read before writing any code
3. Your plan for the next change, before making it

Do not write any code until you have confirmed the plan with me.
```

---

## Notes for the handoff

- Always update the "Current status" line above before starting a new session.
- The CLAUDE.md file is the single source of truth for working rules. If you
  discover a rule needs updating, update CLAUDE.md as part of that session.
- ARCHITECTURE.md should be updated at the end of each sprint to reflect what
  was actually built (it will be created in Sprint 4, but notes can be added
  to CLAUDE.md in the meantime).
- The models in `models/style/` are not in git (too large). Run `install.sh`
  on a fresh clone to download them.
- The `assets/backgrounds/cafe_terrace.png` file is also not in git — it is
  user-supplied. It must be a 1600×1200 RGB PNG.

---

## Quick session checklist

Before each Claude Code session:

- [ ] Update "Current status" in the prompt above
- [ ] Note which sprint you are in
- [ ] Note any blockers or decisions from the last session
- [ ] Have the Pi Zero 2W accessible via SSH if testing Sprint 2 or later
- [ ] Confirm the background image is in `assets/backgrounds/cafe_terrace.png`
```
