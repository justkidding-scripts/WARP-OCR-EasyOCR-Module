#!/usr/bin/env python3
"""
Advanced Overlay System for Discord Screenshare OCR
Provides multiple overlay modes for real-time visual feedback

Features:
- Multiple overlay types (floating, docked, fullscreen)
- Customizable themes and styles
- Translation overlay support
- Performance monitoring display
- Hotkey controls
- Auto-positioning and collision avoidance
"""

import tkinter as tk
from tkinter import ttk, font as tkFont
import threading
import time
import json
import os
from datetime import datetime
import numpy as np
import cv2
from PIL import Image, ImageTk, ImageFont, ImageDraw
import keyboard
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import queue

# Configure logging
logging.basicConfig(level=logging.INFO)

@dataclass
class OverlayConfig:
    """Configuration for overlay appearance and behavior"""
    position: Tuple[int, int] = (100, 100)
    size: Tuple[int, int] = (400, 300)
    opacity: float = 0.8
    font_size: int = 12
    font_family: str = "Courier"
    background_color: str = "#000000"
    text_color: str = "#00ff00"
    border_width: int = 2
    border_color: str = "#00ff00"
    auto_hide: bool = True
    auto_hide_delay: float = 5.0
    always_on_top: bool = True
    resizable: bool = True
    show_metadata: bool = True
    show_timestamps: bool = True
    max_text_length: int = 1000

class FloatingOverlay:
    """Floating overlay window for OCR results"""
    
    def __init__(self, config: OverlayConfig):
        self.config = config
        self.window = None
        self.text_widget = None
        self.is_visible = False
        self.last_update = time.time()
        self.auto_hide_timer = None
        self.current_text = ""
        
        self.create_window()
        self.setup_hotkeys()
        
    def create_window(self):
        """Create the floating overlay window"""
        try:
            # Create main window
            self.window = tk.Toplevel()
            self.window.title("OCR Overlay")
            self.window.geometry(f"{self.config.size[0]}x{self.config.size[1]}+{self.config.position[0]}+{self.config.position[1]}")
            
            # Window properties
            self.window.attributes('-alpha', self.config.opacity)
            self.window.attributes('-topmost', self.config.always_on_top)
            self.window.configure(bg=self.config.background_color)
            
            # Make window borderless or with custom border
            if self.config.border_width == 0:
                self.window.overrideredirect(True)
            else:
                self.window.configure(highlightbackground=self.config.border_color,
                                    highlightthickness=self.config.border_width)
            
            # Configure for resizing if enabled
            if self.config.resizable:
                self.window.resizable(True, True)
            else:
                self.window.resizable(False, False)
            
            # Create text widget
            self.create_text_widget()
            
            # Hide initially
            self.window.withdraw()
            
            logging.info("Floating overlay window created")
            
        except Exception as e:
            logging.error(f"Error creating overlay window: {e}")
    
    def create_text_widget(self):
        """Create the text display widget"""
        try:
            # Create font
            overlay_font = tkFont.Font(
                family=self.config.font_family,
                size=self.config.font_size,
                weight="bold"
            )
            
            # Create frame for better layout
            main_frame = tk.Frame(self.window, bg=self.config.background_color)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
            
            # Create text widget with scrollbar
            text_frame = tk.Frame(main_frame, bg=self.config.background_color)
            text_frame.pack(fill=tk.BOTH, expand=True)
            
            self.text_widget = tk.Text(
                text_frame,
                bg=self.config.background_color,
                fg=self.config.text_color,
                font=overlay_font,
                wrap=tk.WORD,
                borderwidth=0,
                highlightthickness=0,
                insertbackground=self.config.text_color,
                selectbackground="#444444",
                selectforeground=self.config.text_color
            )
            
            # Add scrollbar
            scrollbar = tk.Scrollbar(text_frame, command=self.text_widget.yview)
            self.text_widget.configure(yscrollcommand=scrollbar.set)
            
            # Pack widgets
            self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Create status bar if metadata is enabled
            if self.config.show_metadata:
                self.status_bar = tk.Label(
                    main_frame,
                    bg=self.config.background_color,
                    fg=self.config.text_color,
                    font=tkFont.Font(family=self.config.font_family, size=max(8, self.config.font_size-2)),
                    anchor="w"
                )
                self.status_bar.pack(fill=tk.X, pady=(2, 0))
            
        except Exception as e:
            logging.error(f"Error creating text widget: {e}")
    
    def setup_hotkeys(self):
        """Setup global hotkeys for overlay control"""
        try:
            # Check if we have keyboard access (requires root on Linux)
            import os
            import getpass
            
            # Skip hotkeys if not root (to avoid permission errors)
            if os.name == 'posix' and getpass.getuser() != 'root':
                logging.info("Skipping hotkey registration (requires root privileges on Linux)")
                logging.info("Overlay can still be controlled via GUI interface")
                return
            
            # Register hotkeys if we have permission
            keyboard.add_hotkey('ctrl+shift+o', self.toggle_visibility)
            keyboard.add_hotkey('ctrl+shift+c', self.clear_text)
            keyboard.add_hotkey('ctrl+shift+plus', lambda: self.resize_overlay(1.1))
            keyboard.add_hotkey('ctrl+shift+minus', lambda: self.resize_overlay(0.9))
            
            logging.info("Overlay hotkeys registered successfully")
            
        except ImportError:
            logging.info("Keyboard module not available, hotkeys disabled")
        except Exception as e:
            logging.warning(f"Could not register hotkeys: {e}")
            logging.info("Hotkeys disabled, overlay can be controlled via GUI interface")
    
    def update_text(self, text: str, metadata: Optional[Dict] = None):
        """Update overlay with new OCR text"""
        if not self.window or not self.text_widget:
            return
        
        try:
            self.current_text = text
            self.last_update = time.time()
            
            # Format text with timestamp if enabled
            display_text = ""
            if self.config.show_timestamps:
                timestamp = datetime.now().strftime("[%H:%M:%S] ")
                display_text += timestamp
            
            # Truncate text if too long
            if len(text) > self.config.max_text_length:
                text = text[:self.config.max_text_length] + "..."
            
            display_text += text
            
            # Update text widget
            self.text_widget.delete(1.0, tk.END)
            self.text_widget.insert(1.0, display_text)
            
            # Update status bar with metadata
            if self.config.show_metadata and hasattr(self, 'status_bar') and metadata:
                status_text = []
                
                if metadata.get('processing_time'):
                    status_text.append(f"Time: {metadata['processing_time']:.2f}s")
                
                if metadata.get('confidence'):
                    status_text.append(f"Confidence: {metadata['confidence']:.1f}%")
                
                if metadata.get('word_count'):
                    status_text.append(f"Words: {metadata['word_count']}")
                
                self.status_bar.config(text=" | ".join(status_text))
            
            # Show overlay if text is not empty
            if text.strip():
                self.show()
                
                # Set auto-hide timer
                if self.config.auto_hide:
                    if self.auto_hide_timer:
                        self.window.after_cancel(self.auto_hide_timer)
                    self.auto_hide_timer = self.window.after(
                        int(self.config.auto_hide_delay * 1000),
                        self.hide
                    )
            else:
                self.hide()
                
        except Exception as e:
            logging.error(f"Error updating overlay text: {e}")
    
    def show(self):
        """Show the overlay window"""
        if self.window and not self.is_visible:
            self.window.deiconify()
            self.window.lift()
            self.is_visible = True
    
    def hide(self):
        """Hide the overlay window"""
        if self.window and self.is_visible:
            self.window.withdraw()
            self.is_visible = False
    
    def toggle_visibility(self):
        """Toggle overlay visibility"""
        if self.is_visible:
            self.hide()
        else:
            self.show()
    
    def clear_text(self):
        """Clear overlay text"""
        if self.text_widget:
            self.text_widget.delete(1.0, tk.END)
        self.current_text = ""
        self.hide()
    
    def resize_overlay(self, scale_factor: float):
        """Resize the overlay window"""
        if not self.window:
            return
        
        try:
            current_geometry = self.window.geometry()
            width, height, x, y = map(int, current_geometry.replace('x', '+').replace('+', ' ').split())
            
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            
            self.window.geometry(f"{new_width}x{new_height}+{x}+{y}")
            
        except Exception as e:
            logging.error(f"Error resizing overlay: {e}")
    
    def destroy(self):
        """Cleanup overlay resources"""
        try:
            if self.auto_hide_timer:
                self.window.after_cancel(self.auto_hide_timer)
            
            if self.window:
                self.window.destroy()
                
        except Exception as e:
            logging.error(f"Error destroying overlay: {e}")


class DockedOverlay:
    """Docked overlay for continuous display"""
    
    def __init__(self, config: OverlayConfig, dock_position="right"):
        self.config = config
        self.dock_position = dock_position
        self.window = None
        self.text_queue = queue.Queue(maxsize=100)
        self.is_visible = True
        
        self.create_docked_window()
        self.start_update_thread()
    
    def create_docked_window(self):
        """Create docked overlay window"""
        try:
            self.window = tk.Toplevel()
            self.window.title("OCR Live Feed")
            
            # Position window based on dock position
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            
            if self.dock_position == "right":
                x = screen_width - self.config.size[0] - 10
                y = 50
            elif self.dock_position == "left":
                x = 10
                y = 50
            elif self.dock_position == "top":
                x = (screen_width - self.config.size[0]) // 2
                y = 10
            else:  # bottom
                x = (screen_width - self.config.size[0]) // 2
                y = screen_height - self.config.size[1] - 50
            
            self.window.geometry(f"{self.config.size[0]}x{self.config.size[1]}+{x}+{y}")
            self.window.attributes('-alpha', self.config.opacity)
            self.window.attributes('-topmost', self.config.always_on_top)
            self.window.configure(bg=self.config.background_color)
            
            # Create scrolled text widget
            self.create_scrolled_display()
            
        except Exception as e:
            logging.error(f"Error creating docked overlay: {e}")
    
    def create_scrolled_display(self):
        """Create scrollable text display"""
        try:
            main_frame = tk.Frame(self.window, bg=self.config.background_color)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
            
            # Title bar
            title_frame = tk.Frame(main_frame, bg=self.config.background_color)
            title_frame.pack(fill=tk.X, pady=(0, 2))
            
            title_label = tk.Label(
                title_frame,
                text="Live OCR Feed",
                bg=self.config.background_color,
                fg=self.config.text_color,
                font=tkFont.Font(family=self.config.font_family, size=self.config.font_size, weight="bold")
            )
            title_label.pack(side=tk.LEFT)
            
            # Clear button
            clear_btn = tk.Button(
                title_frame,
                text="Clear",
                command=self.clear_all,
                bg="#333333",
                fg=self.config.text_color,
                font=tkFont.Font(size=8),
                relief="flat"
            )
            clear_btn.pack(side=tk.RIGHT)
            
            # Text display area
            text_frame = tk.Frame(main_frame, bg=self.config.background_color)
            text_frame.pack(fill=tk.BOTH, expand=True)
            
            self.text_display = tk.Text(
                text_frame,
                bg=self.config.background_color,
                fg=self.config.text_color,
                font=tkFont.Font(family=self.config.font_family, size=self.config.font_size-1),
                wrap=tk.WORD,
                borderwidth=1,
                relief="sunken",
                state=tk.DISABLED  # Read-only
            )
            
            scrollbar = tk.Scrollbar(text_frame, command=self.text_display.yview)
            self.text_display.configure(yscrollcommand=scrollbar.set)
            
            self.text_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
        except Exception as e:
            logging.error(f"Error creating scrolled display: {e}")
    
    def add_text(self, text: str, metadata: Optional[Dict] = None):
        """Add new text to the docked display"""
        try:
            if not text.strip():
                return
            
            entry = {
                'text': text,
                'metadata': metadata or {},
                'timestamp': datetime.now()
            }
            
            # Add to queue (non-blocking)
            if not self.text_queue.full():
                self.text_queue.put(entry)
            
        except Exception as e:
            logging.error(f"Error adding text to dock: {e}")
    
    def start_update_thread(self):
        """Start thread to update display"""
        def update_worker():
            while True:
                try:
                    # Wait for new text
                    entry = self.text_queue.get(timeout=1.0)
                    
                    if self.text_display:
                        # Format entry
                        timestamp = entry['timestamp'].strftime("[%H:%M:%S] ")
                        display_text = f"{timestamp}{entry['text']}\n"
                        
                        # Add metadata if available
                        metadata = entry['metadata']
                        if metadata and self.config.show_metadata:
                            meta_parts = []
                            if metadata.get('processing_time'):
                                meta_parts.append(f"Time: {metadata['processing_time']:.2f}s")
                            if metadata.get('confidence'):
                                meta_parts.append(f"Conf: {metadata['confidence']:.1f}%")
                            
                            if meta_parts:
                                display_text += f"  ({', '.join(meta_parts)})\n"
                        
                        display_text += "\n"  # Add spacing
                        
                        # Update display (thread-safe)
                        self.window.after(0, self._update_display, display_text)
                
                except queue.Empty:
                    continue
                except Exception as e:
                    logging.error(f"Error in dock update thread: {e}")
                    time.sleep(1)
        
        update_thread = threading.Thread(target=update_worker, daemon=True)
        update_thread.start()
    
    def _update_display(self, text: str):
        """Update display (must be called from main thread)"""
        try:
            if self.text_display:
                self.text_display.config(state=tk.NORMAL)
                self.text_display.insert(tk.END, text)
                
                # Auto-scroll to bottom
                self.text_display.see(tk.END)
                
                # Limit text length (keep last 10000 chars)
                content = self.text_display.get(1.0, tk.END)
                if len(content) > 10000:
                    self.text_display.delete(1.0, f"1.0+{len(content)-10000}c")
                
                self.text_display.config(state=tk.DISABLED)
                
        except Exception as e:
            logging.error(f"Error updating docked display: {e}")
    
    def clear_all(self):
        """Clear all text from display"""
        try:
            if self.text_display:
                self.text_display.config(state=tk.NORMAL)
                self.text_display.delete(1.0, tk.END)
                self.text_display.config(state=tk.DISABLED)
            
            # Clear queue
            while not self.text_queue.empty():
                try:
                    self.text_queue.get_nowait()
                except queue.Empty:
                    break
                    
        except Exception as e:
            logging.error(f"Error clearing docked display: {e}")


class TranslationOverlay:
    """Specialized overlay for translation results"""
    
    def __init__(self, config: OverlayConfig):
        self.config = config
        self.window = None
        self.original_text = ""
        self.translated_text = ""
        
        self.create_translation_window()
    
    def create_translation_window(self):
        """Create translation-specific overlay"""
        try:
            self.window = tk.Toplevel()
            self.window.title("Translation Overlay")
            
            # Position to avoid overlapping with main overlay
            pos_x = self.config.position[0] + 450
            pos_y = self.config.position[1]
            
            self.window.geometry(f"{self.config.size[0]}x{self.config.size[1]}+{pos_x}+{pos_y}")
            self.window.attributes('-alpha', self.config.opacity)
            self.window.attributes('-topmost', self.config.always_on_top)
            self.window.configure(bg=self.config.background_color)
            self.window.withdraw()  # Hidden by default
            
            # Create dual-pane layout
            main_frame = tk.Frame(self.window, bg=self.config.background_color)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Original text section
            original_label = tk.Label(
                main_frame,
                text="Original:",
                bg=self.config.background_color,
                fg=self.config.text_color,
                font=tkFont.Font(family=self.config.font_family, size=self.config.font_size, weight="bold")
            )
            original_label.pack(anchor="w")
            
            self.original_text_widget = tk.Text(
                main_frame,
                height=6,
                bg=self.config.background_color,
                fg=self.config.text_color,
                font=tkFont.Font(family=self.config.font_family, size=self.config.font_size-1),
                wrap=tk.WORD,
                borderwidth=1,
                relief="sunken"
            )
            self.original_text_widget.pack(fill=tk.BOTH, expand=True, pady=(2, 10))
            
            # Translated text section
            translated_label = tk.Label(
                main_frame,
                text="Translation:",
                bg=self.config.background_color,
                fg="#ffaa00",  # Different color for translation
                font=tkFont.Font(family=self.config.font_family, size=self.config.font_size, weight="bold")
            )
            translated_label.pack(anchor="w")
            
            self.translated_text_widget = tk.Text(
                main_frame,
                height=6,
                bg=self.config.background_color,
                fg="#ffaa00",
                font=tkFont.Font(family=self.config.font_family, size=self.config.font_size-1),
                wrap=tk.WORD,
                borderwidth=1,
                relief="sunken"
            )
            self.translated_text_widget.pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            logging.error(f"Error creating translation overlay: {e}")
    
    def update_translation(self, original: str, translated: str):
        """Update translation overlay with original and translated text"""
        try:
            if not self.window:
                return
            
            self.original_text = original
            self.translated_text = translated
            
            # Update text widgets
            if self.original_text_widget:
                self.original_text_widget.delete(1.0, tk.END)
                self.original_text_widget.insert(1.0, original)
            
            if self.translated_text_widget:
                self.translated_text_widget.delete(1.0, tk.END)
                self.translated_text_widget.insert(1.0, translated)
            
            # Show if both texts are available
            if original.strip() and translated.strip():
                self.window.deiconify()
            else:
                self.window.withdraw()
                
        except Exception as e:
            logging.error(f"Error updating translation overlay: {e}")


class OverlayManager:
    """Manager for multiple overlay types"""
    
    def __init__(self):
        self.overlays = {}
        self.config = OverlayConfig()
        self.load_config()
        
        # Initialize overlays
        self.setup_overlays()
    
    def load_config(self):
        """Load overlay configuration from file"""
        config_path = "/home/nike/.config/overlay_config.json"
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                    
                    # Update config with loaded values
                    for key, value in config_data.items():
                        if hasattr(self.config, key):
                            setattr(self.config, key, value)
                            
        except Exception as e:
            logging.error(f"Error loading overlay config: {e}")
    
    def save_config(self):
        """Save overlay configuration to file"""
        config_path = "/home/nike/.config/overlay_config.json"
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        try:
            config_data = {
                'position': self.config.position,
                'size': self.config.size,
                'opacity': self.config.opacity,
                'font_size': self.config.font_size,
                'font_family': self.config.font_family,
                'background_color': self.config.background_color,
                'text_color': self.config.text_color,
                'auto_hide': self.config.auto_hide,
                'auto_hide_delay': self.config.auto_hide_delay,
                'show_metadata': self.config.show_metadata,
                'show_timestamps': self.config.show_timestamps
            }
            
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
                
        except Exception as e:
            logging.error(f"Error saving overlay config: {e}")
    
    def setup_overlays(self):
        """Initialize all overlay types"""
        try:
            # Floating overlay for main OCR results
            self.overlays['floating'] = FloatingOverlay(self.config)
            
            # Docked overlay for continuous feed
            self.overlays['docked'] = DockedOverlay(self.config, dock_position="right")
            
            # Translation overlay
            self.overlays['translation'] = TranslationOverlay(self.config)
            
            logging.info("All overlays initialized")
            
        except Exception as e:
            logging.error(f"Error setting up overlays: {e}")
    
    def update_ocr_result(self, text: str, metadata: Optional[Dict] = None):
        """Update all overlays with new OCR result"""
        try:
            # Update floating overlay
            if 'floating' in self.overlays:
                self.overlays['floating'].update_text(text, metadata)
            
            # Add to docked feed
            if 'docked' in self.overlays:
                self.overlays['docked'].add_text(text, metadata)
                
        except Exception as e:
            logging.error(f"Error updating OCR overlays: {e}")
    
    def update_translation(self, original: str, translated: str):
        """Update translation overlay"""
        try:
            if 'translation' in self.overlays:
                self.overlays['translation'].update_translation(original, translated)
                
        except Exception as e:
            logging.error(f"Error updating translation overlay: {e}")
    
    def cleanup(self):
        """Cleanup all overlays"""
        try:
            for overlay in self.overlays.values():
                if hasattr(overlay, 'destroy'):
                    overlay.destroy()
                elif hasattr(overlay, 'window') and overlay.window:
                    overlay.window.destroy()
                    
        except Exception as e:
            logging.error(f"Error cleaning up overlays: {e}")


def test_overlay_system():
    """Test the overlay system"""
    try:
        print("Testing overlay system...")
        
        # Create overlay manager
        overlay_manager = OverlayManager()
        
        # Test OCR results
        test_texts = [
            "This is a test OCR result from Discord screenshare",
            "Another line of text detected by the OCR system",
            "Testing real-time feedback display functionality"
        ]
        
        for i, text in enumerate(test_texts):
            metadata = {
                'processing_time': 1.2 + i * 0.1,
                'confidence': 90 + i * 2,
                'word_count': len(text.split())
            }
            
            overlay_manager.update_ocr_result(text, metadata)
            time.sleep(2)
        
        # Test translation
        overlay_manager.update_translation(
            "Hola, ¿cómo estás?",
            "Hello, how are you?"
        )
        
        print("Overlay test completed. Check the display windows.")
        return True
        
    except Exception as e:
        print(f"Overlay test error: {e}")
        return False


if __name__ == "__main__":
    # Test the overlay system
    test_overlay_system()
    
    # Keep the test running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down overlay test...")