# Gap Analysis and Assumption Verification

The following items were verified against primary sources before any code is written.

---

### 1. Pi Zero 2W is quad-core, not dual-core

**Confirmed.** RP3A0 SiP: 4× ARM Cortex-A53 @ 1 GHz, 512 MB LPDDR2.
The "2" denotes hardware revision, not core count.

**RAM ceiling:** 512 MB hard limit. The RAM chip is stacked inside the RP3A0
package and cannot be upgraded. Swap on SD card is a last resort, not a
design assumption.

Source: Raspberry Pi Foundation product page; PiCockpit hardware deep-dive.

---

### 2. IMX500 detection runs on the sensor, not the Pi CPU

**Confirmed.** The Sony IMX500 contains an integrated AI accelerator that
processes inference entirely on-sensor and returns bounding-box metadata to
the host via `picamera2`. The Pi CPU is not involved in detection inference.

**Installation requirement:** `imx500-all` and `imx500-tools` via `apt`.
Pre-packaged `.rpk` model files at `/usr/share/imx500-models/`.
Recommended model: `imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk`.

**Pi Zero 2W note:** Camera connector uses a 22-pin 0.5mm pitch CSI connector.
A 22-to-15-pin adapter cable is required. This is a **hardware prerequisite**.

Source: Raspberry Pi AI Camera documentation; Adafruit; RidgeRun (September 2025).

---

### 3. rembg model selection and RAM impact

**Original claim:** "rembg with U2-Net, ~170 MB model"

**Verified and corrected:**

- `u2net.onnx` — 176 MB on disk; ~300–400 MB RAM during inference.
- `u2net_human_seg.onnx` — same size, trained for human segmentation. **Preferred.**
- `silueta.onnx` — 43 MB, fallback if RAM pressure is severe.
- `u2netp.onnx` — lightweight variant, lower quality.

**RAM concern is real.** OS (~87 MB) + picamera2 + rembg (~300 MB peak) + TFLite
will likely exceed 512 MB without careful sequencing.

**Mitigation strategy:**
- Run rembg and TFLite **sequentially**: rembg first, then TFLite — never concurrently.
- Default to `u2net_human_seg`; fall back to `silueta` on OOM.
- Set swap to 512 MB as a safety net.
- Monitor RSS at each stage in Sprint 3.

Source: rembg GitHub; HuggingFace model repository.

---

### 4. Style transfer model: what actually exists

**Original claim:** "Quantised INT8 TFLite fast-style model (Johnson architecture)"

**Corrected:** Johnson's models are PyTorch/Lua Torch files. No ready-made INT8
TFLite version exists without a non-trivial export pipeline.

**What actually exists:** Google Magenta arbitrary-image-stylization INT8 models:

```
style_predict_quantized.tflite  (~600 KB)
style_transform_quantized.tflite (~9.5 MB)
```

See `docs/plan/install.md` for download URLs.

**Two-stage pipeline:**
1. **Style prediction**: 256×256 style image → `(1, 1, 1, 100)` style bottleneck.
2. **Style transform**: bottleneck + 384×384 content image → styled image.

The style bottleneck is **pre-computed once at startup** and cached.

**Inference time on Cortex-A53:** Realistically **30–90 seconds** for the
transform stage. Full pipeline (crop → rembg → style → composite → display)
is **60–120 seconds** end-to-end. This is acceptable given the display refresh
is 20–25 s and the scene update is not time-critical.

Source: TensorFlow Lite style transfer overview; TF blog post (April 2020);
Magenta GitHub.

---

### 5. Inky Impression 13.3" refresh time

**Original claim:** "15–30 seconds for a full refresh"

**Corrected:** 2025 Edition (Spectra 6 E Ink): ~12 s core refresh at 25–50°C;
**20–25 s** for a complete real-world cycle including SPI transfer. Cooler
temperatures increase refresh time.

**Older hardware note:** Pre-2025 Inky Impression 13.3" panels take 30–40 s typical.
Check `inky` library version and board revision at startup.

**GPIO note:** Button C on the 13.3" model is on GPIO 25, not GPIO 16.

Source: Pimoroni product page; Adafruit; Pimoroni getting-started guide.

---

### 6. Camera ribbon cable: physical prerequisite gap

**Gap identified — not in original plan.**

Pi Zero 2W uses a **22-pin 0.5mm pitch** CSI connector. The AI Camera ships
with a 15-pin cable for full-sized Pi boards. A **22-pin to 15-pin adapter
cable** is required. This is a **hard prerequisite**.

---

### 7. IMX500 model format: `.rpk`, not `.tflite`

**Gap identified — original plan implied TFLite for the IMX500.**

IMX500 NPU models use Sony's proprietary `.rpk` format loaded by `picamera2`'s
`IMX500` class at initialisation. Entirely separate from TFLite models used
on the Pi CPU for style transfer. No conversion needed — installed via `apt`.

Source: Raspberry Pi AI Camera documentation; RidgeRun guide (September 2025).

---

### 8. Van Gogh "Café Terrace at Night" — copyright status

**Clarification.** Van Gogh died in 1890. His works are in the public domain
globally. High-resolution digital reproductions are freely available (Wikimedia
Commons, Google Arts & Culture). No licensing concern.
