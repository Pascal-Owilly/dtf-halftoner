# src/ui/main_window.py
import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import numpy as np
from PIL import Image, ImageQt

# Import our core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import DTFConfig
from core.processor import DTFProcessor

class ModernButton(QPushButton):
    """Custom styled button"""
    def __init__(self, text, icon=None, parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(32)
        self.setStyleSheet("""
            QPushButton {
                background-color: #4a86e8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a76d8;
            }
            QPushButton:pressed {
                background-color: #2a66c8;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        
        if icon:
            self.setIcon(icon)

class ModernSlider(QWidget):
    """Slider with label and value display"""
    valueChanged = pyqtSignal(int)
    
    def __init__(self, label, min_val, max_val, default_val, parent=None):
        super().__init__(parent)
        
        self.label = QLabel(label)
        self.label.setFixedWidth(80)
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(min_val, max_val)
        self.slider.setValue(default_val)
        
        self.value_display = QLabel(str(default_val))
        self.value_display.setFixedWidth(40)
        self.value_display.setAlignment(Qt.AlignCenter)
        
        layout = QHBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.slider)
        layout.addWidget(self.value_display)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        self.slider.valueChanged.connect(self.update_display)
        self.slider.valueChanged.connect(self.valueChanged)
    
    def update_display(self, value):
        self.value_display.setText(str(value))
    
    def value(self):
        return self.slider.value()
    
    def setValue(self, value):
        self.slider.setValue(value)

class ImagePreviewWidget(QWidget):
    """Widget for displaying and comparing images"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_pixmap = None
        self.processed_pixmap = None
        self.show_original = True
        self.zoom_factor = 1.0
        
        self.setMinimumSize(400, 300)
        
    def set_images(self, original, processed):
        """Set original and processed images"""
        if original is not None:
            # Convert numpy array to QPixmap
            if isinstance(original, np.ndarray):
                original = Image.fromarray(original)
            
            if isinstance(original, Image.Image):
                original = ImageQt.ImageQt(original)
            
            self.original_pixmap = QPixmap.fromImage(original)
        
        if processed is not None:
            if isinstance(processed, np.ndarray):
                processed = Image.fromarray(processed)
            
            if isinstance(processed, Image.Image):
                processed = ImageQt.ImageQt(processed)
            
            self.processed_pixmap = QPixmap.fromImage(processed)
        
        self.update()
    
    def paintEvent(self, event):
        """Paint the widget"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Fill background
        painter.fillRect(self.rect(), QColor(240, 240, 240))
        
        if self.show_original and self.original_pixmap:
            self.draw_pixmap(painter, self.original_pixmap, "Original")
        elif self.processed_pixmap:
            self.draw_pixmap(painter, self.processed_pixmap, "Processed")
    
    def draw_pixmap(self, painter, pixmap, label):
        """Draw pixmap centered with label"""
        # Scale pixmap
        scaled_pixmap = pixmap.scaled(
            int(pixmap.width() * self.zoom_factor),
            int(pixmap.height() * self.zoom_factor),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        # Center in widget
        x = (self.width() - scaled_pixmap.width()) // 2
        y = (self.height() - scaled_pixmap.height()) // 2
        
        # Draw shadow
        shadow_rect = QRect(x + 3, y + 3, scaled_pixmap.width(), scaled_pixmap.height())
        painter.fillRect(shadow_rect, QColor(0, 0, 0, 100))
        
        # Draw pixmap
        painter.drawPixmap(x, y, scaled_pixmap)
        
        # Draw border
        painter.setPen(QColor(200, 200, 200))
        painter.drawRect(x, y, scaled_pixmap.width(), scaled_pixmap.height())
        
        # Draw label
        painter.setPen(QColor(80, 80, 80))
        painter.drawText(x + 10, y + 20, label)

class ChannelToggleWidget(QWidget):
    """Widget for toggling channel visibility"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.channels = {
            'C': QCheckBox('Cyan'),
            'M': QCheckBox('Magenta'),
            'Y': QCheckBox('Yellow'),
            'K': QCheckBox('Black'),
            'W': QCheckBox('White'),
            'RGB': QCheckBox('RGB')
        }
        
        # Set colors for channel labels
        self.channels['C'].setStyleSheet("QCheckBox { color: #00ffff; }")
        self.channels['M'].setStyleSheet("QCheckBox { color: #ff00ff; }")
        self.channels['Y'].setStyleSheet("QCheckBox { color: #ffff00; }")
        self.channels['K'].setStyleSheet("QCheckBox { color: #000000; }")
        self.channels['W'].setStyleSheet("QCheckBox { color: #ffffff; background-color: #666666; }")
        
        # Default: all checked
        for checkbox in self.channels.values():
            checkbox.setChecked(True)
        
        layout = QHBoxLayout()
        for checkbox in self.channels.values():
            layout.addWidget(checkbox)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def get_visible_channels(self):
        """Return list of visible channel names"""
        visible = []
        for key, checkbox in self.channels.items():
            if checkbox.isChecked():
                visible.append(key.lower())
        return visible

class DTFMainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize configuration
        self.config = DTFConfig()
        self.processor = DTFProcessor(self.config)
        
        # UI state
        self.current_image_path = None
        self.original_image = None
        self.processed_image = None
        
        self.init_ui()
        self.setWindowTitle("DTF Halftoner Pro")
        self.resize(1200, 800)
        
        # Apply custom style
        self.apply_stylesheet()
    
    def init_ui(self):
        """Initialize the user interface"""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Left panel (settings)
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 1)
        
        # Right panel (preview)
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 2)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def create_left_panel(self):
        """Create left panel with settings"""
        panel = QWidget()
        panel.setMaximumWidth(350)
        
        layout = QVBoxLayout()
        
        # File section
        file_group = self.create_file_section()
        layout.addWidget(file_group)
        
        # Halftone settings
        settings_group = self.create_settings_section()
        layout.addWidget(settings_group)
        
        # Channel controls
        channel_group = self.create_channel_section()
        layout.addWidget(channel_group)
        
        # White layer settings
        white_group = self.create_white_layer_section()
        layout.addWidget(white_group)
        
        # Process button
        self.process_btn = ModernButton("Process Image")
        self.process_btn.clicked.connect(self.process_image)
        self.process_btn.setEnabled(False)
        layout.addWidget(self.process_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        panel.setLayout(layout)
        
        return panel
    
    def create_file_section(self):
        """Create file selection section"""
        group = QGroupBox("File")
        layout = QVBoxLayout()
        
        # Load button
        self.load_btn = ModernButton("Load Image...")
        self.load_btn.clicked.connect(self.load_image)
        layout.addWidget(self.load_btn)
        
        # Image info
        self.image_info = QLabel("No image loaded")
        self.image_info.setWordWrap(True)
        layout.addWidget(self.image_info)
        
        # Save buttons
        save_layout = QHBoxLayout()
        self.save_btn = ModernButton("Save All")
        self.save_btn.clicked.connect(self.save_results)
        self.save_btn.setEnabled(False)
        save_layout.addWidget(self.save_btn)
        
        self.export_btn = ModernButton("Export...")
        self.export_btn.clicked.connect(self.export_settings)
        save_layout.addWidget(self.export_btn)
        
        layout.addLayout(save_layout)
        
        group.setLayout(layout)
        return group
    
    def create_settings_section(self):
        """Create halftone settings section"""
        group = QGroupBox("Halftone Settings")
        layout = QVBoxLayout()
        
        # DPI
        self.dpi_slider = ModernSlider("DPI:", 150, 1200, 600)
        self.dpi_slider.valueChanged.connect(self.update_dpi)
        layout.addWidget(self.dpi_slider)
        
        # LPI
        self.lpi_slider = ModernSlider("LPI:", 10, 100, 55)
        self.lpi_slider.valueChanged.connect(self.update_lpi)
        layout.addWidget(self.lpi_slider)
        
        # Method selection
        method_layout = QHBoxLayout()
        method_layout.addWidget(QLabel("Method:"))
        
        self.method_combo = QComboBox()
        self.method_combo.addItems(["Ordered Dithering", "Error Diffusion", "Hybrid"])
        self.method_combo.currentTextChanged.connect(self.update_method)
        method_layout.addWidget(self.method_combo)
        
        layout.addLayout(method_layout)
        
        # Matrix size (for ordered dithering)
        self.matrix_combo = QComboBox()
        self.matrix_combo.addItems(["4x4", "8x8", "16x16"])
        self.matrix_combo.currentIndexChanged.connect(self.update_matrix_size)
        
        matrix_layout = QHBoxLayout()
        matrix_layout.addWidget(QLabel("Matrix:"))
        matrix_layout.addWidget(self.matrix_combo)
        matrix_layout.addStretch()
        layout.addLayout(matrix_layout)
        
        group.setLayout(layout)
        return group
    
    def create_channel_section(self):
        """Create channel controls section"""
        group = QGroupBox("Channels")
        layout = QVBoxLayout()
        
        # Channel toggles
        self.channel_toggles = ChannelToggleWidget()
        layout.addWidget(self.channel_toggles)
        
        # Individual channel settings button
        self.channel_settings_btn = QPushButton("Channel Settings...")
        self.channel_settings_btn.clicked.connect(self.show_channel_settings)
        layout.addWidget(self.channel_settings_btn)
        
        group.setLayout(layout)
        return group
    
    def create_white_layer_section(self):
        """Create white layer settings section"""
        group = QGroupBox("White Layer")
        layout = QVBoxLayout()
        
        # Method selection
        white_layout = QHBoxLayout()
        white_layout.addWidget(QLabel("Method:"))
        
        self.white_combo = QComboBox()
        self.white_combo.addItems(["Full", "Halftone", "Edge Enhanced"])
        self.white_combo.currentTextChanged.connect(self.update_white_method)
        white_layout.addWidget(self.white_combo)
        
        layout.addLayout(white_layout)
        
        # Threshold slider
        self.threshold_slider = ModernSlider("Threshold:", 0, 100, 75)
        self.threshold_slider.valueChanged.connect(self.update_threshold)
        layout.addWidget(self.threshold_slider)
        
        # Preview white only checkbox
        self.preview_white = QCheckBox("Preview white layer only")
        self.preview_white.stateChanged.connect(self.update_preview)
        layout.addWidget(self.preview_white)
        
        group.setLayout(layout)
        return group
    
    def create_right_panel(self):
        """Create right panel with preview"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Preview widget
        self.preview_widget = ImagePreviewWidget()
        layout.addWidget(self.preview_widget, 1)
        
        # Preview controls
        controls = QHBoxLayout()
        
        # Zoom controls
        controls.addWidget(QLabel("Zoom:"))
        self.zoom_combo = QComboBox()
        self.zoom_combo.addItems(["25%", "50%", "100%", "200%", "400%"])
        self.zoom_combo.setCurrentText("100%")
        self.zoom_combo.currentTextChanged.connect(self.update_zoom)
        controls.addWidget(self.zoom_combo)
        
        # View mode
        controls.addWidget(QLabel("View:"))
        self.view_combo = QComboBox()
        self.view_combo.addItems(["Original", "Processed", "Side by Side"])
        self.view_combo.currentTextChanged.connect(self.update_view_mode)
        controls.addWidget(self.view_combo)
        
        controls.addStretch()
        layout.addLayout(controls)
        
        panel.setLayout(layout)
        return panel
    
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        open_action = QAction('Open Image...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.load_image)
        file_menu.addAction(open_action)
        
        save_action = QAction('Save Results...', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_results)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Alt+F4')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu('Edit')
        
        settings_action = QAction('Settings...', self)
        settings_action.triggered.connect(self.show_settings)
        edit_menu.addAction(settings_action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        zoom_in = QAction('Zoom In', self)
        zoom_in.setShortcut('Ctrl++')
        zoom_in.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in)
        
        zoom_out = QAction('Zoom Out', self)
        zoom_out.setShortcut('Ctrl+-')
        zoom_out.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def apply_stylesheet(self):
        """Apply custom stylesheet for modern look"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            QLabel {
                color: #333333;
            }
            
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 3px;
                text-align: center;
            }
            
            QProgressBar::chunk {
                background-color: #4a86e8;
                border-radius: 3px;
            }
            
            QComboBox {
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 3px;
                background-color: white;
            }
            
            QComboBox:hover {
                border-color: #4a86e8;
            }
            
            QSlider::groove:horizontal {
                height: 4px;
                background: #dddddd;
                border-radius: 2px;
            }
            
            QSlider::handle:horizontal {
                background: #4a86e8;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            
            QCheckBox {
                spacing: 5px;
            }
            
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)
    
    # ===== Event Handlers =====
    
    def load_image(self):
        """Load image from file"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff);;All Files (*)"
        )
        
        if path:
            self.current_image_path = path
            
            # Load and display image
            self.original_image = self.processor.load_image(path)
            if self.original_image is not None:
                self.preview_widget.set_images(self.original_image, None)
                
                # Update image info
                h, w, _ = self.original_image.shape
                self.image_info.setText(
                    f"<b>{os.path.basename(path)}</b><br>"
                    f"Size: {w} × {h} pixels<br>"
                    f"Mode: RGB"
                )
                
                # Enable process button
                self.process_btn.setEnabled(True)
                
                self.status_bar.showMessage(f"Loaded: {os.path.basename(path)}")
    
    def process_image(self):
        """Process the loaded image"""
        if self.original_image is None:
            QMessageBox.warning(self, "Warning", "Please load an image first.")
            return
        
        # Disable UI during processing
        self.process_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Process in separate thread to keep UI responsive
        self.worker_thread = QThread()
        self.worker = ProcessingWorker(
            self.processor,
            self.original_image
        )
        self.worker.moveToThread(self.worker_thread)
        
        # Connect signals
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_processing_finished)
        self.worker.error.connect(self.on_processing_error)
        
        # Start thread
        self.worker_thread.started.connect(self.worker.process)
        self.worker_thread.start()
    
    def update_progress(self, step, message):
        """Update progress bar"""
        total_steps = 8
        percentage = int((step / total_steps) * 100)
        self.progress_bar.setValue(percentage)
        self.status_bar.showMessage(message)
    
    def on_processing_finished(self, result):
        """Handle processing completion"""
        self.worker_thread.quit()
        self.worker_thread.wait()
        
        self.processed_image = self.processor.create_preview()
        self.preview_widget.set_images(self.original_image, self.processed_image)
        
        # Enable save button
        self.save_btn.setEnabled(True)
        
        # Reset UI
        self.process_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        self.status_bar.showMessage("Processing complete!")
    
    def on_processing_error(self, error_msg):
        """Handle processing error"""
        self.worker_thread.quit()
        self.worker_thread.wait()
        
        QMessageBox.critical(self, "Processing Error", error_msg)
        
        # Reset UI
        self.process_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        self.status_bar.showMessage("Processing failed")
    
    def save_results(self):
        """Save processed results"""
        if not self.processor.results:
            QMessageBox.warning(self, "Warning", "No processed results to save.")
            return
        
        # Ask for output directory
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            os.path.dirname(self.current_image_path) if self.current_image_path else ""
        )
        
        if output_dir:
            try:
                # Get base name from input file
                if self.current_image_path:
                    base_name = os.path.splitext(
                        os.path.basename(self.current_image_path)
                    )[0]
                else:
                    base_name = "output"
                
                # Save results
                saved_files = self.processor.save_results(output_dir, base_name)
                
                # Show success message
                QMessageBox.information(
                    self,
                    "Save Complete",
                    f"Saved {len(saved_files)} files to:\n{output_dir}"
                )
                
                self.status_bar.showMessage(f"Saved {len(saved_files)} files")
                
            except Exception as e:
                QMessageBox.critical(self, "Save Error", str(e))
    
    def export_settings(self):
        """Export current settings to file"""
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Settings",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if path:
            try:
                self.config.save(path)
                self.status_bar.showMessage(f"Settings exported to {path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))
    
    def update_dpi(self, value):
        self.config.dpi = value
    
    def update_lpi(self, value):
        self.config.lpi = value
    
    def update_method(self, text):
        mapping = {
            "Ordered Dithering": "ordered",
            "Error Diffusion": "error_diffusion",
            "Hybrid": "hybrid"
        }
        self.config.method = mapping.get(text, "ordered")
    
    def update_matrix_size(self, index):
        sizes = {0: 4, 1: 8, 2: 16}
        self.config.matrix_size = sizes.get(index, 8)
    
    def update_white_method(self, text):
        mapping = {
            "Full": "full",
            "Halftone": "halftone",
            "Edge Enhanced": "edge_enhanced"
        }
        self.config.white_method = mapping.get(text, "edge_enhanced")
    
    def update_threshold(self, value):
        self.config.white_threshold = value / 100.0
    
    def update_zoom(self, text):
        # Remove % sign and convert to float
        zoom_str = text.replace('%', '')
        try:
            zoom = float(zoom_str) / 100.0
            self.preview_widget.zoom_factor = zoom
            self.preview_widget.update()
        except ValueError:
            pass
    
    def update_view_mode(self, text):
        if text == "Original":
            self.preview_widget.show_original = True
        elif text == "Processed":
            self.preview_widget.show_original = False
        elif text == "Side by Side":
            # Implement side by side view
            pass
        self.preview_widget.update()
    
    def update_preview(self):
        """Update preview based on current settings"""
        if self.processed_image is not None:
            self.preview_widget.set_images(self.original_image, self.processed_image)
    
    def zoom_in(self):
        """Zoom in preview"""
        current_text = self.zoom_combo.currentText()
        zoom_levels = ["25%", "50%", "100%", "200%", "400%"]
        
        current_index = zoom_levels.index(current_text)
        if current_index < len(zoom_levels) - 1:
            self.zoom_combo.setCurrentText(zoom_levels[current_index + 1])
    
    def zoom_out(self):
        """Zoom out preview"""
        current_text = self.zoom_combo.currentText()
        zoom_levels = ["25%", "50%", "100%", "200%", "400%"]
        
        current_index = zoom_levels.index(current_text)
        if current_index > 0:
            self.zoom_combo.setCurrentText(zoom_levels[current_index - 1])
    
    def show_channel_settings(self):
        """Show channel settings dialog"""
        QMessageBox.information(
            self,
            "Channel Settings",
            "Individual channel settings dialog will be implemented here."
        )
    
    def show_settings(self):
        """Show settings dialog"""
        QMessageBox.information(
            self,
            "Settings",
            "Application settings dialog will be implemented here."
        )
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About DTF Halftoner Pro",
            "<h2>DTF Halftoner Pro v1.0</h2>"
            "<p>Professional DTF (Direct-to-Film) halftoning software.</p>"
            "<p>Created for Windows desktop.</p>"
            "<p>© 2024 All rights reserved.</p>"
        )
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Clean up resources
        if hasattr(self, 'worker_thread'):
            self.worker_thread.quit()
            self.worker_thread.wait()
        
        event.accept()

class ProcessingWorker(QObject):
    """Worker for processing images in separate thread"""
    
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, processor, image):
        super().__init__()
        self.processor = processor
        self.image = image
    
    def process(self):
        """Process image (runs in separate thread)"""
        try:
            # Process with progress callback
            def progress_callback(step, message):
                self.progress.emit(step, message)
            
            result = self.processor.process(
                self.image,
                progress_callback=progress_callback
            )
            
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(str(e))