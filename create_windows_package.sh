#!/bin/bash
# Script to create clean Windows package

echo "Creating Windows package..."

# Create temporary directory
TEMP_DIR="/tmp/dtf_windows_package"
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

# Copy essential files
echo "1. Copying source code..."
cp -r src "$TEMP_DIR/"
cp -r resources "$TEMP_DIR/" 2>/dev/null || mkdir -p "$TEMP_DIR/resources"

# Copy build scripts
echo "2. Copying build scripts..."
cp build_windows.py "$TEMP_DIR/" 2>/dev/null || echo "No build_windows.py found"
cp requirements.txt "$TEMP_DIR/" 2>/dev/null || echo "No requirements.txt found"

# Create README for Windows user
echo "3. Creating Windows instructions..."
cat > "$TEMP_DIR/WINDOWS_INSTRUCTIONS.txt" << 'EOT'
==========================================
DTF HALFTONER - WINDOWS SETUP INSTRUCTIONS
==========================================

WHAT YOU NEED:
1. Windows 10 or 11
2. Python 3.8 or later
3. Internet connection (for downloading packages)

STEP-BY-STEP:

1. INSTALL PYTHON
   - Download from: https://www.python.org/downloads/
   - Run installer
   - CHECK "Add Python to PATH"
   - Click "Install Now"

2. OPEN COMMAND PROMPT AS ADMINISTRATOR
   - Press Windows Key + X
   - Choose "Windows PowerShell (Admin)" or "Command Prompt (Admin)"
   - Type: python --version
   - Should show: Python 3.x.x

3. INSTALL DEPENDENCIES
   - In Command Prompt, navigate to this folder:
     cd C:\path\to\DTF_Halftoner_Project
   - Install packages:
     pip install pyinstaller pillow numpy opencv-python scikit-image PySide6

4. BUILD THE .EXE
   - Run the build script:
     python build_windows.py
   - Wait 2-5 minutes for build to complete

5. FIND YOUR .EXE
   - After build, look in: dist\DTF Halftoner Pro.exe
   - Double-click to run!

6. (OPTIONAL) CREATE INSTALLER
   - Download Inno Setup: https://jrsoftware.org/isdl.php
   - Run installer_script.iss in Inno Setup

TROUBLESHOOTING:
- If "python" not found: Reinstall Python with "Add to PATH" checked
- If pip fails: Try: python -m pip install --upgrade pip
- If build fails: Make sure you're running as Administrator

CONTACT:
If you have issues, contact: [Your Email]

EOT

# Create simple build script if none exists
if [ ! -f "$TEMP_DIR/build_windows.py" ]; then
    echo "4. Creating simple build script..."
    cat > "$TEMP_DIR/build_windows.py" << 'PYEOF'
import os
import sys
import subprocess
import platform

print("DTF Halftoner - Windows Build Script")
print("=" * 40)

# Check Windows
if platform.system() != "Windows":
    print("ERROR: This script must run on Windows!")
    print(f"You are on: {platform.system()}")
    input("Press Enter to exit...")
    sys.exit(1)

print("1. Installing dependencies...")
packages = [
    "pyinstaller",
    "pillow",
    "numpy",
    "opencv-python",
    "scikit-image",
    "PySide6",
]

for pkg in packages:
    print(f"   Installing {pkg}...")
    subprocess.run([sys.executable, "-m", "pip", "install", pkg], check=False)

print("\n2. Building executable...")
cmd = [
    "pyinstaller",
    "--name=DTF Halftoner",
    "--windowed",
    "--onefile",
    "--clean",
    "src/main.py"
]

print(f"Running: {' '.join(cmd)}")
result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode == 0:
    print("\n✅ SUCCESS!")
    print("Your .exe file is ready:")
    print("Location: dist\\DTF Halftoner.exe")
    print("\nDouble-click to run!")
else:
    print("\n❌ BUILD FAILED!")
    print("Error:", result.stderr)

input("\nPress Enter to exit...")
PYEOF
fi

# Create minimal main.py if none exists
if [ ! -f "$TEMP_DIR/src/main.py" ]; then
    echo "5. Creating minimal main.py..."
    mkdir -p "$TEMP_DIR/src"
    cat > "$TEMP_DIR/src/main.py" << 'PYEOF'
import sys
import os
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

def main():
    print("DTF Halftoner - Windows Version")
    print("=" * 40)
    
    # Platform check
    if sys.platform == "win32":
        print("Running on Windows ✓")
        import ctypes
        # Enable High DPI
        if hasattr(ctypes, 'windll'):
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
    
    # Try to run GUI
    try:
        from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton
        from PySide6.QtCore import Qt
        
        app = QApplication(sys.argv)
        app.setApplicationName("DTF Halftoner")
        
        window = QMainWindow()
        window.setWindowTitle("DTF Halftoner - Ready!")
        window.setGeometry(100, 100, 600, 400)
        
        # Create central widget
        central = QWidget()
        layout = QVBoxLayout()
        
        # Add title
        title = QLabel("DTF Halftoner")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Add message
        msg = QLabel("Application built successfully!\n\nNext: Load an image and process it.")
        msg.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg)
        
        # Add button
        btn = QPushButton("Load Image")
        btn.clicked.connect(lambda: print("Button clicked!"))
        layout.addWidget(btn)
        
        central.setLayout(layout)
        window.setCentralWidget(central)
        
        window.show()
        sys.exit(app.exec_())
        
    except ImportError as e:
        print(f"GUI Error: {e}")
        print("\nInstalling PySide6...")
        print("Run in Command Prompt (Admin):")
        print("  pip install PySide6")
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
PYEOF
fi

# Create zip file
echo "6. Creating ZIP file..."
cd /tmp
ZIP_FILE="$HOME/Desktop/DTF_Halftoner_Windows.zip"
rm -f "$ZIP_FILE"
zip -r "$ZIP_FILE" dtf_windows_package/

echo ""
echo "✅ PACKAGE CREATED!"
echo "Location: $ZIP_FILE"
echo ""
echo "NEXT STEPS:"
echo "1. Copy this ZIP file to Windows (USB, Email, Cloud)"
echo "2. Extract on Windows"
echo "3. Follow WINDOWS_INSTRUCTIONS.txt"
echo ""
echo "Package size: $(du -sh "$ZIP_FILE" | cut -f1)"
