# Revised Architecture

## System diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ Pi Zero 2W (4× Cortex-A53, 512 MB RAM, Raspberry Pi OS Lite)   │
│                                                                 │
│  picamera2                                                      │
│  ├── IMX500 NPU: SSD MobileNetV2 detection (.rpk)  [~0 ms CPU] │
│  └── Pi CPU: frame crop from full 12MP image                   │
│                                                                 │
│  rembg (onnxruntime CPU)                                        │
│  └── u2net_human_seg.onnx (~176 MB) → RGBA subject PNG         │
│      [load once, session kept open across subjects]             │
│                                                                 │
│  TFLite (ai-edge-litert, 4 threads)                            │
│  ├── style_predict: cached at startup (~0 ms after init)       │
│  └── style_transform: per-subject (~30–90 s on A53)            │
│                                                                 │
│  Pillow compositor                                              │
│  └── paste styled PNG into fixed slot on 1600×1200 background  │
│                                                                 │
│  inky library → SPI → Inky Impression 13.3" (20–25 s refresh)  │
└─────────────────────────────────────────────────────────────────┘
```

## Memory management sequence (critical)

```
startup:
  load background image (Pillow, ~6 MB in RAM)
  pre-compute style bottleneck (TFLite predict, ~50 MB peak, then free)
  open rembg session (keep open — 300 MB)

on ENTERING confirmed:
  run rembg on crop → RGBA PNG
  [do NOT free rembg session — reloading costs 5–10 s]
  allocate TFLite transform interpreter (~100 MB)
  run style transform
  free TFLite interpreter + gc.collect()
  composite and display
```

## End-to-end timing estimate (Pi Zero 2W)

| Stage | Estimated time |
|-------|---------------|
| rembg background removal | 15–30 s |
| TFLite style transform | 30–90 s |
| Pillow composite | < 1 s |
| Inky display refresh | 20–25 s |
| **Total** | **65–146 s** |

This is acceptable — the scene update is not time-critical.
