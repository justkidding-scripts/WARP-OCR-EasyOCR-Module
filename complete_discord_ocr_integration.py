#!/usr/bin/env python3
"""
Complete Discord Screenshare OCR Integration System
Combines all components for real-time OCR feedback with performance optimization

Features:
- Real-time Discord window capture
- OCR with timeout protection
- Multiple overlay types
- Discord bot/webhook integration
- Performance monitoring and optimization
- Automatic resource management
"""

import sys
import os
import time
import threading
import asyncio
import logging
import json
import queue
from datetime import datetime
from typing import Dict, Optional, List, Tuple

# Add paths for our modules
sys.path.append('/home/nike')

# Initialize module availability flags
HAS_ENHANCED_OCR = False
HAS_DISCORD_BOT = False
HAS_OVERLAY_SYSTEM = False
HAS_MAIN_OCR = False

try:
    # Import our custom modules
    from enhanced_ocr_classes import WorkingQuickOCR, WorkingFastScreenOCR
    HAS_ENHANCED_OCR = True
except ImportError as e:
    print(f"Enhanced OCR classes not available: {e}")
    WorkingQuickOCR = None
    WorkingFastScreenOCR = None

try:
    from enhanced_ocr_classes import DiscordOptimizedOCR
except ImportError:
    DiscordOptimizedOCR = None

try:
    from discord_bot_integration import UnifiedDiscordOCRIntegration
    HAS_DISCORD_BOT = True
except ImportError as e:
    print(f"Discord bot integration not available: {e}")
    UnifiedDiscordOCRIntegration = None

try:
    from advanced_overlay_system import OverlayManager, OverlayConfig
    HAS_OVERLAY_SYSTEM = True
except ImportError as e:
    print(f"Advanced overlay system not available: {e}")
    OverlayManager = None
    OverlayConfig = None

try:
    # Import the main OCR system
    from discord_screenshare_ocr import DiscordScreenshareOCR
    HAS_MAIN_OCR = True
except ImportError as e:
    print(f"Main OCR system not available: {e}")
    DiscordScreenshareOCR = None

try:
    # Import Discord launcher
    from discord_launcher import DiscordLauncher
    HAS_DISCORD_LAUNCHER = True
except ImportError as e:
    print(f"Discord launcher not available: {e}")
    DiscordLauncher = None

try:
    import cv2
    import numpy as np
    import pyautogui
    import psutil
    import tkinter as tk
    from tkinter import ttk
    import requests
except ImportError as e:
    print(f"Import error: {e}")
    print("Some modules may not be available. Continuing with basic functionality.")


class PerformanceMonitor:
    """Monitor and optimize system performance"""
    
    def __init__(self):
        self.metrics = {
            'fps': 0,
            'cpu_usage': 0,
            'memory_usage': 0,
            'ocr_success_rate': 0,
            'avg_processing_time': 0,
            'frames_processed': 0,
            'frames_skipped': 0,
            'error_count': 0
        }
        
        self.history = []
        self.max_history = 300  # 5 minutes at 1 sample per second
        self.running = False
        
    def start_monitoring(self):
        """Start performance monitoring thread"""
        self.running = True
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()
        
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.running = False
        
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Get system metrics
                process = psutil.Process()
                self.metrics['cpu_usage'] = process.cpu_percent()
                self.metrics['memory_usage'] = process.memory_info().rss / 1024 / 1024  # MB
                
                # Store history
                self.history.append({
                    'timestamp': time.time(),
                    'metrics': self.metrics.copy()
                })
                
                # Limit history size
                if len(self.history) > self.max_history:
                    self.history.pop(0)
                
                time.sleep(1)
                
            except Exception as e:
                logging.error(f"Performance monitoring error: {e}")
                time.sleep(1)
    
    def update_ocr_metrics(self, processing_time: float, success: bool):
        """Update OCR-specific metrics"""
        self.metrics['frames_processed'] += 1
        
        if success:
            # Update success rate (moving average)
            current_rate = self.metrics['ocr_success_rate']
            self.metrics['ocr_success_rate'] = current_rate * 0.95 + (100 * 0.05)
            
            # Update processing time (moving average)
            current_time = self.metrics['avg_processing_time']
            self.metrics['avg_processing_time'] = current_time * 0.9 + (processing_time * 0.1)
        else:
            self.metrics['frames_skipped'] += 1
            self.metrics['error_count'] += 1
            
            # Update success rate
            current_rate = self.metrics['ocr_success_rate']
            self.metrics['ocr_success_rate'] = current_rate * 0.95
    
    def get_current_metrics(self) -> Dict:
        """Get current performance metrics"""
        return self.metrics.copy()
    
    def get_recommendations(self) -> List[str]:
        """Get performance optimization recommendations"""
        recommendations = []
        
        if self.metrics['cpu_usage'] > 80:
            recommendations.append("High CPU usage - consider reducing OCR frequency")
        
        if self.metrics['memory_usage'] > 500:
            recommendations.append("High memory usage - consider clearing cache or restarting")
        
        if self.metrics['ocr_success_rate'] < 60:
            recommendations.append("Low OCR success rate - check image quality and preprocessing")
        
        if self.metrics['avg_processing_time'] > 3.0:
            recommendations.append("Slow OCR processing - consider using faster OCR engine")
        
        if self.metrics['error_count'] > 10:
            recommendations.append("High error count - check system stability")
        
        return recommendations


class AdaptiveOCRController:
    """Automatically adjust OCR parameters based on performance"""
    
    def __init__(self, performance_monitor: PerformanceMonitor):
        self.performance_monitor = performance_monitor
        self.current_interval = 2.0
        self.min_interval = 0.5
        self.max_interval = 10.0
        self.adjustment_factor = 0.1
        
    def adjust_parameters(self) -> Dict[str, float]:
        """Adjust OCR parameters based on current performance"""
        metrics = self.performance_monitor.get_current_metrics()
        
        adjustments = {}
        
        # Adjust interval based on CPU usage
        if metrics['cpu_usage'] > 80:
            # Increase interval to reduce CPU load
            self.current_interval = min(self.current_interval * (1 + self.adjustment_factor), self.max_interval)
            adjustments['interval_increased'] = self.current_interval
        elif metrics['cpu_usage'] < 40 and self.current_interval > self.min_interval:
            # Decrease interval for better responsiveness
            self.current_interval = max(self.current_interval * (1 - self.adjustment_factor), self.min_interval)
            adjustments['interval_decreased'] = self.current_interval
        
        # Suggest timeout adjustments
        if metrics['avg_processing_time'] > 2.0:
            adjustments['suggested_timeout'] = metrics['avg_processing_time'] + 1.0
        else:
            adjustments['suggested_timeout'] = 3.0
        
        return adjustments


class IntegratedDiscordOCRSystem:
    """Complete integrated Discord OCR system"""
    
    def __init__(self, config_path: str = "/home/nike/.config/discord_ocr_system.json"):
        self.config_path = config_path
        self.config = self.load_config()
        
        # Initialize components
        self.performance_monitor = PerformanceMonitor()
        self.adaptive_controller = AdaptiveOCRController(self.performance_monitor)
        
        # OCR components
        self.main_ocr = None
        self.fast_ocr = None
        self.discord_ocr = None
        
        # Integration components
        self.overlay_manager = None
        self.discord_integration = None
        self.main_system = None
        self.discord_launcher = None
        
        # State
        self.running = False
        self.processing_thread = None
        
        self.initialize_components()
        
    def load_config(self) -> Dict:
        """Load system configuration"""
        default_config = {
            'ocr_engine': 'tesseract',
            'ocr_timeout': 3.0,
            'ocr_interval': 2.0,
            'discord_bot_token': None,
            'discord_webhook_url': None,
            'enable_overlays': True,
            'enable_performance_monitoring': True,
            'enable_adaptive_control': True,
            'max_cpu_usage': 80,
            'max_memory_usage': 1000,  # MB
            'log_level': 'INFO'
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
        except Exception as e:
            logging.error(f"Error loading config: {e}")
        
        return default_config
    
    def save_config(self):
        """Save system configuration"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving config: {e}")
    
    def initialize_components(self):
        """Initialize all system components"""
        try:
            logging.info("Initializing Discord OCR System components...")
            
            # Initialize OCR engines with fallback handling
            if HAS_ENHANCED_OCR and WorkingQuickOCR:
                self.main_ocr = WorkingQuickOCR(
                    timeout=self.config['ocr_timeout'],
                    engine=self.config['ocr_engine']
                )
                logging.info("Main OCR engine initialized")
            else:
                self.main_ocr = self._create_basic_tesseract_ocr()
                logging.info("Using basic Tesseract OCR fallback")
            
            if HAS_ENHANCED_OCR and WorkingFastScreenOCR:
                self.fast_ocr = WorkingFastScreenOCR(
                    timeout=self.config['ocr_timeout'] * 0.8,
                    engine=self.config['ocr_engine']
                )
                logging.info("Fast OCR engine initialized")
            else:
                self.fast_ocr = self.main_ocr
                logging.info("Using main OCR as fast OCR fallback")
            
            if DiscordOptimizedOCR:
                try:
                    self.discord_ocr = DiscordOptimizedOCR(
                        timeout=self.config['ocr_timeout'] * 0.6
                    )
                    logging.info("Discord optimized OCR initialized")
                except Exception as e:
                    logging.warning(f"Could not initialize Discord OCR: {e}")
                    self.discord_ocr = self.main_ocr
            else:
                self.discord_ocr = self.main_ocr
                logging.info("Using main OCR as Discord OCR fallback")
            
            # Initialize overlay system
            if self.config['enable_overlays'] and HAS_OVERLAY_SYSTEM:
                try:
                    overlay_config = OverlayConfig() if OverlayConfig else None
                    self.overlay_manager = OverlayManager() if OverlayManager else None
                    if self.overlay_manager:
                        logging.info("Overlay system initialized")
                    else:
                        logging.warning("Overlay manager not available")
                except Exception as e:
                    logging.warning(f"Could not initialize overlays: {e}")
                    self.overlay_manager = None
            else:
                logging.info("Overlay system disabled or not available")
                self.overlay_manager = None
            
            # Initialize Discord integration
            if HAS_DISCORD_BOT and (self.config['discord_bot_token'] or self.config['discord_webhook_url']):
                try:
                    if UnifiedDiscordOCRIntegration:
                        self.discord_integration = UnifiedDiscordOCRIntegration(
                            bot_token=self.config['discord_bot_token'],
                            webhook_url=self.config['discord_webhook_url'],
                            websocket_port=8765
                        )
                        logging.info("Discord integration initialized")
                    else:
                        logging.warning("Discord integration class not available")
                        self.discord_integration = None
                except Exception as e:
                    logging.warning(f"Could not initialize Discord integration: {e}")
                    self.discord_integration = None
            else:
                logging.info("Discord integration disabled or not available")
                self.discord_integration = None
            
            # Initialize Discord launcher
            if HAS_DISCORD_LAUNCHER and DiscordLauncher:
                try:
                    self.discord_launcher = DiscordLauncher()
                    logging.info("Discord launcher initialized")
                    
                    # Auto-launch Discord if enabled
                    if self.config.get('auto_launch_discord', True):
                        self._launch_discord_if_needed()
                except Exception as e:
                    logging.warning(f"Could not initialize Discord launcher: {e}")
                    self.discord_launcher = None
            else:
                logging.info("Discord launcher not available")
                self.discord_launcher = None
            
            # Initialize main OCR system
            if HAS_MAIN_OCR and DiscordScreenshareOCR:
                try:
                    self.main_system = DiscordScreenshareOCR()
                    self.main_system.ocr_interval = self.config['ocr_interval']
                    logging.info("Main OCR system initialized")
                except Exception as e:
                    logging.warning(f"Could not initialize main OCR system: {e}")
                    self.main_system = self._create_minimal_ocr_system()
            else:
                logging.warning("Main OCR system not available, creating minimal substitute")
                self.main_system = self._create_minimal_ocr_system()
            
            # Start performance monitoring
            if self.config['enable_performance_monitoring']:
                self.performance_monitor.start_monitoring()
                logging.info("Performance monitoring started")
            
            logging.info("Component initialization completed")
            
        except Exception as e:
            logging.error(f"Error initializing components: {e}")
            raise
    
    def _create_basic_tesseract_ocr(self):
        """Create basic Tesseract OCR fallback"""
        class BasicTesseractOCR:
            def __init__(self, timeout=5.0):
                self.timeout = timeout
                pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
                self.tesseract_config = '--oem 3 --psm 6'
                
            def ocr_with_timeout(self, image, timeout=None):
                try:
                    if timeout is None:
                        timeout = self.timeout
                    # Basic preprocessing
                    if len(image.shape) == 3:
                        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    else:
                        gray = image
                    # Simple OCR
                    text = pytesseract.image_to_string(gray, config=self.tesseract_config)
                    return text.strip()
                except Exception as e:
                    logging.error(f"Basic OCR error: {e}")
                    return ""
            
            def fast_ocr(self, image):
                return self.ocr_with_timeout(image)
                
        return BasicTesseractOCR(self.config['ocr_timeout'])
    
    def _create_minimal_ocr_system(self):
        """Create minimal OCR system substitute"""
        class MinimalOCRSystem:
            def __init__(self):
                self.ocr_interval = 2.0
                self.running = False
                
            def capture_discord_screen(self):
                try:
                    # Basic screenshot capture
                    screenshot = pyautogui.screenshot()
                    return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                except Exception as e:
                    logging.error(f"Screenshot error: {e}")
                    return None
                    
            def stop_processing(self):
                self.running = False
                
        return MinimalOCRSystem()
    
    def _launch_discord_if_needed(self):
        """Launch Discord if not already running"""
        if not self.discord_launcher:
            logging.warning("Discord launcher not available")
            return False
        
        try:
            status = self.discord_launcher.get_discord_status()
            
            if not status['running']:
                logging.info("🚀 Launching Discord for OCR monitoring...")
                success = self.discord_launcher.launch_discord()
                
                if success:
                    # Wait for Discord window if configured
                    if self.config.get('wait_for_discord_window', True):
                        window_ready = self.discord_launcher.wait_for_discord_window(
                            timeout=self.config.get('discord_launch_timeout', 30)
                        )
                        if window_ready:
                            logging.info("✅ Discord is ready for OCR monitoring")
                        else:
                            logging.warning("⚠️  Discord window not detected, but continuing")
                    else:
                        logging.info("✅ Discord launched successfully")
                    return True
                else:
                    logging.error("❌ Failed to launch Discord")
                    return False
            else:
                logging.info("✅ Discord is already running")
                return True
                
        except Exception as e:
            logging.error(f"Error launching Discord: {e}")
            return False
    
    def start_system(self):
        """Start the complete OCR system"""
        if self.running:
            logging.warning("System is already running")
            return
        
        try:
            logging.info("Starting integrated Discord OCR system...")
            
            self.running = True
            
            # Start main processing loop
            self.processing_thread = threading.Thread(target=self._main_processing_loop, daemon=True)
            self.processing_thread.start()
            
            # Start Discord integration if available
            if self.discord_integration:
                discord_thread = threading.Thread(
                    target=self._start_discord_integration, 
                    daemon=True
                )
                discord_thread.start()
            
            logging.info("Discord OCR system started successfully")
            
        except Exception as e:
            logging.error(f"Error starting system: {e}")
            self.running = False
            raise
    
    def stop_system(self):
        """Stop the complete OCR system"""
        if not self.running:
            return
        
        logging.info("Stopping Discord OCR system...")
        
        self.running = False
        
        # Stop performance monitoring
        self.performance_monitor.stop_monitoring()
        
        # Cleanup components
        if self.overlay_manager:
            self.overlay_manager.cleanup()
        
        if self.main_system:
            self.main_system.stop_processing()
        
        # Wait for processing thread to finish
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5)
        
        logging.info("Discord OCR system stopped")
    
    def _main_processing_loop(self):
        """Main processing loop"""
        last_capture_time = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # Check if it's time for next capture
                if current_time - last_capture_time < self.config['ocr_interval']:
                    time.sleep(0.1)
                    continue
                
                start_time = current_time
                last_capture_time = current_time
                
                # Capture Discord screen
                screen_image = self.main_system.capture_discord_screen()
                
                if screen_image is not None:
                    # Choose OCR engine based on system load
                    metrics = self.performance_monitor.get_current_metrics()
                    
                    if metrics['cpu_usage'] > 70:
                        # Use fast OCR when CPU is loaded
                        ocr_text = self.fast_ocr.fast_ocr(screen_image)
                        ocr_engine_used = "fast"
                    elif metrics['avg_processing_time'] < 1.0:
                        # Use main OCR when performance is good
                        ocr_text = self.main_ocr.ocr_with_timeout(screen_image)
                        ocr_engine_used = "main"
                    else:
                        # Use Discord-optimized OCR as fallback
                        ocr_text = self.discord_ocr.extract_discord_text(screen_image)
                        ocr_engine_used = "discord"
                    
                    processing_time = time.time() - start_time
                    success = bool(ocr_text and ocr_text.strip())
                    
                    # Update performance metrics
                    self.performance_monitor.update_ocr_metrics(processing_time, success)
                    
                    if success:
                        # Prepare metadata
                        metadata = {
                            'processing_time': processing_time,
                            'engine_used': ocr_engine_used,
                            'word_count': len(ocr_text.split()),
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        # Update overlays
                        if self.overlay_manager:
                            self.overlay_manager.update_ocr_result(ocr_text, metadata)
                        
                        # Send to Discord
                        if self.discord_integration:
                            asyncio.create_task(
                                self.discord_integration.send_ocr_result(ocr_text, metadata)
                            )
                        
                        logging.info(f"OCR result: {len(ocr_text)} chars in {processing_time:.2f}s using {ocr_engine_used}")
                
                # Apply adaptive control
                if self.config['enable_adaptive_control']:
                    adjustments = self.adaptive_controller.adjust_parameters()
                    if adjustments:
                        self.config['ocr_interval'] = self.adaptive_controller.current_interval
                
                # Check resource limits
                metrics = self.performance_monitor.get_current_metrics()
                if metrics['cpu_usage'] > self.config['max_cpu_usage']:
                    logging.warning(f"High CPU usage: {metrics['cpu_usage']:.1f}%")
                    time.sleep(1)  # Brief pause to reduce load
                
                if metrics['memory_usage'] > self.config['max_memory_usage']:
                    logging.warning(f"High memory usage: {metrics['memory_usage']:.1f}MB")
                
            except Exception as e:
                logging.error(f"Error in main processing loop: {e}")
                self.performance_monitor.update_ocr_metrics(0, False)
                time.sleep(1)
    
    def _start_discord_integration(self):
        """Start Discord integration in separate thread"""
        try:
            if self.discord_integration:
                self.discord_integration.start_all_services()
        except Exception as e:
            logging.error(f"Discord integration error: {e}")
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        metrics = self.performance_monitor.get_current_metrics()
        recommendations = self.performance_monitor.get_recommendations()
        
        # Get Discord status if launcher is available
        discord_status = {}
        if self.discord_launcher:
            discord_status = self.discord_launcher.get_discord_status()
        
        status = {
            'running': self.running,
            'components': {
                'ocr_engines': bool(self.main_ocr and self.fast_ocr and self.discord_ocr),
                'overlays': bool(self.overlay_manager),
                'discord_integration': bool(self.discord_integration),
                'discord_launcher': bool(self.discord_launcher),
                'performance_monitoring': self.config['enable_performance_monitoring']
            },
            'discord': discord_status,
            'performance': metrics,
            'recommendations': recommendations,
            'config': self.config.copy()
        }
        
        return status
    
    def create_control_interface(self):
        """Create GUI control interface"""
        root = tk.Tk()
        root.title("Discord OCR System Control")
        root.geometry("800x600")
        
        # Create notebook for tabs
        notebook = ttk.Notebook(root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Control tab
        control_frame = ttk.Frame(notebook)
        notebook.add(control_frame, text="Control")
        
        # Status display
        status_frame = ttk.LabelFrame(control_frame, text="System Status", padding=10)
        status_frame.pack(fill=tk.X, pady=5)
        
        self.status_text = tk.Text(status_frame, height=8, state=tk.DISABLED)
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        start_btn = ttk.Button(button_frame, text="Start System", command=self.start_system)
        start_btn.pack(side=tk.LEFT, padx=5)
        
        stop_btn = ttk.Button(button_frame, text="Stop System", command=self.stop_system)
        stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Performance tab
        perf_frame = ttk.Frame(notebook)
        notebook.add(perf_frame, text="Performance")
        
        self.perf_text = tk.Text(perf_frame, height=20, state=tk.DISABLED)
        self.perf_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Settings tab
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="Settings")
        
        # Add settings controls here
        ttk.Label(settings_frame, text="OCR Interval (seconds):").pack(anchor=tk.W, padx=10, pady=5)
        interval_var = tk.StringVar(value=str(self.config['ocr_interval']))
        interval_entry = ttk.Entry(settings_frame, textvariable=interval_var)
        interval_entry.pack(fill=tk.X, padx=10, pady=2)
        
        def save_settings():
            try:
                self.config['ocr_interval'] = float(interval_var.get())
                self.save_config()
                logging.info("Settings saved")
            except Exception as e:
                logging.error(f"Error saving settings: {e}")
        
        save_btn = ttk.Button(settings_frame, text="Save Settings", command=save_settings)
        save_btn.pack(pady=10)
        
        # Update status periodically
        def update_display():
            try:
                status = self.get_system_status()
                
                # Update status text
                self.status_text.config(state=tk.NORMAL)
                self.status_text.delete(1.0, tk.END)
                
                status_info = f"""System Running: {status['running']}

Components:
- OCR Engines: {status['components']['ocr_engines']}
- Overlays: {status['components']['overlays']}
- Discord Integration: {status['components']['discord_integration']}
- Performance Monitoring: {status['components']['performance_monitoring']}

Performance:
- CPU Usage: {status['performance']['cpu_usage']:.1f}%
- Memory Usage: {status['performance']['memory_usage']:.1f}MB
- OCR Success Rate: {status['performance']['ocr_success_rate']:.1f}%
- Avg Processing Time: {status['performance']['avg_processing_time']:.2f}s
- Frames Processed: {status['performance']['frames_processed']}
- Frames Skipped: {status['performance']['frames_skipped']}

Recommendations:
{chr(10).join(status['recommendations']) if status['recommendations'] else 'None'}
"""
                
                self.status_text.insert(1.0, status_info)
                self.status_text.config(state=tk.DISABLED)
                
                # Update performance text
                self.perf_text.config(state=tk.NORMAL)
                self.perf_text.delete(1.0, tk.END)
                self.perf_text.insert(1.0, json.dumps(status, indent=2))
                self.perf_text.config(state=tk.DISABLED)
                
            except Exception as e:
                logging.error(f"Error updating display: {e}")
            
            root.after(1000, update_display)
        
        update_display()
        return root


def main():
    """Main application entry point"""
    print("Discord Screenshare OCR Integration System")
    print("==========================================")
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/home/nike/discord_ocr_system.log'),
            logging.StreamHandler()
        ]
    )
    
    try:
        # Create integrated system
        system = IntegratedDiscordOCRSystem()
        
        # Create control interface
        control_interface = system.create_control_interface()
        
        # Run the interface
        try:
            control_interface.mainloop()
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            system.stop_system()
    
    except Exception as e:
        logging.error(f"System error: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()