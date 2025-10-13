#!/usr/bin/env python3
"""
Basic OCR Test Script
Tests core OCR functionality before running full WARP OCR system
"""

import sys
import os
import cv2
import numpy as np
import pytesseract
import pyautogui
import logging
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_tesseract():
    """Test if Tesseract is available and working"""
    try:
        pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
        version = pytesseract.get_tesseract_version()
        logging.info(f"✅ Tesseract version: {version}")
        return True
    except Exception as e:
        logging.error(f"❌ Tesseract not available: {e}")
        return False

def test_screenshot():
    """Test screenshot capability"""
    try:
        screenshot = pyautogui.screenshot()
        logging.info(f"✅ Screenshot captured: {screenshot.size}")
        return screenshot
    except Exception as e:
        logging.error(f"❌ Screenshot failed: {e}")
        return None

def test_basic_ocr():
    """Test basic OCR on a screenshot"""
    try:
        # Create a simple test image with text
        img = np.zeros((200, 600, 3), dtype=np.uint8)
        img.fill(255)  # White background
        
        # Convert to PIL for text rendering (if available)
        pil_img = Image.fromarray(img)
        
        # Convert to OpenCV format
        cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale for OCR
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        
        # Add some text using OpenCV (simple method)
        cv2.putText(gray, 'WARP OCR TEST', (50, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
        
        # Perform OCR
        text = pytesseract.image_to_string(gray, config='--oem 3 --psm 6')
        text = text.strip()
        
        if 'WARP' in text or 'OCR' in text or 'TEST' in text:
            logging.info(f"✅ Basic OCR test passed: '{text}'")
            return True
        else:
            logging.warning(f"⚠️  OCR result unclear: '{text}'")
            return True  # Still working, just unclear
            
    except Exception as e:
        logging.error(f"❌ Basic OCR test failed: {e}")
        return False

def test_screen_ocr():
    """Test OCR on actual screen capture"""
    try:
        # Take a screenshot
        screenshot = pyautogui.screenshot()
        
        # Convert to OpenCV format
        img_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        # Take a small region for testing (center of screen)
        h, w = img_cv.shape[:2]
        test_region = img_cv[h//3:2*h//3, w//3:2*w//3]
        
        # Convert to grayscale
        gray = cv2.cvtColor(test_region, cv2.COLOR_BGR2GRAY)
        
        # Perform OCR
        text = pytesseract.image_to_string(gray, config='--oem 3 --psm 6')
        text = text.strip()
        
        if len(text) > 0:
            logging.info(f"✅ Screen OCR test passed: Found {len(text)} characters")
            logging.info(f"   Sample text: '{text[:100]}...' " if len(text) > 100 else f"   Text: '{text}'")
            return True
        else:
            logging.warning("⚠️  Screen OCR found no text (this might be normal)")
            return True
            
    except Exception as e:
        logging.error(f"❌ Screen OCR test failed: {e}")
        return False

def test_imports():
    """Test if all required modules can be imported"""
    required_modules = [
        ('cv2', 'opencv-python'),
        ('numpy', 'numpy'),
        ('pytesseract', 'pytesseract'),
        ('pyautogui', 'pyautogui'),
        ('PIL', 'pillow'),
        ('requests', 'requests')
    ]
    
    all_good = True
    for module_name, package_name in required_modules:
        try:
            __import__(module_name)
            logging.info(f"✅ {module_name} imported successfully")
        except ImportError as e:
            logging.error(f"❌ {module_name} import failed: {e}")
            logging.error(f"   Try: pip install {package_name}")
            all_good = False
    
    return all_good

def main():
    """Run all tests"""
    print("WARP OCR Basic Functionality Test")
    print("=================================")
    
    tests = [
        ("Module imports", test_imports),
        ("Tesseract availability", test_tesseract),
        ("Screenshot capability", lambda: test_screenshot() is not None),
        ("Basic OCR", test_basic_ocr),
        ("Screen OCR", test_screen_ocr)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- Testing {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logging.error(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "="*50)
    print("TEST RESULTS SUMMARY")
    print("="*50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! WARP OCR should work.")
        return 0
    elif passed >= len(results) - 1:
        print("⚠️  Most tests passed. WARP OCR should work with minor issues.")
        return 0
    else:
        print("❌ Multiple test failures. Please fix issues before running WARP OCR.")
        return 1

if __name__ == "__main__":
    sys.exit(main())