#!/bin/bash
# WARP OCR Screenshare Launcher
# Enhanced Discord Screenshare OCR Integration System
#
# Features:
# - Real-time Discord window OCR capture
# - Multiple overlay display modes
# - Discord bot/webhook integration
# - Performance monitoring and optimization
# - Automatic dependency management

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Prefer EasyOCR environment if available, fallback to regular venv
if [[ -d "$SCRIPT_DIR/venv_easyocr" ]]; then
    VENV_DIR="$SCRIPT_DIR/venv_easyocr"
    USING_EASYOCR=true
else
    VENV_DIR="$SCRIPT_DIR/venv"
    USING_EASYOCR=false
fi
LOG_FILE="$SCRIPT_DIR/warp_ocr.log"
PID_FILE="$SCRIPT_DIR/warp_ocr.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE" >&2
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

# Check if running
is_running() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Check system dependencies
check_dependencies() {
    log "Checking system dependencies..."
    
    # Check Python 3
    if ! command -v python3 >&/dev/null; then
        error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check Tesseract
    if ! command -v tesseract >&/dev/null; then
        warn "Tesseract not found. Installing..."
        sudo apt-get update && sudo apt-get install -y tesseract-ocr tesseract-ocr-eng
    fi
    
    # Check xdotool
    if ! command -v xdotool >&/dev/null; then
        warn "xdotool not found. Installing..."
        sudo apt-get install -y xdotool
    fi
    
    # Check X11 display
    if [[ -z "${DISPLAY:-}" ]]; then
        error "No DISPLAY set. Make sure X11 is running and DISPLAY is exported"
        exit 1
    fi
    
    log "System dependencies check completed"
}

# Setup Python virtual environment
setup_venv() {
    log "Setting up Python virtual environment..."
    
    if [[ ! -d "$VENV_DIR" ]]; then
        python3 -m venv "$VENV_DIR"
        log "Virtual environment created"
    fi
    
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    if [[ -f "$SCRIPT_DIR/requirements.txt" ]]; then
        pip install -r "$SCRIPT_DIR/requirements.txt"
        log "Requirements installed from requirements.txt"
    else
        # Install core dependencies
        log "Installing core dependencies..."
        pip install opencv-python pillow pytesseract pyautogui psutil keyboard discord.py aiohttp websockets numpy
    fi
}

# Create config directory
setup_config() {
    local config_dir="$HOME/.config"
    mkdir -p "$config_dir"
    
    # Create default Discord OCR config if it doesn't exist
    local ocr_config="$config_dir/discord_ocr_config.json"
    if [[ ! -f "$ocr_config" ]]; then
        cat > "$ocr_config" << 'EOF'
{
  "webhook_url": null,
  "ocr_interval": 2.0,
  "translation_enabled": false,
  "ocr_timeout": 3.0,
  "enable_overlays": true,
  "enable_performance_monitoring": true,
  "log_level": "INFO"
}
EOF
        info "Created default config at $ocr_config"
        info "Edit this file to add your Discord webhook URL and customize settings"
    fi
    
    # Create system config
    local system_config="$config_dir/discord_ocr_system.json"
    if [[ ! -f "$system_config" ]]; then
        cat > "$system_config" << 'EOF'
{
  "ocr_engine": "tesseract",
  "ocr_timeout": 3.0,
  "ocr_interval": 2.0,
  "discord_bot_token": null,
  "discord_webhook_url": null,
  "auto_launch_discord": true,
  "discord_launch_timeout": 30,
  "wait_for_discord_window": true,
  "enable_overlays": true,
  "enable_performance_monitoring": true,
  "enable_adaptive_control": true,
  "max_cpu_usage": 80,
  "max_memory_usage": 1000,
  "log_level": "INFO"
}
EOF
        info "Created system config at $system_config"
    fi
}

# Launch Discord if enabled
launch_discord() {
    local config_file="$HOME/.config/discord_ocr_system.json"
    local auto_launch_discord=true
    
    # Check configuration for Discord auto-launch
    if [[ -f "$config_file" ]]; then
        auto_launch_discord=$(python3 -c "import json; config=json.load(open('$config_file')); print(str(config.get('auto_launch_discord', True)).lower())" 2>/dev/null || echo "true")
    fi
    
    if [[ "$auto_launch_discord" == "true" ]]; then
        log "Checking Discord status..."
        
        # Activate virtual environment and launch Discord
        source "$VENV_DIR/bin/activate"
        cd "$SCRIPT_DIR"
        
        python3 -c "
import sys
sys.path.append('.')
from discord_launcher import DiscordLauncher
import logging

logging.basicConfig(level=logging.INFO)
launcher = DiscordLauncher()

status = launcher.get_discord_status()
if not status['running']:
    print('🚀 Launching Discord...')
    success = launcher.launch_discord()
    if success:
        launcher.wait_for_discord_window()
        print('✅ Discord is ready for OCR monitoring')
    else:
        print('⚠️  Discord launch failed - continuing with OCR only')
else:
    print('✅ Discord is already running')
"
    else
        info "Discord auto-launch disabled"
    fi
}

# Start the OCR system
start_ocr() {
    if is_running; then
        warn "WARP OCR is already running (PID: $(cat "$PID_FILE"))"
        return 0
    fi
    
    log "Starting WARP OCR Screenshare System..."
    
    if [[ "$USING_EASYOCR" == "true" ]]; then
        info "Using EasyOR virtual environment with PyTorch"
    else
        info "Using standard virtual environment with Tesseract"
    fi
    
    check_dependencies
    setup_venv
    setup_config
    
    # Launch Discord before starting OCR
    launch_discord
    
    source "$VENV_DIR/bin/activate"
    cd "$SCRIPT_DIR"
    
    # Export display for GUI
    export DISPLAY="${DISPLAY:-:0}"
    
    # Start the main system
    nohup python3 complete_discord_ocr_integration.py > "$LOG_FILE" 2>&1 &
    local pid=$!
    echo "$pid" > "$PID_FILE"
    
    # Wait a moment to check if it started successfully
    sleep 2
    if is_running; then
        log "WARP OCR started successfully (PID: $pid)"
        info "Log file: $LOG_FILE"
        info "Use 'stop' to stop the service"
    else
        error "Failed to start WARP OCR. Check log file: $LOG_FILE"
        return 1
    fi
}

# Stop the OCR system
stop_ocr() {
    if ! is_running; then
        warn "WARP OCR is not running"
        return 0
    fi
    
    local pid=$(cat "$PID_FILE")
    log "Stopping WARP OCR (PID: $pid)..."
    
    # Graceful shutdown
    kill -TERM "$pid" 2>/dev/null || true
    
    # Wait for shutdown
    local count=0
    while kill -0 "$pid" 2>/dev/null && [[ $count -lt 10 ]]; do
        sleep 1
        ((count++))
    done
    
    # Force kill if still running
    if kill -0 "$pid" 2>/dev/null; then
        warn "Process didn't terminate gracefully, forcing shutdown..."
        kill -KILL "$pid" 2>/dev/null || true
    fi
    
    rm -f "$PID_FILE"
    log "WARP OCR stopped"
}

# Show status
status_ocr() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        log "WARP OCR is running (PID: $pid)"
        
        # Show resource usage
        if command -v ps >/dev/null; then
            ps -p "$pid" -o pid,ppid,cpu,pmem,etime,cmd 2>/dev/null || true
        fi
    else
        info "WARP OCR is not running"
    fi
}

# Show logs
show_logs() {
    if [[ -f "$LOG_FILE" ]]; then
        tail -n 50 "$LOG_FILE"
    else
        warn "No log file found at $LOG_FILE"
    fi
}

# Interactive mode
interactive_mode() {
    log "WARP OCR Interactive Control Panel"
    info "Available commands: start, stop, status, logs, config, test, quit"
    
    while true; do
        echo
        read -p "WARP OCR > " cmd
        
        case "$cmd" in
            start|s)
                start_ocr
                ;;
            stop|x)
                stop_ocr
                ;;
            status|st)
                status_ocr
                ;;
            logs|l)
                show_logs
                ;;
            config|c)
                info "Config files:"
                info "- System: ~/.config/discord_ocr_system.json"
                info "- Discord: ~/.config/discord_ocr_config.json"
                info "- Overlay: ~/.config/overlay_config.json"
                ;;
            test|t)
                test_ocr
                ;;
            restart|r)
                stop_ocr
                sleep 2
                start_ocr
                ;;
            quit|q|exit)
                log "Goodbye!"
                break
                ;;
            help|h|*)
                echo "Commands:"
                echo "  start, s     - Start WARP OCR"
                echo "  stop, x      - Stop WARP OCR" 
                echo "  status, st   - Show status"
                echo "  logs, l      - Show recent logs"
                echo "  config, c    - Show config file locations"
                echo "  test, t      - Test OCR functionality"
                echo "  restart, r   - Restart service"
                echo "  quit, q      - Exit interactive mode"
                ;;
        esac
    done
}

# Test OCR functionality
test_ocr() {
    log "Testing OCR functionality..."
    
    source "$VENV_DIR/bin/activate" 2>/dev/null || setup_venv
    cd "$SCRIPT_DIR"
    
    python3 -c "
import sys
sys.path.append('.')
from enhanced_ocr_classes import test_ocr_classes
if test_ocr_classes():
    print('✅ OCR test passed')
else:
    print('❌ OCR test failed')
"
}

# Main command handler
main() {
    case "${1:-interactive}" in
        start)
            start_ocr
            ;;
        stop)
            stop_ocr
            ;;
        restart)
            stop_ocr
            sleep 2
            start_ocr
            ;;
        status)
            status_ocr
            ;;
        logs)
            show_logs
            ;;
        test)
            test_ocr
            ;;
        interactive|i|"")
            interactive_mode
            ;;
        install)
            check_dependencies
            setup_venv
            setup_config
            log "Installation completed"
            ;;
        *)
            echo "Usage: $0 {start|stop|restart|status|logs|test|install|interactive}"
            echo
            echo "Commands:"
            echo "  start        - Start WARP OCR service"
            echo "  stop         - Stop WARP OCR service"
            echo "  restart      - Restart WARP OCR service"
            echo "  status       - Show service status"
            echo "  logs         - Show recent logs"
            echo "  test         - Test OCR functionality"
            echo "  install      - Install dependencies and setup"
            echo "  interactive  - Enter interactive mode (default)"
            exit 1
            ;;
    esac
}

# Trap signals for cleanup
trap 'echo; log "Interrupted"; exit 130' INT TERM

# Create log file
touch "$LOG_FILE"

# Run main function
main "$@"