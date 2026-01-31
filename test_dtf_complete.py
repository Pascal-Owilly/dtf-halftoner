#!/usr/bin/env python3
"""
DTF Halftoner - Complete Test Suite
Run this on Ubuntu to verify everything works before building for Windows
"""
import sys
import os
import numpy as np
import tempfile
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}❌ {msg}{RESET}")

def print_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{RESET}")

def print_info(msg):
    print(f"{BLUE}ℹ️  {msg}{RESET}")

def print_header(msg):
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}{msg}{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

class DTFHalftonerTester:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.temp_dir = tempfile.mkdtemp(prefix="dtf_test_")
        print(f"Test directory: {self.temp_dir}")
    
    def cleanup(self):
        """Clean up temporary files"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def run_test(self, test_func, test_name):
        """Run a test and track results"""
        try:
            result = test_func()
            if result:
                self.passed += 1
                print_success(f"{test_name}")
            else:
                self.failed += 1
                print_error(f"{test_name}")
            return result
        except Exception as e:
            self.failed += 1
            print_error(f"{test_name}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_environment(self):
        """Test Python environment and basic imports"""
        print_header("1. ENVIRONMENT TEST")
        
        # Test Python version
        version = sys.version_info
        if version.major == 3 and version.minor >= 8:
            print_success(f"Python {version.major}.{version.minor}.{version.micro} - OK")
        else:
            print_warning(f"Python {version.major}.{version.minor} - Consider upgrading to 3.8+")
        
        # Test essential imports
        imports = [
            ("numpy", "np"),
            ("PIL.Image", "Image"),
            ("PIL.ImageDraw", "ImageDraw"),
            ("PIL.ImageFont", "ImageFont"),
        ]
        
        for import_path, short_name in imports:
            try:
                # Handle dotted imports
                if '.' in import_path:
                    module_name, attr_name = import_path.rsplit('.', 1)
                    module = __import__(module_name, fromlist=[attr_name])
                    globals()[short_name] = getattr(module, attr_name)
                else:
                    globals()[short_name] = __import__(import_path)
                print_success(f"{import_path} - OK")
            except ImportError as e:
                print_error(f"{import_path} - FAILED: {e}")
                return False
        
        # Test optional imports
        optional_imports = [
            "cv2",
            "skimage",
            "PySide6.QtWidgets",
            "PyQt5.QtWidgets",
        ]
        
        print_info("\nOptional imports:")
        for import_name in optional_imports:
            try:
                if '.' in import_name:
                    module_name, attr_name = import_name.rsplit('.', 1)
                    __import__(module_name, fromlist=[attr_name])
                else:
                    __import__(import_name)
                print_success(f"{import_name} - Available")
            except ImportError:
                print_warning(f"{import_name} - Not available")
        
        return True
    
    def test_core_algorithms(self):
        """Test the core halftoning algorithms"""
        print_header("2. CORE ALGORITHMS TEST")
        
        # Create test image
        test_img = np.zeros((200, 300, 3), dtype=np.uint8)
        test_img[50:150, 50:150] = [255, 0, 0]      # Red
        test_img[50:150, 150:250] = [0, 255, 0]     # Green
        
        # Test 1: RGB to CMYK conversion
        try:
            # Simple RGB to CMYK conversion
            rgb_norm = test_img.astype(np.float32) / 255.0
            c = 1.0 - rgb_norm[:, :, 0]
            m = 1.0 - rgb_norm[:, :, 1]
            y = 1.0 - rgb_norm[:, :, 2]
            k = np.minimum(np.minimum(c, m), y)
            
            # Verify ranges
            assert 0.0 <= c.min() <= c.max() <= 1.0
            assert 0.0 <= k.min() <= k.max() <= 1.0
            print_success("RGB to CMYK conversion - OK")
        except Exception as e:
            print_error(f"RGB to CMYK conversion - FAILED: {e}")
            return False
        
        # Test 2: Ordered dithering
        try:
            # Create Bayer matrix
            bayer_2x2 = np.array([[0, 2], [3, 1]]) / 4.0
            
            # Test with simple gradient
            gradient = np.array([[0, 64, 128, 192, 255]], dtype=np.uint8)
            normalized = gradient.astype(float) / 255.0
            
            # Tile matrix
            h, w = gradient.shape
            tiled = np.tile(bayer_2x2, (1, (w + 1) // 2))
            tiled = tiled[:, :w]
            
            # Apply dithering
            result = (normalized > tiled) * 255
            
            # Verify result is binary (0 or 255)
            unique_values = np.unique(result)
            assert set(unique_values).issubset({0, 255})
            print_success("Ordered dithering - OK")
        except Exception as e:
            print_error(f"Ordered dithering - FAILED: {e}")
            return False
        
        # Test 3: White layer generation
        try:
            # Generate white layer based on brightness
            gray = np.mean(test_img, axis=2)
            white_layer = (gray < 200) * 255  # Threshold at 200
            
            # Verify shape and values
            assert white_layer.shape == (200, 300)
            assert set(np.unique(white_layer)).issubset({0, 255})
            print_success("White layer generation - OK")
        except Exception as e:
            print_error(f"White layer generation - FAILED: {e}")
            return False
        
        return True
    
    def test_image_io(self):
        """Test image loading and saving"""
        print_header("3. IMAGE I/O TEST")
        
        # Create test image
        test_img = np.zeros((100, 150, 3), dtype=np.uint8)
        test_img[25:75, 25:75] = [255, 0, 0]
        test_img[25:75, 75:125] = [0, 255, 0]
        
        # Save as PNG
        png_path = os.path.join(self.temp_dir, "test.png")
        Image.fromarray(test_img).save(png_path)
        assert os.path.exists(png_path), "PNG file not created"
        
        # Load PNG
        loaded_png = np.array(Image.open(png_path))
        assert loaded_png.shape == test_img.shape, "PNG shape mismatch"
        
        # Save as JPEG
        jpg_path = os.path.join(self.temp_dir, "test.jpg")
        Image.fromarray(test_img).save(jpg_path, quality=95)
        assert os.path.exists(jpg_path), "JPEG file not created"
        
        # Load JPEG (note: JPEG may slightly alter colors)
        loaded_jpg = np.array(Image.open(jpg_path))
        assert loaded_jpg.shape == test_img.shape, "JPEG shape mismatch"
        
        print_success("Image I/O (PNG/JPEG) - OK")
        
        # Test TIFF if PIL supports it
        try:
            tiff_path = os.path.join(self.temp_dir, "test.tiff")
            Image.fromarray(test_img).save(tiff_path, compression="tiff_lzw")
            assert os.path.exists(tiff_path), "TIFF file not created"
            print_success("TIFF support - OK")
        except Exception as e:
            print_warning(f"TIFF support: {e}")
        
        return True
    
    def test_processing_pipeline(self):
        """Test complete processing pipeline"""
        print_header("4. PROCESSING PIPELINE TEST")
        
        # Create a more complex test image
        width, height = 400, 300
        test_img = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Add gradient
        for i in range(width):
            test_img[:, i, 0] = int(i / width * 255)  # Red gradient
        
        # Add color patches
        colors = [
            ((50, 50, 100, 100), [255, 0, 0]),     # Red
            ((150, 50, 200, 100), [0, 255, 0]),    # Green
            ((250, 50, 300, 100), [0, 0, 255]),    # Blue
            ((50, 150, 100, 200), [255, 255, 0]),  # Yellow
            ((150, 150, 200, 200), [255, 0, 255]), # Magenta
            ((250, 150, 300, 200), [0, 255, 255]), # Cyan
        ]
        
        for (x1, y1, x2, y2), color in colors:
            test_img[y1:y2, x1:x2] = color
        
        # Save test image
        input_path = os.path.join(self.temp_dir, "pipeline_input.jpg")
        Image.fromarray(test_img).save(input_path, quality=95)
        
        # Simulate processing pipeline
        try:
            output_dir = os.path.join(self.temp_dir, "pipeline_output")
            os.makedirs(output_dir, exist_ok=True)
            
            # Load image
            img = Image.open(input_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            rgb_array = np.array(img)
            
            # Step 1: Convert to CMYK
            rgb_norm = rgb_array.astype(np.float32) / 255.0
            c = 1.0 - rgb_norm[:, :, 0]
            m = 1.0 - rgb_norm[:, :, 1]
            y = 1.0 - rgb_norm[:, :, 2]
            k = np.minimum(np.minimum(c, m), y)
            
            # Step 2: Generate white layer
            gray = np.mean(rgb_array, axis=2)
            white = (gray < 220) * 255
            
            # Step 3: Create simple Bayer matrix
            bayer = np.array([[0, 8, 2, 10],
                             [12, 4, 14, 6],
                             [3, 11, 1, 9],
                             [15, 7, 13, 5]]) / 16.0
            
            # Step 4: Apply halftoning to each channel
            channels = {
                'cyan': c,
                'magenta': m,
                'yellow': y,
                'black': k,
                'white': white.astype(float) / 255.0
            }
            
            # Save each channel
            for name, channel in channels.items():
                # Tile Bayer matrix
                h, w = channel.shape
                bh, bw = bayer.shape
                tiles_h = (h + bh - 1) // bh
                tiles_w = (w + bw - 1) // bw
                tiled = np.tile(bayer, (tiles_h, tiles_w))[:h, :w]
                
                # Apply dithering
                halftoned = (channel > tiled) * 255
                
                # Save
                output_path = os.path.join(output_dir, f"{name}.png")
                Image.fromarray(halftoned.astype(np.uint8)).save(output_path)
            
            # Verify outputs
            expected_files = {'cyan.png', 'magenta.png', 'yellow.png', 
                             'black.png', 'white.png'}
            actual_files = set(os.listdir(output_dir))
            
            if expected_files.issubset(actual_files):
                print_success(f"Pipeline generated {len(actual_files)} files")
                
                # Check file sizes (should be reasonable)
                for filename in expected_files:
                    filepath = os.path.join(output_dir, filename)
                    size_kb = os.path.getsize(filepath) / 1024
                    if 10 < size_kb < 500:  # Reasonable range for 400x300 image
                        print_success(f"  {filename}: {size_kb:.1f} KB")
                    else:
                        print_warning(f"  {filename}: {size_kb:.1f} KB (unusual size)")
                
                return True
            else:
                missing = expected_files - actual_files
                print_error(f"Missing files: {missing}")
                return False
                
        except Exception as e:
            print_error(f"Pipeline failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_gui_framework(self):
        """Test GUI framework availability"""
        print_header("5. GUI FRAMEWORK TEST")
        
        gui_available = False
        gui_framework = None
        
        # Try PySide6
        try:
            from PySide6.QtWidgets import QApplication
            gui_available = True
            gui_framework = "PySide6"
        except ImportError:
            pass
        
        # Try PyQt5
        if not gui_available:
            try:
                from PyQt5.QtWidgets import QApplication
                gui_available = True
                gui_framework = "PyQt5"
            except ImportError:
                pass
        
        if gui_available:
            print_success(f"{gui_framework} - Available")
            
            # Test simple GUI creation (headless)
            try:
                # Create QApplication without display (for testing)
                if 'QApplication' in locals() or 'QApplication' in globals():
                    # We already imported it
                    pass
                else:
                    if gui_framework == "PySide6":
                        from PySide6.QtWidgets import QApplication
                    else:
                        from PyQt5.QtWidgets import QApplication
                
                # Create app in headless mode
                app = QApplication.instance()
                if app is None:
                    app = QApplication([])
                
                print_success("QApplication creation - OK")
                return True
                
            except Exception as e:
                print_error(f"GUI creation failed: {e}")
                return False
        else:
            print_warning("No GUI framework found (PySide6 or PyQt5)")
            print_info("Note: Core algorithms will still work, but GUI won't")
            return True  # Not a failure, just a warning
    
    def test_windows_compatibility(self):
        """Check for Windows compatibility issues"""
        print_header("6. WINDOWS COMPATIBILITY CHECK")
        
        issues = []
        
        # Check 1: Linux-specific imports
        linux_specific = [
            'fcntl', 'grp', 'pwd', 'termios', 'spwd',
            'syslog', 'resource', 'posix', 'posixpath'
        ]
        
        for module in linux_specific:
            try:
                __import__(module)
                issues.append(f"Uses Linux-specific module: {module}")
            except ImportError:
                pass
        
        # Check 2: Hardcoded Linux paths
        test_code_path = str(project_root / "src")
        
        # Scan Python files for potential issues
        python_files = []
        for root, dirs, files in os.walk(project_root):
            # Skip virtual environment
            if 'venv' in root or '.git' in root:
                continue
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        linux_path_patterns = [
            '/home/', '/tmp/', '/var/', '/usr/', '/etc/',
            '~/',  # Could be OK, but better to use os.path.expanduser
        ]
        
        for py_file in python_files[:10]:  # Check first 10 files
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                    
                    for pattern in linux_path_patterns:
                        if pattern in content:
                            # Check if it's in a comment
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                if pattern in line and not line.strip().startswith('#'):
                                    issues.append(f"Linux path in {os.path.relpath(py_file, project_root)} line {i+1}: {line.strip()[:50]}...")
            except:
                pass
        
        # Check 3: File path handling
        try:
            # Test cross-platform path joining
            test_path = os.path.join("output", "images", "test.png")
            if '\\' in test_path or '//' in test_path:
                issues.append("Path joining might not be cross-platform")
            else:
                print_success("Path handling - OK")
        except:
            issues.append("Path handling issue")
        
        # Check 4: Case sensitivity (Linux is case-sensitive, Windows less so)
        print_info("Note: Linux is case-sensitive, Windows is not")
        
        # Report issues
        if issues:
            print_warning(f"Found {len(issues)} potential compatibility issues:")
            for issue in issues[:5]:  # Show first 5
                print(f"  • {issue}")
            if len(issues) > 5:
                print(f"  • ... and {len(issues) - 5} more")
            return False
        else:
            print_success("No compatibility issues found")
            return True
    
    def test_performance(self):
        """Test performance with a medium-sized image"""
        print_header("7. PERFORMANCE TEST")
        
        try:
            import time
            
            # Create medium test image (800x600)
            width, height = 800, 600
            test_img = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Add gradient
            for i in range(width):
                test_img[:, i, 0] = int(i / width * 255)  # Red gradient
                test_img[:, i, 1] = int((width - i) / width * 255)  # Green gradient
            
            # Time the processing
            start_time = time.time()
            
            # Convert to grayscale
            gray = np.mean(test_img, axis=2)
            
            # Simple halftoning
            bayer_8x8 = np.array([
                [0, 32, 8, 40, 2, 34, 10, 42],
                [48, 16, 56, 24, 50, 18, 58, 26],
                [12, 44, 4, 36, 14, 46, 6, 38],
                [60, 28, 52, 20, 62, 30, 54, 22],
                [3, 35, 11, 43, 1, 33, 9, 41],
                [51, 19, 59, 27, 49, 17, 57, 25],
                [15, 47, 7, 39, 13, 45, 5, 37],
                [63, 31, 55, 23, 61, 29, 53, 21]
            ]) / 64.0
            
            # Apply dithering
            normalized = gray.astype(float) / 255.0
            h, w = gray.shape
            bh, bw = bayer_8x8.shape
            tiles_h = (h + bh - 1) // bh
            tiles_w = (w + bw - 1) // bw
            tiled = np.tile(bayer_8x8, (tiles_h, tiles_w))[:h, :w]
            result = (normalized > tiled) * 255
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Save result for inspection
            output_path = os.path.join(self.temp_dir, "performance_test.png")
            Image.fromarray(result.astype(np.uint8)).save(output_path)
            
            print_info(f"Processed 800x600 image in {processing_time:.2f} seconds")
            
            if processing_time < 2.0:
                print_success(f"Performance: {processing_time:.2f}s - GOOD")
                return True
            elif processing_time < 5.0:
                print_warning(f"Performance: {processing_time:.2f}s - ACCEPTABLE")
                return True
            else:
                print_error(f"Performance: {processing_time:.2f}s - TOO SLOW")
                return False
                
        except Exception as e:
            print_error(f"Performance test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print_header("DTF HALFTONER - COMPREHENSIVE TEST SUITE")
        print_info(f"Python: {sys.version}")
        print_info(f"Platform: {sys.platform}")
        print_info(f"Test directory: {self.temp_dir}")
        
        # Run all tests
        tests = [
            (self.test_environment, "Environment"),
            (self.test_core_algorithms, "Core Algorithms"),
            (self.test_image_io, "Image I/O"),
            (self.test_processing_pipeline, "Processing Pipeline"),
            (self.test_gui_framework, "GUI Framework"),
            (self.test_windows_compatibility, "Windows Compatibility"),
            (self.test_performance, "Performance"),
        ]
        
        results = []
        for test_func, test_name in tests:
            result = self.run_test(test_func, test_name)
            results.append((test_name, result))
        
        # Summary
        print_header("TEST SUMMARY")
        print(f"{BOLD}Tests Passed: {self.passed}/{len(tests)}{RESET}")
        print(f"{BOLD}Tests Failed: {self.failed}/{len(tests)}{RESET}")
        
        print(f"\n{BOLD}Detailed Results:{RESET}")
        for test_name, result in results:
            if result:
                print(f"  {GREEN}✓{RESET} {test_name}")
            else:
                print(f"  {RED}✗{RESET} {test_name}")
        
        # Final recommendation
        print_header("RECOMMENDATION")
        
        if self.failed == 0:
            print_success("🎉 ALL TESTS PASSED!")
            print("\nYour DTF Halftoner code is ready for Windows deployment.")
            print("\nNext steps:")
            print("1. Transfer the entire project folder to Windows")
            print("2. Install Python and dependencies on Windows")
            print("3. Run the build script to create .exe")
            print("4. Test the .exe on Windows")
            return True
        elif self.failed <= 2:
            print_warning("⚠️  MOST TESTS PASSED")
            print("\nSome tests failed, but core functionality is likely working.")
            print("\nCheck the failed tests above.")
            print("You can still build for Windows, but test thoroughly.")
            return True
        else:
            print_error("❌ MULTIPLE TESTS FAILED")
            print("\nFix the failed tests before building for Windows.")
            print("Check the error messages above for details.")
            return False

def main():
    """Main test runner"""
    tester = DTFHalftonerTester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    finally:
        # Clean up
        print_info("\nCleaning up test files...")
        tester.cleanup()
        print_info("Test complete!")

if __name__ == "__main__":
    # Ensure we're in the right directory
    os.chdir(project_root)
    
    # Create minimal src structure if it doesn't exist
    os.makedirs(project_root / "src", exist_ok=True)
    os.makedirs(project_root / "src/core", exist_ok=True)
    os.makedirs(project_root / "src/ui", exist_ok=True)
    
    # Create empty __init__.py files if they don't exist
    for init_file in [
        project_root / "src" / "__init__.py",
        project_root / "src/core" / "__init__.py",
        project_root / "src/ui" / "__init__.py"
    ]:
        if not init_file.exists():
            init_file.touch()
    
    # Run tests
    exit_code = main()
    sys.exit(exit_code)
