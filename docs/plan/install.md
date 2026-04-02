# Installation: Dependencies and Model Download

## System packages

```bash
# On Pi, after flashing Raspberry Pi OS Lite 64-bit
sudo apt update
sudo apt install -y \
    imx500-all \
    imx500-models \
    python3-picamera2 \
    python3-pip \
    python3-venv \
    git
```

## Python virtual environment

```bash
python3 -m venv venv --system-site-packages
# --system-site-packages needed to access picamera2 which is apt-installed
source venv/bin/activate
```

## Python packages

```bash
pip install \
    rembg[cpu] \
    tflite-runtime \
    pillow \
    inky[rpi] \
    pyyaml \
    numpy
```

**Note:** Use `tflite-runtime` only — the full `tensorflow` package is too
large for the Pi Zero 2W.

## Model download

```bash
mkdir -p models/style

# Style prediction model (INT8, ~600 KB)
curl -L "https://storage.googleapis.com/download.tensorflow.org/models/tflite/task_library/style_transfer/android/magenta_arbitrary-image-stylization-v1-256_int8_prediction_1.tflite" \
    -o models/style/style_predict_int8.tflite

# Style transform model (INT8, ~9.5 MB)
curl -L "https://storage.googleapis.com/download.tensorflow.org/models/tflite/task_library/style_transfer/android/magenta_arbitrary-image-stylization-v1-256_int8_transfer_1.tflite" \
    -o models/style/style_transform_int8.tflite

# rembg model (auto-downloaded on first run; to pre-download):
python3 -c "from rembg import new_session; new_session('u2net_human_seg')"
```

## Swap file (safety net for RAM pressure)

```bash
sudo dphys-swapfile swapoff
sudo sed -i 's/CONF_SWAPSIZE=100/CONF_SWAPSIZE=512/' /etc/dphys-swapfile
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```
