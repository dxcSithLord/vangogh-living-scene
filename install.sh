#!/usr/bin/env bash
# install.sh — Van Gogh Living Scene installer
# Run on Raspberry Pi OS Lite 64-bit (Bookworm)
# Standards: NIST SI-7, OWASP A08, FIPS 140-3 (SHA-256 integrity),
#            CIS L2 (core dump restriction), NIST SC-28 (file permissions)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# --- SEC-10: Restrict core dumps (CIS L2) ---
ulimit -c 0

echo "=== Installing system packages ==="
sudo apt update
sudo apt install -y \
    imx500-all \
    imx500-models \
    python3-picamera2 \
    python3-pip \
    python3-venv \
    git

echo "=== Creating Python virtual environment ==="
python3 -m venv venv --system-site-packages
# shellcheck disable=SC1091
source venv/bin/activate

echo "=== Installing Python packages ==="
python3 -m pip install --upgrade pip
# SEC-04: Hash-pinned install for supply chain integrity (OWASP A08, FIPS 140-3)
python3 -m pip install --require-hashes -r requirements.lock

echo "=== Downloading style transfer models ==="
mkdir -p models/style

PREDICT_URL="https://storage.googleapis.com/download.tensorflow.org/models/tflite/task_library/style_transfer/android/magenta_arbitrary-image-stylization-v1-256_int8_prediction_1.tflite"
TRANSFORM_URL="https://storage.googleapis.com/download.tensorflow.org/models/tflite/task_library/style_transfer/android/magenta_arbitrary-image-stylization-v1-256_int8_transfer_1.tflite"

# --- SEC-01: SHA-256 checksums for model integrity (NIST SI-7, FIPS 140-3) ---
PREDICT_SHA256="af6ad4b2e7aeba0675f32636082ab915ced5375229a3f8aff7e714c6213f5ed2"
TRANSFORM_SHA256="7a1550643cf034a4d813c0aa276976cd15da4141b4f1ec3631db1d0d9c8e2cd1"

verify_checksum() {
    local file="$1"
    local expected="$2"
    local actual
    actual="$(sha256sum "$file" | awk '{print $1}')"
    if [ "$actual" != "$expected" ]; then
        echo "CRITICAL: Checksum mismatch for $file"
        echo "  Expected: $expected"
        echo "  Actual:   $actual"
        rm -f "$file"
        return 1
    fi
    echo "Checksum verified: $file"
}

if [ ! -f models/style/style_predict_int8.tflite ]; then
    curl -L "$PREDICT_URL" -o models/style/style_predict_int8.tflite
    echo "Downloaded style_predict_int8.tflite"
else
    echo "style_predict_int8.tflite already exists"
fi
verify_checksum models/style/style_predict_int8.tflite "$PREDICT_SHA256"

if [ ! -f models/style/style_transform_int8.tflite ]; then
    curl -L "$TRANSFORM_URL" -o models/style/style_transform_int8.tflite
    echo "Downloaded style_transform_int8.tflite"
else
    echo "style_transform_int8.tflite already exists"
fi
verify_checksum models/style/style_transform_int8.tflite "$TRANSFORM_SHA256"

echo "=== Pre-downloading rembg model ==="
python3 -c "from rembg import new_session; new_session('u2net_human_seg')"

echo "=== Configuring swap (512 MB) ==="
sudo dphys-swapfile swapoff
sudo sed -i 's/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=512/' /etc/dphys-swapfile
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# --- SEC-13: Restrict config file permissions (NIST SC-28) ---
chmod 640 config/config.yaml

echo "=== Creating vangogh system user ==="
if ! id -u vangogh >/dev/null 2>&1; then
    sudo useradd --system --create-home --shell /usr/sbin/nologin vangogh
    echo "Created system user: vangogh"
else
    echo "User vangogh already exists"
fi

echo "=== Setting directory permissions ==="
# vangogh user needs read access to project and write access to log dir
sudo chown -R vangogh:vangogh "$SCRIPT_DIR"
sudo chmod -R u=rwX,g=rX,o= "$SCRIPT_DIR"

sudo mkdir -p /var/log/vangogh
sudo chown vangogh:vangogh /var/log/vangogh
sudo chmod 750 /var/log/vangogh

# Add vangogh to groups needed for hardware access (camera, SPI, GPIO, I2C)
sudo usermod -aG video,spi,gpio,i2c vangogh

echo "=== Installing systemd service (SEC-03) ==="
sudo cp "$SCRIPT_DIR/vangogh_scene.service" /etc/systemd/system/vangogh_scene.service
sudo chmod 644 /etc/systemd/system/vangogh_scene.service
sudo systemctl daemon-reload
sudo systemctl enable vangogh_scene.service
echo "Service installed and enabled (not started)"

echo "=== Configuring journald log limit (RG-07) ==="
# Prevent log-driven SD card fill on constrained storage
if ! grep -q "SystemMaxUse=50M" /etc/systemd/journald.conf 2>/dev/null; then
    echo "SystemMaxUse=50M" | sudo tee -a /etc/systemd/journald.conf >/dev/null
    sudo systemctl restart systemd-journald
    echo "journald SystemMaxUse set to 50M"
else
    echo "journald SystemMaxUse already configured"
fi

echo "=== Installation complete ==="
echo "Start the service with: sudo systemctl start vangogh_scene.service"
echo "View logs with: journalctl -u vangogh_scene.service -f"
