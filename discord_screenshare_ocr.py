#!/usr/bin/env python3
"""
Discord Screenshare OCR Integration System
Real-time OCR processing of Discord screenshare with feedback overlay

Features:
- Real-time screen capture from Discord window
- OCR processing with timeout handling
- Live overlay with OCR results
- Discord webhook integration
- Translation support
- Performance monitoring
"""

import cv2
import numpy as np
import pyautogui
import pytesseract
import threading
import time
import tkinter as tk
from tkinter import ttk
import requests
import json
import os
from datetime import datetime
import psutil
import subprocess
from PIL import Image, ImageTk
import asyncio
import websockets
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/nike/discord_ocr.log'),
        logging.StreamHandler()
    ]
)

class DiscordScreenshareOCR:
    def __init__(self):
        self.running = False
        self.discord_window = None
        self.ocr_results = []
        self.last_ocr_text = ""
        self.ocr_interval = 2.0  # seconds
        self.overlay_window = None
        self.discord_webhook_url = None
        self.translation_enabled = False
        self.performance_stats = {
            'frames_processed': 0,
            'ocr_calls': 0,
            'avg_processing_time': 0,
            'memory_usage': 0
        }
        
        # Initialize components
        self.setup_tesseract()
        self.create_overlay()
        self.load_config()
        
    def setup_tesseract(self):
        """Configure Tesseract OCR settings"""
        pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
        # Optimized config for screen text
        self.tesseract_config = '--oem 3 --psm 6'
        
    def load_config(self):
        """Load configuration from file"""
        config_path = '/home/nike/.config/discord_ocr_config.json'
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self.discord_webhook_url = config.get('webhook_url')
                    self.ocr_interval = config.get('ocr_interval', 2.0)
                    self.translation_enabled = config.get('translation_enabled', False)
        except Exception as e:
            logging.error(f"Error loading config: {e}")
    
    def save_config(self):
        """Save configuration to file"""
        config_path = '/home/nike/.config/discord_ocr_config.json'
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        try:
            config = {
                'webhook_url': self.discord_webhook_url,
                'ocr_interval': self.ocr_interval,
                'translation_enabled': self.translation_enabled
            }
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving config: {e}")

    def find_discord_window(self):
        """Find Discord window for screen capture"""
        try:
            # Use xdotool to find Discord window
            result = subprocess.run(['xdotool', 'search', '--name', 'Discord'], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                window_id = result.stdout.strip().split('\n')[0]
                # Get window geometry
                geometry = subprocess.run(['xdotool', 'getwindowgeometry', window_id],
                                        capture_output=True, text=True)
                if geometry.returncode == 0:
                    return window_id
        except Exception as e:
            logging.error(f"Error finding Discord window: {e}")
        return None

    def capture_discord_screen(self):
        """Capture screen content from Discord window"""
        try:
            if not self.discord_window:
                self.discord_window = self.find_discord_window()
                if not self.discord_window:
                    logging.warning("Discord window not found")
                    return None
            
            # Get window position and size
            geometry_cmd = ['xdotool', 'getwindowgeometry', '--shell', self.discord_window]
            result = subprocess.run(geometry_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return None
                
            geometry = {}
            for line in result.stdout.strip().split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    geometry[key] = int(value) if value.isdigit() else value
            
            # Capture screenshot of Discord window area
            x, y = geometry.get('X', 0), geometry.get('Y', 0)
            width, height = geometry.get('WIDTH', 800), geometry.get('HEIGHT', 600)
            
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
        except Exception as e:
            logging.error(f"Error capturing Discord screen: {e}")
            return None

    def preprocess_image(self, image):
        """Preprocess image for better OCR accuracy"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive thresholding
            processed = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Denoise
            processed = cv2.medianBlur(processed, 3)
            
            # Scale up for better OCR
            scale_factor = 2
            height, width = processed.shape
            processed = cv2.resize(processed, (width * scale_factor, height * scale_factor))
            
            return processed
        except Exception as e:
            logging.error(f"Error preprocessing image: {e}")
            return image

    def perform_ocr_with_timeout(self, image, timeout=5.0):
        """Perform OCR with timeout handling (WorkingQuickOCR approach)"""
        try:
            start_time = time.time()
            
            # Preprocess image
            processed_image = self.preprocess_image(image)
            
            # OCR with timeout using threading
            result_container = [None]
            error_container = [None]
            
            def ocr_worker():
                try:
                    text = pytesseract.image_to_string(processed_image, config=self.tesseract_config)
                    result_container[0] = text.strip()
                except Exception as e:
                    error_container[0] = str(e)
            
            ocr_thread = threading.Thread(target=ocr_worker, daemon=True)
            ocr_thread.start()
            ocr_thread.join(timeout=timeout)
            
            if ocr_thread.is_alive():
                logging.warning(f"OCR timeout after {timeout}s")
                return ""
            
            if error_container[0]:
                logging.error(f"OCR error: {error_container[0]}")
                return ""
            
            processing_time = time.time() - start_time
            self.performance_stats['avg_processing_time'] = (
                self.performance_stats['avg_processing_time'] * 0.9 + processing_time * 0.1
            )
            
            return result_container[0] if result_container[0] else ""
            
        except Exception as e:
            logging.error(f"OCR processing error: {e}")
            return ""

    def create_overlay(self):
        """Create transparent overlay window for displaying OCR results"""
        self.overlay_window = tk.Toplevel()
        self.overlay_window.withdraw()  # Hide initially
        self.overlay_window.attributes('-topmost', True)
        self.overlay_window.attributes('-alpha', 0.8)
        self.overlay_window.overrideredirect(True)
        self.overlay_window.configure(bg='black')
        
        # Create text widget for OCR results
        self.overlay_text = tk.Text(
            self.overlay_window,
            bg='black',
            fg='lime',
            font=('Courier', 12, 'bold'),
            wrap=tk.WORD,
            height=10,
            width=60
        )
        self.overlay_text.pack(padx=5, pady=5)
        
        # Position overlay (top-right corner)
        self.overlay_window.geometry("500x300+1400+50")

    def update_overlay(self, text):
        """Update overlay window with new OCR text"""
        try:
            if self.overlay_window:
                self.overlay_text.delete(1.0, tk.END)
                self.overlay_text.insert(1.0, f"[{datetime.now().strftime('%H:%M:%S')}] OCR Results:\n\n{text}")
                
                if text.strip() and not self.overlay_window.winfo_viewable():
                    self.overlay_window.deiconify()
                elif not text.strip() and self.overlay_window.winfo_viewable():
                    self.overlay_window.withdraw()
        except Exception as e:
            logging.error(f"Error updating overlay: {e}")

    def send_to_discord(self, text):
        """Send OCR results to Discord via webhook"""
        if not self.discord_webhook_url or not text.strip():
            return
        
        try:
            payload = {
                "content": f"**OCR Results:**\n```\n{text}\n```",
                "username": "OCR Bot"
            }
            
            response = requests.post(self.discord_webhook_url, json=payload, timeout=5)
            if response.status_code == 204:
                logging.info("OCR results sent to Discord")
            else:
                logging.warning(f"Discord webhook response: {response.status_code}")
                
        except Exception as e:
            logging.error(f"Error sending to Discord: {e}")

    def translate_text(self, text):
        """Translate text using LibreTranslate or Google Translate API"""
        if not self.translation_enabled or not text.strip():
            return text
        
        try:
            # Using LibreTranslate (local instance)
            translate_url = "http://localhost:5000/translate"
            payload = {
                "q": text,
                "source": "auto",
                "target": "en",
                "format": "text"
            }
            
            response = requests.post(translate_url, json=payload, timeout=10)
            if response.status_code == 200:
                result = response.json()
                return f"Original: {text}\n\nTranslated: {result.get('translatedText', text)}"
        except:
            pass
        
        return text

    def update_performance_stats(self):
        """Update performance statistics"""
        try:
            process = psutil.Process()
            self.performance_stats['memory_usage'] = process.memory_info().rss / 1024 / 1024  # MB
        except:
            pass

    def ocr_processing_loop(self):
        """Main OCR processing loop"""
        logging.info("Starting OCR processing loop")
        
        while self.running:
            try:
                start_time = time.time()
                
                # Capture Discord screen
                screen_image = self.capture_discord_screen()
                if screen_image is not None:
                    self.performance_stats['frames_processed'] += 1
                    
                    # Perform OCR
                    ocr_text = self.perform_ocr_with_timeout(screen_image, timeout=3.0)
                    
                    if ocr_text and ocr_text != self.last_ocr_text:
                        self.performance_stats['ocr_calls'] += 1
                        self.last_ocr_text = ocr_text
                        
                        # Translate if enabled
                        final_text = self.translate_text(ocr_text)
                        
                        # Update overlay
                        self.update_overlay(final_text)
                        
                        # Send to Discord
                        self.send_to_discord(final_text)
                        
                        # Store results
                        self.ocr_results.append({
                            'timestamp': datetime.now(),
                            'text': final_text,
                            'processing_time': time.time() - start_time
                        })
                        
                        # Keep only last 100 results
                        if len(self.ocr_results) > 100:
                            self.ocr_results = self.ocr_results[-100:]
                
                # Update performance stats
                self.update_performance_stats()
                
                # Sleep until next interval
                elapsed = time.time() - start_time
                sleep_time = max(0, self.ocr_interval - elapsed)
                time.sleep(sleep_time)
                
            except Exception as e:
                logging.error(f"Error in OCR processing loop: {e}")
                time.sleep(1)

    def start_processing(self):
        """Start the OCR processing"""
        if not self.running:
            self.running = True
            self.processing_thread = threading.Thread(target=self.ocr_processing_loop, daemon=True)
            self.processing_thread.start()
            logging.info("Discord screenshare OCR started")

    def stop_processing(self):
        """Stop the OCR processing"""
        self.running = False
        if hasattr(self, 'processing_thread'):
            self.processing_thread.join(timeout=5)
        logging.info("Discord screenshare OCR stopped")

    def create_control_panel(self):
        """Create GUI control panel"""
        control_window = tk.Tk()
        control_window.title("Discord Screenshare OCR Control")
        control_window.geometry("600x400")
        
        # Status frame
        status_frame = ttk.LabelFrame(control_window, text="Status", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Stopped")
        self.status_label.pack()
        
        # Control buttons
        button_frame = ttk.Frame(control_window)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        start_btn = ttk.Button(button_frame, text="Start OCR", command=self.start_processing)
        start_btn.pack(side=tk.LEFT, padx=5)
        
        stop_btn = ttk.Button(button_frame, text="Stop OCR", command=self.stop_processing)
        stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Settings frame
        settings_frame = ttk.LabelFrame(control_window, text="Settings", padding=10)
        settings_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(settings_frame, text="OCR Interval (seconds):").pack(anchor=tk.W)
        interval_var = tk.StringVar(value=str(self.ocr_interval))
        interval_entry = ttk.Entry(settings_frame, textvariable=interval_var)
        interval_entry.pack(fill=tk.X, pady=2)
        
        ttk.Label(settings_frame, text="Discord Webhook URL:").pack(anchor=tk.W)
        webhook_var = tk.StringVar(value=self.discord_webhook_url or "")
        webhook_entry = ttk.Entry(settings_frame, textvariable=webhook_var)
        webhook_entry.pack(fill=tk.X, pady=2)
        
        translation_var = tk.BooleanVar(value=self.translation_enabled)
        translation_check = ttk.Checkbutton(settings_frame, text="Enable Translation", 
                                          variable=translation_var)
        translation_check.pack(anchor=tk.W, pady=2)
        
        def save_settings():
            self.ocr_interval = float(interval_var.get())
            self.discord_webhook_url = webhook_var.get()
            self.translation_enabled = translation_var.get()
            self.save_config()
        
        save_btn = ttk.Button(settings_frame, text="Save Settings", command=save_settings)
        save_btn.pack(pady=5)
        
        # Performance stats
        stats_frame = ttk.LabelFrame(control_window, text="Performance", padding=10)
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.stats_text = tk.Text(stats_frame, height=8)
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        
        def update_status():
            if self.running:
                self.status_label.config(text="Running - Processing Discord screenshare")
            else:
                self.status_label.config(text="Stopped")
            
            # Update performance stats
            stats = self.performance_stats
            stats_text = f"""Frames Processed: {stats['frames_processed']}
OCR Calls: {stats['ocr_calls']}
Avg Processing Time: {stats['avg_processing_time']:.2f}s
Memory Usage: {stats['memory_usage']:.1f} MB
Last OCR Result: {len(self.last_ocr_text)} characters
Recent Results: {len(self.ocr_results)} stored"""
            
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, stats_text)
            
            control_window.after(1000, update_status)
        
        update_status()
        return control_window

def main():
    """Main application entry point"""
    print("Discord Screenshare OCR Integration System")
    print("==========================================")
    
    # Create OCR system
    ocr_system = DiscordScreenshareOCR()
    
    # Create and show control panel
    control_panel = ocr_system.create_control_panel()
    
    try:
        control_panel.mainloop()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        ocr_system.stop_processing()

if __name__ == "__main__":
    main()