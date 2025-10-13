#!/bin/bash
# EasyOCR Setup Script for WARP OCR System
# Detects optimal Python version and sets up EasyOCR with CPU/GPU auto-detection

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/easyocr_setup.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"; }
error() { echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE" >&2; }
warn() { echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"; }
info() { echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"; }

# Check if CUDA is available
check_cuda() {
    if command -v nvidia-smi >/dev/null 2>&1; then
        if nvidia-smi >/dev/null 2>&1; then
            log "✅ CUDA GPU detected"
            return 0
        else
            warn "NVIDIA driver not properly installed"
        fi
    fi
    log "🔧 No CUDA GPU available - using CPU mode"
    return 1
}

# Detect best Python version
detect_python_version() {
    local python_versions=("python3.11" "python3.10" "python3.12" "python3.13")
    
    for python in "${python_versions[@]}"; do
        if command -v "$python" >/dev/null 2>&1; then
            local version
            version=$("$python" --version 2>&1 | cut -d' ' -f2)
            log "Found $python (version $version)"
            
            # Test if we can create a virtual environment
            if "$python" -m venv --help >/dev/null 2>&1; then
                echo "$python"
                return 0
            fi
        fi
    done
    
    # Fallback to python3
    if command -v python3 >/dev/null 2>&1; then
        local version
        version=$(python3 --version 2>&1 | cut -d' ' -f2)
        log "Falling back to python3 (version $version)"
        echo "python3"
        return 0
    fi
    
    error "No suitable Python version found"
    return 1
}

# Create optimized virtual environment
create_venv() {
    local python_cmd=$1
    local venv_name=$2
    
    log "Creating virtual environment with $python_cmd..."
    
    # Remove existing venv if present
    if [[ -d "$SCRIPT_DIR/$venv_name" ]]; then
        warn "Removing existing virtual environment..."
        rm -rf "$SCRIPT_DIR/$venv_name"
    fi
    
    # Create new virtual environment
    "$python_cmd" -m venv "$SCRIPT_DIR/$venv_name"
    
    # Activate and upgrade pip
    source "$SCRIPT_DIR/$venv_name/bin/activate"
    pip install --upgrade pip wheel setuptools
    
    log "✅ Virtual environment created: $venv_name"
}

# Install PyTorch based on hardware
install_pytorch() {
    local has_cuda=$1
    
    log "Installing PyTorch..."
    
    if [[ $has_cuda == "true" ]]; then
        info "Installing PyTorch with CUDA support..."
        # Install latest stable PyTorch with CUDA
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    else
        info "Installing PyTorch CPU-only version..."
        # Install CPU-only PyTorch (smaller and faster for CPU-only systems)
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    fi
    
    # Verify PyTorch installation
    python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"
}

# Install EasyOCR and dependencies
install_easyocr() {
    log "Installing EasyOCR and dependencies..."
    
    # Install EasyOCR
    pip install easyocr>=1.7.0
    
    # Install additional image processing libraries for better performance
    pip install opencv-python-headless>=4.8.0
    pip install Pillow>=9.0.0
    pip install numpy>=1.21.0
    
    # Install additional dependencies that might be needed
    pip install scikit-image
    pip install imageio
    
    log "✅ EasyOCR installation completed"
}

# Test EasyOCR installation
test_easyocr() {
    log "Testing EasyOCR installation..."
    
    python -c "
import easyocr
import torch
import cv2
import numpy as np

print('EasyOCR version:', easyocr.__version__)
print('PyTorch version:', torch.__version__)
print('CUDA available:', torch.cuda.is_available())

# Test EasyOCR initialization
reader = easyocr.Reader(['en'])
print('✅ EasyOCR Reader initialized successfully')

# Test with a simple image
test_img = np.ones((100, 300, 3), dtype=np.uint8) * 255
cv2.putText(test_img, 'WARP OCR TEST', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

try:
    result = reader.readtext(test_img)
    print(f'✅ OCR Test successful: {len(result)} text regions detected')
    if result:
        print(f'   Sample result: {result[0][1] if result else \"No text\"}')
except Exception as e:
    print(f'❌ OCR Test failed: {e}')
    exit(1)

print('🎉 EasyOCR is working correctly!')
"
}

# Update requirements files
update_requirements() {
    local has_cuda=$1
    
    log "Updating requirements files..."
    
    # Create modular requirements structure
    cat > "$SCRIPT_DIR/requirements-base.txt" << 'EOF'
# Core OCR and Image Processing
opencv-python>=4.8.0
pillow>=9.0.0
pytesseract>=0.3.10
numpy>=1.21.0

# GUI and System Interaction
pyautogui>=0.9.50
keyboard>=0.13.5
psutil>=5.9.0

# Discord Integration
discord.py>=2.3.0
aiohttp>=3.8.0
websockets>=11.0.0
requests>=2.25.0

# Additional utilities
scikit-image>=0.19.0
imageio>=2.22.0
EOF

    if [[ $has_cuda == "true" ]]; then
        cat > "$SCRIPT_DIR/requirements-ocr-gpu.txt" << 'EOF'
# EasyOCR with GPU support
--index-url https://download.pytorch.org/whl/cu118
torch>=2.0.0
torchvision>=0.15.0
torchaudio>=2.0.0
easyocr>=1.7.0
EOF
    else
        cat > "$SCRIPT_DIR/requirements-ocr-cpu.txt" << 'EOF'
# EasyOCR with CPU support
--index-url https://download.pytorch.org/whl/cpu
torch>=2.0.0
torchvision>=0.15.0
torchaudio>=2.0.0
easyocr>=1.7.0
EOF
    fi
    
    # Update main requirements.txt
    cat > "$SCRIPT_DIR/requirements.txt" << 'EOF'
# Base requirements
-r requirements-base.txt

# OCR Engine (uncomment appropriate version)
# For GPU systems:
# -r requirements-ocr-gpu.txt
# For CPU systems:
-r requirements-ocr-cpu.txt
EOF

    log "✅ Requirements files updated"
}

# Update configuration to use EasyOCR
update_config() {
    log "Updating WARP OCR configuration..."
    
    # Update system config
    local config_file="$HOME/.config/discord_ocr_system.json"
    if [[ -f "$config_file" ]]; then
        # Create backup
        cp "$config_file" "$config_file.backup.$(date +%s)"
        
        # Update OCR engine setting
        python3 -c "
import json
import sys

config_file = '$config_file'
try:
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    config['ocr_engine'] = 'easyocr'
    config['easyocr_languages'] = ['en']
    config['easyocr_gpu'] = $(check_cuda && echo 'true' || echo 'false')
    config['easyocr_batch_size'] = 1
    config['easyocr_workers'] = 1
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print('✅ Configuration updated successfully')
except Exception as e:
    print(f'❌ Error updating config: {e}')
    sys.exit(1)
"
    else
        warn "Config file not found, will be created on first run"
    fi
}

# Main setup function
main() {
    log "🚀 Starting EasyOCR setup for WARP OCR System"
    
    # Create log file
    touch "$LOG_FILE"
    
    # Detect hardware capabilities
    local has_cuda="false"
    if check_cuda; then
        has_cuda="true"
    fi
    
    # Detect best Python version
    local python_cmd
    python_cmd=$(detect_python_version)
    if [[ -z "$python_cmd" ]]; then
        error "Failed to find suitable Python version"
        exit 1
    fi
    
    info "Using Python: $python_cmd"
    info "CUDA support: $has_cuda"
    
    # Create virtual environment for EasyOCR
    create_venv "$python_cmd" "venv_easyocr"
    
    # Install PyTorch
    install_pytorch "$has_cuda"
    
    # Install EasyOCR
    install_easyocr
    
    # Test installation
    test_easyocr
    
    # Update requirements files
    update_requirements "$has_cuda"
    
    # Update configuration
    update_config
    
    log "🎉 EasyOCR setup completed successfully!"
    info "Virtual environment: $SCRIPT_DIR/venv_easyocr"
    info "Log file: $LOG_FILE"
    info "Next steps:"
    info "1. Update launcher script to use venv_easyocr"
    info "2. Restart WARP OCR service"
    info "3. Test OCR with new EasyOCR engine"
}

# Run main function
main "$@"