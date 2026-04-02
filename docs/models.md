# Model Reference

## Detection (on IMX500 NPU)

- File: `/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk`
- Installed via: `sudo apt install imx500-models`
- Format: Sony `.rpk` (loaded by picamera2 IMX500 class, not by Python directly)
- Classes: COCO 80-class. Relevant: `person` (index 0), `cat` (15), `dog` (16),
  `bird` (14), `horse` (17)

## Style prediction (CPU, LiteRT INT8)

- File: `models/style/style_predict_int8.tflite`
- Size: ~600 KB
- Input: `(1, 256, 256, 3)` float32 style image
- Output: `(1, 1, 1, 100)` style bottleneck
- Run: **once at startup**, result cached
- Runtime: `ai-edge-litert` (Google LiteRT, successor to tflite-runtime)
- Import: `from ai_edge_litert.interpreter import Interpreter`

## Style transform (CPU, LiteRT INT8)

- File: `models/style/style_transform_int8.tflite`
- Size: ~9.5 MB
- Input 0: `(1, 384, 384, 3)` float32 content image
- Input 1: `(1, 1, 1, 100)` style bottleneck
- Output: `(1, 384, 384, 3)` float32 stylised image
- Run: **per subject**, interpreter created and destroyed each time
- Runtime: `ai-edge-litert` (same as style prediction)

## Background removal (CPU, ONNX via rembg)

- Model: `u2net_human_seg` (auto-downloaded to `~/.u2net/` by rembg)
- Size: ~176 MB on disk, ~300 MB peak RAM
- Session: created once at startup, kept open
