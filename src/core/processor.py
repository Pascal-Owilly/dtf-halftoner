# src/core/processor.py
import numpy as np
from PIL import Image
import time
import threading
from queue import Queue
from typing import Dict, List, Optional, Callable
import os

class DTFProcessor:
    """Main processing engine with multi-threading support"""
    
    def __init__(self, config):
        self.config = config
        self.halftone_algorithms = HalftoneAlgorithms()
        self.color_separator = DTFColorSeparator(config)
        
        # Processing state
        self.is_processing = False
        self.current_progress = 0
        self.total_steps = 0
        
        # Results cache
        self.results = {}
        self.original_image = None
        
    def load_image(self, path: str) -> Optional[np.ndarray]:
        """Load image from file with error handling"""
        try:
            img = Image.open(path)
            
            # Convert to RGB if needed
            if img.mode == 'RGBA':
                # Create white background for transparency
                white_bg = Image.new('RGB', img.size, (255, 255, 255))
                white_bg.paste(img, mask=img.split()[3])
                img = white_bg
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            self.original_image = np.array(img)
            return self.original_image
            
        except Exception as e:
            print(f"Error loading image: {e}")
            return None
    
    def process(
        self,
        image: np.ndarray,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, np.ndarray]:
        """
        Main processing pipeline
        Returns dictionary with all channels
        """
        self.is_processing = True
        self.current_progress = 0
        self.total_steps = 8  # Total steps in pipeline
        
        try:
            # Step 1: Color separation
            if progress_callback:
                progress_callback(1, "Separating colors...")
            
            cmyk_array, black_channel = self.color_separator.rgb_to_cmyk(image)
            
            # Step 2: Generate white layer
            if progress_callback:
                progress_callback(2, "Generating white layer...")
            
            white_layer = self.color_separator.generate_white_layer(image)
            
            # Step 3: Apply dot gain compensation
            if progress_callback:
                progress_callback(3, "Applying dot gain compensation...")
            
            channels = {
                'cyan': cmyk_array[:, :, 0],
                'magenta': cmyk_array[:, :, 1],
                'yellow': cmyk_array[:, :, 2],
                'black': black_channel,
                'white': white_layer
            }
            
            # Apply dot gain to each channel
            for name in channels:
                if name != 'white':  # Usually no dot gain on white
                    channels[name] = self.color_separator.apply_dot_gain_compensation(
                        channels[name]
                    )
            
            # Step 4-8: Halftone each channel
            halftoned = {}
            
            # Process channels in parallel (simplified version)
            channel_order = ['cyan', 'magenta', 'yellow', 'black', 'white']
            
            for i, name in enumerate(channel_order):
                step_num = 4 + i
                if progress_callback:
                    progress_callback(step_num, f"Halftoning {name} channel...")
                
                angle = self.config.angles.get(name, 0.0)
                
                if self.config.method == 'ordered':
                    halftoned[name] = self.halftone_algorithms.ordered_dither(
                        channels[name],
                        matrix_size=self.config.matrix_size,
                        angle=angle
                    )
                elif self.config.method == 'error_diffusion':
                    halftoned[name] = self.halftone_algorithms.floyd_steinberg(
                        channels[name]
                    )
                elif self.config.method == 'hybrid':
                    halftoned[name] = self.halftone_algorithms.hybrid_halftone(
                        channels[name]
                    )
                else:
                    # Default to ordered dithering
                    halftoned[name] = self.halftone_algorithms.ordered_dither(
                        channels[name]
                    )
            
            self.results = halftoned
            
            if progress_callback:
                progress_callback(8, "Processing complete!")
            
            return halftoned
            
        except Exception as e:
            print(f"Processing error: {e}")
            raise
        finally:
            self.is_processing = False
    
    def save_results(
        self,
        output_dir: str,
        base_name: str = "output"
    ) -> List[str]:
        """Save all channels as separate TIFF files"""
        if not self.results:
            raise ValueError("No results to save. Process image first.")
        
        saved_files = []
        os.makedirs(output_dir, exist_ok=True)
        
        for name, channel in self.results.items():
            filename = os.path.join(output_dir, f"{base_name}_{name}.tiff")
            
            # Save as TIFF with LZW compression
            img = Image.fromarray(channel)
            img.save(
                filename,
                format='TIFF',
                compression='tiff_lzw',
                dpi=(self.config.dpi, self.config.dpi)
            )
            
            saved_files.append(filename)
        
        # Also save a composite preview
        preview = self.create_preview()
        preview_path = os.path.join(output_dir, f"{base_name}_preview.png")
        Image.fromarray(preview).save(preview_path)
        saved_files.append(preview_path)
        
        return saved_files
    
    def create_preview(self) -> np.ndarray:
        """Create RGB preview from halftoned channels"""
        if not self.results:
            return np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Simple simulation of halftoned print
        h, w = self.results['cyan'].shape
        
        # Convert halftone dots to simulated RGB
        # This is a simplified simulation for preview only
        preview = np.zeros((h, w, 3), dtype=np.float32)
        
        # Combine channels (simplified color mixing)
        for name, channel in self.results.items():
            channel_norm = channel.astype(np.float32) / 255.0
            
            if name == 'cyan':
                preview[:, :, 0] += (1 - channel_norm)  # Less cyan = more red
            elif name == 'magenta':
                preview[:, :, 1] += (1 - channel_norm)  # Less magenta = more green
            elif name == 'yellow':
                preview[:, :, 2] += (1 - channel_norm)  # Less yellow = more blue
            elif name == 'white':
                # White ink makes colors brighter
                brightness_boost = channel_norm * 0.3
                preview += brightness_boost[:, :, np.newaxis]
        
        # Clip and convert to uint8
        preview = np.clip(preview, 0, 1) * 255
        return preview.astype(np.uint8)