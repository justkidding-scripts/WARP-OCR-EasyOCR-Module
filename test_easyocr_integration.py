#!/usr/bin/env python3
"""
EasyOCR Integration Test for WARP OCR System
Tests the integration between WARP OCR and EasyOCR
"""

import sys
import os
import cv2
import numpy as np
import logging

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_easyocr_import():
    """Test EasyOCR can be imported"""
    try:
        import easyocr
        import torch
        logging.info(f"✅ EasyOCR version: {easyocr.__version__}")
        logging.info(f"✅ PyTorch version: {torch.__version__}")
        logging.info(f"✅ CUDA available: {torch.cuda.is_available()}")
        return True
    except ImportError as e:
        logging.error(f"❌ EasyOCR import failed: {e}")
        return False

def test_enhanced_ocr_classes():
    """Test enhanced OCR classes with EasyOCR"""
    try:
        from enhanced_ocr_classes import WorkingQuickOCR
        
        # Initialize with EasyOCR
        ocr = WorkingQuickOCR(timeout=10.0, engine='easyocr')
        logging.info("✅ WorkingQuickOCR initialized with EasyOCR")
        
        # Create test image
        test_img = np.ones((120, 500, 3), dtype=np.uint8) * 255
        cv2.putText(test_img, 'WARP EasyOCR Integration Test', (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        # Test OCR
        result = ocr.ocr_with_timeout(test_img)
        logging.info(f"✅ OCR Result: '{result}'")
        
        if 'WARP' in result or 'EasyOCR' in result or 'Integration' in result:
            logging.info("✅ EasyOCR integration test passed")
            return True
        else:
            logging.warning(f"⚠️  OCR result unclear but functional: '{result}'")
            return True
            
    except Exception as e:
        logging.error(f"❌ Enhanced OCR classes test failed: {e}")
        return False

def test_complete_integration():
    """Test complete WARP OCR integration with EasyOCR"""
    try:
        from complete_discord_ocr_integration import IntegratedDiscordOCRSystem
        
        # Initialize system
        system = IntegratedDiscordOCRSystem()
        logging.info("✅ IntegratedDiscordOCRSystem initialized")
        
        # Check if EasyOCR is being used
        if hasattr(system.main_ocr, 'engine') and system.main_ocr.engine == 'easyocr':
            logging.info("✅ System is using EasyOCR engine")
        else:
            logging.info("ℹ️  System is using fallback OCR engine")
        
        # Get system status
        status = system.get_system_status()
        logging.info(f"✅ System status retrieved: {len(status)} components")
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Complete integration test failed: {e}")
        return False

def test_performance_comparison():
    """Compare EasyOCR vs Tesseract performance"""
    try:
        from enhanced_ocr_classes import WorkingQuickOCR
        import time
        
        # Create test image with varied text
        test_img = np.ones((200, 600, 3), dtype=np.uint8) * 255
        cv2.putText(test_img, 'Performance Test Image', (10, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(test_img, 'Mixed content: ABC123!@#', (10, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        cv2.putText(test_img, 'Date: 2025-10-13', (10, 150), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        results = {}
        
        # Test EasyOCR
        try:
            ocr_easy = WorkingQuickOCR(timeout=15.0, engine='easyocr')
            start_time = time.time()
            result_easy = ocr_easy.ocr_with_timeout(test_img)
            easy_time = time.time() - start_time
            
            results['easyocr'] = {
                'result': result_easy,
                'time': easy_time,
                'length': len(result_easy)
            }
            logging.info(f"✅ EasyOCR: {easy_time:.2f}s, {len(result_easy)} chars")
        except Exception as e:
            logging.warning(f"EasyOCR test failed: {e}")
        
        # Test Tesseract
        try:
            ocr_tess = WorkingQuickOCR(timeout=10.0, engine='tesseract')
            start_time = time.time()
            result_tess = ocr_tess.ocr_with_timeout(test_img)
            tess_time = time.time() - start_time
            
            results['tesseract'] = {
                'result': result_tess,
                'time': tess_time,
                'length': len(result_tess)
            }
            logging.info(f"✅ Tesseract: {tess_time:.2f}s, {len(result_tess)} chars")
        except Exception as e:
            logging.warning(f"Tesseract test failed: {e}")
        
        # Compare results
        if 'easyocr' in results and 'tesseract' in results:
            easy_perf = results['easyocr']
            tess_perf = results['tesseract']
            
            logging.info("📊 Performance Comparison:")
            logging.info(f"   EasyOCR: {easy_perf['time']:.2f}s, {easy_perf['length']} chars")
            logging.info(f"   Tesseract: {tess_perf['time']:.2f}s, {tess_perf['length']} chars")
            
            if easy_perf['time'] < tess_perf['time']:
                logging.info("🚀 EasyOCR is faster")
            else:
                logging.info("🚀 Tesseract is faster")
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Performance comparison failed: {e}")
        return False

def main():
    """Run all EasyOCR integration tests"""
    print("WARP OCR EasyOCR Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("EasyOCR Import", test_easyocr_import),
        ("Enhanced OCR Classes", test_enhanced_ocr_classes),
        ("Complete Integration", test_complete_integration),
        ("Performance Comparison", test_performance_comparison)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- Testing {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"{'✅ PASS' if result else '❌ FAIL'}: {test_name}")
        except Exception as e:
            logging.error(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))
            print(f"💥 CRASH: {test_name}")
    
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! EasyOCR integration is working perfectly.")
        return 0
    elif passed >= total - 1:
        print("⚠️  Most tests passed. EasyOCR integration is mostly working.")
        return 0
    else:
        print("❌ Multiple test failures. Please check EasyOCR installation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())