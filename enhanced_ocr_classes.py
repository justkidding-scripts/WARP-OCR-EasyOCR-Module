#!/usr/bin/env python3
"""
Enhanced OCR Classes for Discord Screenshare Integration
Based on WorkingQuickOCR and WorkingFastScreenOCR with improvements

Features:
- Timeout handling to prevent OCR hangs
- Multiple OCR engines (Tesseract, PaddleOCR, EasyOCR)
- Image preprocessing optimization
- Performance monitoring
- Multi-threaded processing
"""

import cv2
import numpy as np
import pytesseract
import threading
import time
import queue
import logging
from PIL import Image
import subprocess
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import signal
import os

class WorkingQuickOCR:
    """Enhanced OCR class with timeout handling and multiple engines"""
    
    def __init__(self, timeout=5.0, engine='tesseract'):
        self.timeout = timeout
        self.engine = engine
        self.performance_stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'timeout_calls': 0,
            'avg_processing_time': 0.0
        }
        
        # Initialize OCR engine
        self._setup_ocr_engine()
        
    def _setup_ocr_engine(self):
        """Setup the OCR engine based on selection"""
        if self.engine == 'tesseract':
            pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
            self.tesseract_config = '--oem 3 --psm 6'
        elif self.engine == 'easyocr':
            try:
                import easyocr
                # Initialize with CPU/GPU auto-detection
                self.easyocr_reader = easyocr.Reader(['en'], gpu=False)  # CPU mode for stability
                logging.info("EasyOCR initialized successfully")
            except ImportError as e:
                logging.warning(f"EasyOCR not available: {e}, falling back to Tesseract")
                self.engine = 'tesseract'
                self._setup_ocr_engine()  # Re-setup with Tesseract
            except Exception as e:
                logging.error(f"EasyOCR initialization failed: {e}, falling back to Tesseract")
                self.engine = 'tesseract'
                self._setup_ocr_engine()  # Re-setup with Tesseract
        elif self.engine == 'paddleocr':
            try:
                from paddleocr import PaddleOCR
                self.paddleocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            except ImportError:
                logging.warning("PaddleOCR not available, falling back to Tesseract")
                self.engine = 'tesseract'

    def preprocess_image(self, image, enhance_contrast=True, denoise=True):
        """Advanced image preprocessing for better OCR results"""
        try:
            if isinstance(image, np.ndarray):
                processed = image.copy()
            else:
                processed = np.array(image)
            
            # Convert to grayscale if needed
            if len(processed.shape) == 3:
                processed = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
            
            # Enhance contrast
            if enhance_contrast:
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                processed = clahe.apply(processed)
            
            # Denoise
            if denoise:
                processed = cv2.fastNlMeansDenoising(processed)
            
            # Apply adaptive thresholding
            processed = cv2.adaptiveThreshold(
                processed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Morphological operations to clean up
            kernel = np.ones((1,1), np.uint8)
            processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)
            
            # Scale up for better OCR (2x scaling)
            height, width = processed.shape
            processed = cv2.resize(processed, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)
            
            return processed
            
        except Exception as e:
            logging.error(f"Error in image preprocessing: {e}")
            return image

    def ocr_with_timeout(self, image, timeout=None):
        """Perform OCR with timeout protection using your proven timeout fix"""
        if timeout is None:
            timeout = self.timeout
            
        start_time = time.time()
        self.performance_stats['total_calls'] += 1
        
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image)
            
            # Create result containers for thread communication
            result_queue = queue.Queue()
            error_queue = queue.Queue()
            
            def ocr_worker():
                """Worker function that runs OCR in separate thread"""
                try:
                    # Use the processed image from outer scope
                    ocr_image = processed_image
                    
                    if self.engine == 'tesseract':
                        text = pytesseract.image_to_string(ocr_image, config=self.tesseract_config)
                    elif self.engine == 'easyocr':
                        # Convert image format for EasyOCR if needed
                        if len(ocr_image.shape) == 2:  # Grayscale
                            # EasyOCR works better with RGB images
                            import cv2
                            ocr_image = cv2.cvtColor(ocr_image, cv2.COLOR_GRAY2RGB)
                        results = self.easyocr_reader.readtext(ocr_image)
                        # Extract text from EasyOCR results (format: [bbox, text, confidence])
                        text = ' '.join([result[1] for result in results if len(result) > 1])
                    elif self.engine == 'paddleocr':
                        results = self.paddleocr.ocr(ocr_image, cls=True)
                        text = ' '.join([line[1][0] for line in results[0] if line])
                    else:
                        text = pytesseract.image_to_string(ocr_image, config=self.tesseract_config)
                    
                    result_queue.put(text.strip())
                except Exception as e:
                    error_queue.put(str(e))
            
            # Start OCR in separate thread
            ocr_thread = threading.Thread(target=ocr_worker, daemon=True)
            ocr_thread.start()
            
            # Wait for result with timeout
            ocr_thread.join(timeout=timeout)
            
            if ocr_thread.is_alive():
                # Timeout occurred
                self.performance_stats['timeout_calls'] += 1
                logging.warning(f"OCR timeout after {timeout}s")
                return ""
            
            # Check for errors
            if not error_queue.empty():
                error_msg = error_queue.get()
                logging.error(f"OCR error: {error_msg}")
                return ""
            
            # Get successful result
            if not result_queue.empty():
                result = result_queue.get()
                self.performance_stats['successful_calls'] += 1
                
                # Update performance stats
                processing_time = time.time() - start_time
                self.performance_stats['avg_processing_time'] = (
                    self.performance_stats['avg_processing_time'] * 0.9 + processing_time * 0.1
                )
                
                return result
            
            return ""
            
        except Exception as e:
            logging.error(f"OCR processing error: {e}")
            return ""

    def get_performance_stats(self):
        """Get performance statistics"""
        stats = self.performance_stats.copy()
        if stats['total_calls'] > 0:
            stats['success_rate'] = stats['successful_calls'] / stats['total_calls'] * 100
            stats['timeout_rate'] = stats['timeout_calls'] / stats['total_calls'] * 100
        else:
            stats['success_rate'] = 0
            stats['timeout_rate'] = 0
        return stats


class WorkingFastScreenOCR(WorkingQuickOCR):
    """Fast screen-optimized OCR class for real-time processing"""
    
    def __init__(self, timeout=3.0, engine='tesseract', cache_size=50):
        super().__init__(timeout, engine)
        self.cache_size = cache_size
        self.text_cache = {}
        self.last_processed_hash = None
        self.duplicate_threshold = 0.8
        
    def _calculate_image_hash(self, image):
        """Calculate simple hash for image comparison"""
        try:
            # Resize to small size for hash calculation
            small_image = cv2.resize(image, (8, 8))
            return hash(small_image.tobytes())
        except:
            return None
    
    def _is_similar_to_cached(self, current_hash):
        """Check if current image is similar to recently processed ones"""
        if not current_hash or not self.text_cache:
            return False
        
        # Check if exact hash exists
        if current_hash in self.text_cache:
            return True
        
        # For performance, don't do complex similarity matching in fast mode
        return False
    
    def fast_ocr(self, image, force_process=False):
        """Fast OCR with caching and duplicate detection"""
        try:
            # Calculate image hash for duplicate detection
            image_hash = self._calculate_image_hash(image)
            
            if not force_process and self._is_similar_to_cached(image_hash):
                return self.text_cache.get(image_hash, "")
            
            # Perform OCR with shorter timeout for real-time processing
            result = self.ocr_with_timeout(image, timeout=self.timeout)
            
            # Cache result
            if image_hash and result:
                self.text_cache[image_hash] = result
                
                # Limit cache size
                if len(self.text_cache) > self.cache_size:
                    # Remove oldest entries (simple FIFO)
                    oldest_key = list(self.text_cache.keys())[0]
                    del self.text_cache[oldest_key]
            
            return result
            
        except Exception as e:
            logging.error(f"Fast OCR error: {e}")
            return ""
    
    def batch_ocr(self, images, max_workers=3):
        """Process multiple images in parallel"""
        if not images:
            return []
        
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_image = {
                executor.submit(self.fast_ocr, img): img for img in images
            }
            
            for future in future_to_image:
                try:
                    result = future.result(timeout=self.timeout + 1)
                    results.append(result)
                except TimeoutError:
                    logging.warning("Batch OCR timeout")
                    results.append("")
                except Exception as e:
                    logging.error(f"Batch OCR error: {e}")
                    results.append("")
        
        return results

class DiscordOptimizedOCR(WorkingFastScreenOCR):
    """Discord-specific OCR optimizations"""
    
    def __init__(self, timeout=2.0):
        super().__init__(timeout=timeout, engine='tesseract')
        
        # Discord-specific settings
        self.tesseract_config = '--oem 3 --psm 6'  # Simplified for speed
        self.min_text_length = 3  # Ignore very short detections
        self.discord_text_regions = []  # ROI for common Discord text areas
        
    def preprocess_discord_image(self, image):
        """Discord-specific image preprocessing"""
        try:
            processed = image.copy()
            
            # Focus on text-heavy regions (chat area, usernames, etc.)
            # This could be enhanced with ROI detection for Discord UI
            
            # Convert to grayscale
            if len(processed.shape) == 3:
                processed = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
            
            # Simple thresholding for Discord's dark theme
            processed = cv2.threshold(processed, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            # Light morphological operations
            kernel = np.ones((1,1), np.uint8)
            processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)
            
            return processed
            
        except Exception as e:
            logging.error(f"Discord image preprocessing error: {e}")
            return image
    
    def extract_discord_text(self, image):
        """Extract text optimized for Discord interface"""
        try:
            # Use Discord-specific preprocessing
            processed = self.preprocess_discord_image(image)
            
            # Perform OCR with timeout
            text = self.ocr_with_timeout(processed)
            
            # Filter results
            if text and len(text.strip()) >= self.min_text_length:
                # Basic cleanup for Discord text
                text = text.replace('\n\n', '\n').strip()
                return text
            
            return ""
            
        except Exception as e:
            logging.error(f"Discord text extraction error: {e}")
            return ""

def test_ocr_classes():
    """Test the OCR classes with sample image"""
    try:
        # Create test image with text
        test_image = np.ones((200, 600, 3), dtype=np.uint8) * 255
        cv2.putText(test_image, "Test Discord Message", (50, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        print("Testing OCR Classes...")
        print("=" * 40)
        
        # Test WorkingQuickOCR
        quick_ocr = WorkingQuickOCR(timeout=5.0)
        result1 = quick_ocr.ocr_with_timeout(test_image)
        print(f"WorkingQuickOCR result: '{result1}'")
        print(f"Performance stats: {quick_ocr.get_performance_stats()}")
        
        # Test WorkingFastScreenOCR
        fast_ocr = WorkingFastScreenOCR(timeout=3.0)
        result2 = fast_ocr.fast_ocr(test_image)
        print(f"WorkingFastScreenOCR result: '{result2}'")
        
        # Test DiscordOptimizedOCR
        discord_ocr = DiscordOptimizedOCR(timeout=2.0)
        result3 = discord_ocr.extract_discord_text(test_image)
        print(f"DiscordOptimizedOCR result: '{result3}'")
        
        return True
        
    except Exception as e:
        print(f"OCR test error: {e}")
        return False

if __name__ == "__main__":
    # Test the OCR classes
    test_ocr_classes()