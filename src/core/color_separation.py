# src/core/color_separation.py
import numpy as np
from typing import Tuple, Dict
import colorsys

class DTFColorSeparator:
    """DTF-specific color separation with white layer generation"""
    
    def __init__(self, config):
        self.config = config
    
    def rgb_to_cmyk(self, rgb: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert RGB to CMYK with proper black generation
        Returns: (cmyk_array, black_channel)
        """
        # Normalize RGB
        rgb_norm = rgb.astype(np.float32) / 255.0
        
        # Calculate CMY
        c = 1.0 - rgb_norm[:, :, 0]
        m = 1.0 - rgb_norm[:, :, 1]
        y = 1.0 - rgb_norm[:, :, 2]
        
        # Black generation
        if self.config.black_generation == "GCR":
            # Gray Component Replacement
            k = np.minimum(np.minimum(c, m), y) * 0.8
            k = np.clip(k, 0, 1)
            
            # Adjust CMY
            c = (c - k) / (1.0 - k + 1e-10)
            m = (m - k) / (1.0 - k + 1e-10)
            y = (y - k) / (1.0 - k + 1e-10)
        else:
            # Under Color Removal
            k = np.minimum(np.minimum(c, m), y)
            c = c - k
            m = m - k
            y = y - k
        
        # Apply total ink limit
        total_ink = c + m + y + k
        mask = total_ink > (self.config.total_ink_limit / 100.0)
        
        if np.any(mask):
            scale = (self.config.total_ink_limit / 100.0) / total_ink[mask]
            c[mask] *= scale
            m[mask] *= scale
            y[mask] *= scale
            k[mask] *= scale
        
        # Stack and convert to 0-255
        cmyk = np.stack([c, m, y, k], axis=-1)
        cmyk = np.clip(cmyk, 0, 1) * 255
        
        return cmyk.astype(np.uint8), (k * 255).astype(np.uint8)
    
    def generate_white_layer(
        self,
        rgb: np.ndarray,
        method: str = None
    ) -> np.ndarray:
        """Generate white ink layer using specified method"""
        if method is None:
            method = self.config.white_method
        
        h, w, _ = rgb.shape
        
        if method == "full":
            # Full coverage under all colored areas
            gray = np.mean(rgb, axis=2)
            white = (gray < 250) * 255  # Almost white areas don't need white ink
        
        elif method == "halftone":
            # Halftoned white layer to save ink
            gray = np.mean(rgb, axis=2)
            # Areas that need some white
            white_needed = (gray < 220)
            # Create density map
            density = 1.0 - (gray / 255.0)
            density = np.clip(density, 0, 1)
            # Apply threshold
            white = (density > 0.3) * 255
        
        elif method == "edge_enhanced":
            # Enhanced edges for better definition
            import cv2
            
            # Convert to grayscale
            gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
            
            # Detect edges
            edges = cv2.Canny(gray, 50, 150)
            edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
            
            # Base white mask
            brightness = np.mean(rgb, axis=2)
            base_white = (brightness < 220)
            
            # Combine with edges
            white_mask = base_white | (edges > 0)
            white = white_mask * 255
        
        elif method == "transparency_based":
            # For images with alpha channel
            if rgb.shape[2] == 4:
                alpha = rgb[:, :, 3]
                # White under semi-transparent areas
                white = (alpha < 250) * 255
            else:
                white = np.ones((h, w), dtype=np.uint8) * 255
        
        else:
            # Custom method
            white = np.ones((h, w), dtype=np.uint8) * 255
        
        return white.astype(np.uint8)
    
    def apply_dot_gain_compensation(
        self,
        channel: np.ndarray,
        dot_gain: float = None
    ) -> np.ndarray:
        """Apply dot gain compensation curve"""
        if dot_gain is None:
            dot_gain = self.config.dot_gain
        
        # Create compensation LUT
        x = np.linspace(0, 1, 256)
        # Inverse dot gain curve
        y = 1 - (1 - x) ** (1 / (1 + dot_gain))
        lut = (y * 255).astype(np.uint8)
        
        # Apply LUT
        return lut[channel]