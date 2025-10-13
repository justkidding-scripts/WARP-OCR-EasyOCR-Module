# WARP OCR Screenshare System

## Discord Screenshare OCR Integration with Real-time Feedback

A comprehensive system for real-time OCR (Optical Character Recognition) of Discord screenshare sessions with multiple feedback mechanisms including overlays, Discord bot integration, and performance monitoring.

---

## Features

### Core OCR Capabilities
- **Real-time Discord window capture** using `xdotool` and `pyautogui`
- **Multiple OCR engines** with timeout protection:
 - WorkingQuickOCR (primary, full-featured)
 - WorkingFastScreenOCR (optimized for speed)
 - DiscordOptimizedOCR (UI-specific preprocessing)
- **Advanced image preprocessing** with denoising, scaling, and thresholding
- **Timeout-protected processing** prevents OCR hangs

### Visual Feedback Systems
- **Floating Overlay** - Transparent window showing current OCR results
- **Docked Live Feed** - Continuous scrolling display of all OCR results
- **Translation Overlay** - Side-by-side original and translated text
- **Hotkey Controls** - `Ctrl+Shift+O` (toggle), `Ctrl+Shift+C` (clear)

### Discord Integration
- **Discord Bot** with commands: `!ocr start`, `!ocr stop`, `!ocr status`, `!ocr clear`
- **Webhook Integration** for direct channel posting
- **WebSocket Server** for real-time client connections
- **Rate limiting and spam protection**
- **Rich embed formatting** with metadata (processing time, confidence, etc.)

### Performance & Monitoring
- **Adaptive OCR Control** - Automatically adjusts intervals based on CPU usage
- **Performance Monitoring** - CPU, memory, success rates, processing times
- **Resource Management** - Prevents system overload
- **Comprehensive Logging** - Detailed logs with configurable levels

---

## Installation

### System Dependencies
```bash
# Install Tesseract OCR engine
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# Install xdotool for window management
sudo apt-get install xdotool

# Install Python 3 and tkinter (if not already installed)
sudo apt-get install python3 python3-venv python3-tk
```

### Quick Setup
```bash
# Clone/navigate to the project directory
cd "/home/nike/Modular Deepdive Screenshare"

# Run the interactive installer
./launch_warp_ocr.sh install

# Or start directly (auto-installs dependencies)
./launch_warp_ocr.sh start
```

### Manual Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create configuration files
mkdir -p ~/.config
# Edit ~/.config/discord_ocr_system.json with your settings
```

---

## ️ Configuration

### Main System Config (`~/.config/discord_ocr_system.json`)
```json
{
 "ocr_engine": "tesseract",
 "ocr_timeout": 3.0,
 "ocr_interval": 2.0,
 "discord_bot_token": "YOUR_BOT_TOKEN_HERE",
 "discord_webhook_url": "YOUR_WEBHOOK_URL_HERE",
 "enable_overlays": true,
 "enable_performance_monitoring": true,
 "enable_adaptive_control": true,
 "max_cpu_usage": 80,
 "max_memory_usage": 1000,
 "log_level": "INFO"
}
```

### Discord OCR Config (`~/.config/discord_ocr_config.json`)
```json
{
 "webhook_url": "https/discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN",
 "ocr_interval": 2.0,
 "translation_enabled": false,
 "ocr_timeout": 3.0,
 "enable_overlays": true,
 "enable_performance_monitoring": true,
 "log_level": "INFO"
}
```

### Overlay Config (`~/.config/overlay_config.json`)
```json
{
 "position": [100, 100],
 "size": [400, 300],
 "opacity": 0.8,
 "font_size": 12,
 "font_family": "Courier",
 "background_color": "#000000",
 "text_color": "#00ff00",
 "auto_hide": true,
 "auto_hide_delay": 5.0,
 "show_metadata": true,
 "show_timestamps": true
}
```

---

## Usage

### Command Line Interface
```bash
# Interactive mode (default)
./launch_warp_ocr.sh

# Direct commands
./launch_warp_ocr.sh start # Start the OCR system
./launch_warp_ocr.sh stop # Stop the OCR system
./launch_warp_ocr.sh status # Show current status
./launch_warp_ocr.sh logs # Show recent logs
./launch_warp_ocr.sh test # Test OCR functionality
./launch_warp_ocr.sh restart # Restart the service
```

### Interactive Control Panel
```
WARP OCR > start # Start OCR monitoring
WARP OCR > status # Check system status
WARP OCR > logs # View recent logs
WARP OCR > config # Show config file locations
WARP OCR > test # Test OCR engines
WARP OCR > stop # Stop OCR monitoring
WARP OCR > quit # Exit interactive mode
```

### Discord Bot Commands
```
!ocr start # Start OCR monitoring in this channel
!ocr stop # Stop OCR monitoring
!ocr status # Show monitoring status and statistics
!ocr clear # Clear OCR message history
```

### Hotkey Controls
- **Ctrl+Shift+O** - Toggle overlay visibility
- **Ctrl+Shift+C** - Clear overlay text
- **Ctrl+Shift+Plus** - Increase overlay size
- **Ctrl+Shift+Minus** - Decrease overlay size

---

## ️ Architecture

### Main Components

#### 1. Core OCR Engine (`enhanced_ocr_classes.py`)
```python
WorkingQuickOCR # Primary OCR with timeout protection
WorkingFastScreenOCR # Speed-optimized with caching
DiscordOptimizedOCR # Discord UI specific preprocessing
```

#### 2. Discord Integration (`discord_bot_integration.py`)
```python
DiscordOCRBot # Bot commands and management
WebSocketOCRIntegration # Real-time client connections
UnifiedDiscordOCRIntegration # Combined bot/webhook/websocket
```

#### 3. Overlay System (`advanced_overlay_system.py`)
```python
FloatingOverlay # Main OCR results display
DockedOverlay # Continuous live feed
TranslationOverlay # Translation results
OverlayManager # Centralized overlay control
```

#### 4. Screen Capture (`discord_screenshare_ocr.py`)
```python
DiscordScreenshareOCR # Window detection and capture
```

#### 5. Integration Layer (`complete_discord_ocr_integration.py`)
```python
PerformanceMonitor # System resource monitoring
AdaptiveOCRController # Dynamic parameter adjustment
IntegratedDiscordOCRSystem # Main orchestrator
```

### Data Flow
```
Discord Window → Screen Capture → OCR Processing → Results Distribution
 ↓
 ┌─────────────┼─────────────┐
 ▼ ▼ ▼
 Overlays Discord Bot Performance
 Display Integration Monitor
```

---

## Troubleshooting

### Common Issues

#### OCR Not Working
```bash
# Check Tesseract installation
tesseract --version

# Test OCR engines
./launch_warp_ocr.sh test

# Check system dependencies
./launch_warp_ocr.sh install
```

#### Discord Window Not Found
```bash
# Check if Discord is running
ps aux | grep -i discord

# Verify xdotool can find Discord
xdotool search --name "Discord"

# Check DISPLAY environment variable
echo $DISPLAY
```

#### GUI/Overlay Issues
```bash
# Check X11 session
echo $XDG_SESSION_TYPE

# Install tkinter if missing
sudo apt-get install python3-tk

# Check DISPLAY permissions
xhost +local:
```

#### Performance Issues
```bash
# Check resource usage
./launch_warp_ocr.sh status

# View performance logs
./launch_warp_ocr.sh logs

# Lower CPU usage by increasing OCR interval
# Edit ~/.config/discord_ocr_system.json
# Set "ocr_interval": 5.0
```

### Log Files
- **Main System**: `warp_ocr.log` (in project directory)
- **System Level**: `/home/nike/discord_ocr_system.log`
- **Discord OCR**: `/home/nike/discord_ocr.log`

---

## Performance Tuning

### OCR Engine Selection
```python
# CPU usage > 70% → FastScreenOCR (optimized for speed)
# CPU usage < 40% → WorkingQuickOCR (full accuracy)
# Default fallback → DiscordOptimizedOCR (UI specific)
```

### Adaptive Parameters
- **OCR Interval**: Automatically adjusts (0.5s - 10s) based on CPU load
- **Timeout Values**: Dynamic based on average processing time
- **Cache Management**: Duplicate detection and result caching

### Resource Limits
- **Max CPU**: 80% (configurable)
- **Max Memory**: 1000MB (configurable)
- **Auto-pause**: When limits exceeded

---

## Discord Bot Setup

### 1. Create Discord Application
1. Go to [Discord Developer Portal](https/discord.com/developers/applications)
2. Create new application → Bot section
3. Copy bot token
4. Add to config: `"discord_bot_token": "YOUR_TOKEN"`

### 2. Bot Permissions
Required permissions:
- Send Messages
- Use External Emojis
- Read Message History
- Add Reactions

### 3. Webhook Setup (Alternative)
1. Discord Server → Edit Channel → Integrations → Webhooks
2. Create webhook → Copy URL
3. Add to config: `"discord_webhook_url": "YOUR_WEBHOOK_URL"`

---

## ️ Development

### Project Structure
```
Modular Deepdive Screenshare/
├── launch_warp_ocr.sh # Main launcher script
├── requirements.txt # Python dependencies
├── README.md # This file
├── discord_screenshare_ocr.py # Main OCR system
├── enhanced_ocr_classes.py # OCR engines with timeout
├── discord_bot_integration.py # Discord bot/webhook/websocket
├── advanced_overlay_system.py # Visual feedback overlays
├── complete_discord_ocr_integration.py # Full system integration
├── venv/ # Python virtual environment
├── warp_ocr.log # System log file
└── warp_ocr.pid # Process ID file
```

### Adding New OCR Engines
```python
class CustomOCR(WorkingQuickOCR):
 def _setup_ocr_engine(self):
 if self.engine == 'custom':
 # Initialize your OCR engine
 pass

 def ocr_worker(self):
 # Implement OCR processing
 pass
```

### Extending Overlay System
```python
class CustomOverlay:
 def __init__(self, config: OverlayConfig):
 self.create_custom_window()

 def update_display(self, text: str, metadata: dict):
 # Custom display logic
 pass
```

---

## System Requirements

### Minimum Requirements
- **OS**: Linux (Debian/Ubuntu recommended)
- **Python**: 3.7+
- **Memory**: 500MB RAM
- **Storage**: 200MB free space
- **Display**: X11 session required

### Recommended Requirements
- **Python**: 3.9+
- **Memory**: 1GB+ RAM
- **CPU**: Multi-core for better performance
- **Storage**: 1GB free space (for logs/cache)

### Tested Environments
- **Debian GNU/Linux** (Primary)
- **Ubuntu 20.04+**
- **Kali Linux**
- ️ **Other Linux distros** (may require dependency adjustments)

---

## Contributing

### Bug Reports
Please include:
- Operating system and version
- Python version (`python3 --version`)
- Full error logs (`./launch_warp_ocr.sh logs`)
- Steps to reproduce

### Feature Requests
- Use case description
- Expected behavior
- Technical requirements

---

## License

This project is part of the WARP OCR enhancement system for educational and research purposes.

---

## 🆘 Support

### Quick Help
```bash
./launch_warp_ocr.sh help
```

### Interactive Troubleshooting
```bash
./launch_warp_ocr.sh
# Then type 'help' for available commands
```

### Log Analysis
```bash
# Recent logs
tail -f warp_ocr.log

# Error analysis
grep -i error warp_ocr.log

# Performance metrics
grep -i "cpu\|memory\|processing" warp_ocr.log
```

---

**Made with ️ for the WARP OCR community**

*Last updated: $(date '+%Y-%m-%d %H:%M:%S')*