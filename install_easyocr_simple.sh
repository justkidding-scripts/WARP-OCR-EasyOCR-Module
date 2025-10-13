#!/bin/bash
# Simple EasyOCR Installation Script for WARP OCR
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_NAME="venv_easyocr"

echo "🚀 Installing EasyOCR for WARP OCR System"

# Check for CUDA
HAS_CUDA=false
if nvidia-smi >/dev/null 2>&1; then
    echo "✅ CUDA GPU detected"
    HAS_CUDA=true
else
    echo "🔧 No CUDA GPU - using CPU mode"
fi

# Find Python
PYTHON_CMD=""
for py in python3.11 python3.10 python3.12 python3.13 python3; do
    if command -v "$py" >/dev/null 2>&1; then
        echo "✅ Found $py"
        PYTHON_CMD="$py"
        break
    fi
done

if [[ -z "$PYTHON_CMD" ]]; then
    echo "❌ No Python found"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
rm -rf "$SCRIPT_DIR/$VENV_NAME"
"$PYTHON_CMD" -m venv "$SCRIPT_DIR/$VENV_NAME"

# Activate virtual environment
source "$SCRIPT_DIR/$VENV_NAME/bin/activate"

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip wheel setuptools

# Install PyTorch
echo "🔥 Installing PyTorch..."
if [[ "$HAS_CUDA" == "true" ]]; then
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
else
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

# Install EasyOCR
echo "👁️  Installing EasyOCR..."
pip install easyocr>=1.7.0

# Install additional dependencies
echo "📚 Installing additional dependencies..."
pip install opencv-python-headless>=4.8.0
pip install scikit-image imageio

# Test installation
echo "🧪 Testing EasyOCR..."
python -c "
import easyocr
import torch
import cv2
import numpy as np

print('EasyOCR version:', easyocr.__version__)
print('PyTorch version:', torch.__version__)
print('CUDA available:', torch.cuda.is_available())

# Quick test
print('Initializing EasyOCR Reader...')
reader = easyocr.Reader(['en'])
print('✅ EasyOCR Reader initialized successfully')

# Test with simple image
test_img = np.ones((100, 400, 3), dtype=np.uint8) * 255
cv2.putText(test_img, 'WARP EasyOCR TEST', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

result = reader.readtext(test_img)
print(f'OCR Test: Found {len(result)} text regions')
if result:
    print(f'   Result: {result[0][1]}')

print('🎉 EasyOCR installation successful!')
"

# Update configuration
echo "⚙️  Updating configuration..."
CONFIG_FILE="$HOME/.config/discord_ocr_system.json"
if [[ -f "$CONFIG_FILE" ]]; then
    cp "$CONFIG_FILE" "$CONFIG_FILE.backup"
    python3 -c "
import json
with open('$CONFIG_FILE', 'r') as f:
    config = json.load(f)
config['ocr_engine'] = 'easyocr'
config['easyocr_languages'] = ['en']
config['easyocr_gpu'] = $HAS_CUDA
with open('$CONFIG_FILE', 'w') as f:
    json.dump(config, f, indent=2)
print('Configuration updated')
"
fi

echo ""
echo "🎉 EasyOCR setup completed!"
echo "   Virtual environment: $SCRIPT_DIR/$VENV_NAME"
echo "   To use: source $SCRIPT_DIR/$VENV_NAME/bin/activate"
echo ""
echo "Next: Update launcher script to use this environment"