# src/main.py
import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

# Add src directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import DTFMainWindow

def main():
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("DTF Halftoner Pro")
    app.setOrganizationName("DTF Tools")
    
    # Enable High DPI scaling
    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Load application icon (if available)
    icon_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "resources",
        "icons",
        "app_icon.ico"
    )
    
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Create and show main window
    window = DTFMainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()