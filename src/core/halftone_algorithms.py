# src/core/halftone_algorithms.py
import numpy as np
from numba import jit
from typing import Tuple, Optional

class HalftoneAlgorithms:
    """Collection of halftoning algorithms optimized for performance"""
    
    @staticmethod
    @jit(nopython=True, parallel=True)
    def bayer_matrix(size: int) -> np.ndarray:
        """Generate Bayer ordered dithering matrix"""
        if size == 2:
            return np.array([[0, 2],
                            [3, 1]], dtype=np.float32) / 4.0
        
        # Recursive generation for larger matrices
        n = 2
        matrix = np.array([[0, 2],
                          [3, 1]], dtype=np.float32)
        
        while n < size:
            n *= 2
            new_matrix = np.zeros((n, n), dtype=np.float32)
            
            for i in range(2):
                for j in range(2):
                    quadrant = matrix + (i * 2 + j) * (n * n // 4)
                    new_matrix[i*n//2:(i+1)*n//2, j*n//2:(j+1)*n//2] = quadrant
            
            matrix = new_matrix
        
        return matrix / (size * size)
    
    @staticmethod
    def ordered_dither(
        channel: np.ndarray,
        matrix_size: int = 8,
        angle: float = 45.0
    ) -> np.ndarray:
        """
        Apply ordered dithering with rotation
        Optimized for large images
        """
        h, w = channel.shape
        
        # Generate threshold matrix
        threshold_matrix = HalftoneAlgorithms.bayer_matrix(matrix_size)
        tm_h, tm_w = threshold_matrix.shape
        
        # Normalize input to 0-1
        normalized = channel.astype(np.float32) / 255.0
        
        # Tile threshold matrix
        tiles_h = (h + tm_h - 1) // tm_h
        tiles_w = (w + tm_w - 1) // tm_w
        
        tiled_matrix = np.tile(threshold_matrix, (tiles_h, tiles_w))
        tiled_matrix = tiled_matrix[:h, :w]
        
        # Apply threshold
        result = (normalized > tiled_matrix).astype(np.float32)
        
        # Rotate if angle != 0
        if angle != 0:
            from scipy import ndimage
            result = ndimage.rotate(result, angle, reshape=False, order=1)
        
        return (result * 255).astype(np.uint8)
    
    @staticmethod
    @jit(nopython=True)
    def floyd_steinberg(channel: np.ndarray) -> np.ndarray:
        """Floyd-Steinberg error diffusion dithering"""
        h, w = channel.shape
        output = channel.copy().astype(np.float32)
        
        for y in range(h):
            for x in range(w):
                old_pixel = output[y, x]
                new_pixel = 255.0 if old_pixel > 127.5 else 0.0
                output[y, x] = new_pixel
                error = old_pixel - new_pixel
                
                # Diffuse error to neighbors
                if x + 1 < w:
                    output[y, x + 1] += error * 7.0 / 16.0
                if y + 1 < h:
                    if x > 0:
                        output[y + 1, x - 1] += error * 3.0 / 16.0
                    output[y + 1, x] += error * 5.0 / 16.0
                    if x + 1 < w:
                        output[y + 1, x + 1] += error * 1.0 / 16.0
        
        return np.clip(output, 0, 255).astype(np.uint8)
    
    @staticmethod
    def hybrid_halftone(
        channel: np.ndarray,
        highlight_threshold: float = 0.2,
        shadow_threshold: float = 0.8
    ) -> np.ndarray:
        """Hybrid AM/FM halftoning - AM for midtones, FM for highlights/shadows"""
        normalized = channel.astype(np.float32) / 255.0
        
        # Create masks for different tonal ranges
        highlight_mask = normalized < highlight_threshold
        shadow_mask = normalized > shadow_threshold
        midtone_mask = ~(highlight_mask | shadow_mask)
        
        # Initialize output
        output = np.zeros_like(channel, dtype=np.uint8)
        
        # FM for highlights and shadows
        if np.any(highlight_mask | shadow_mask):
            fm_result = HalftoneAlgorithms.floyd_steinberg(channel)
            output[highlight_mask | shadow_mask] = fm_result[highlight_mask | shadow_mask]
        
        # AM for midtones
        if np.any(midtone_mask):
            am_result = HalftoneAlgorithms.ordered_dither(
                channel[midtone_mask].reshape(-1, 1),
                matrix_size=8
            )
            output[midtone_mask] = am_result.flatten()
        
        return output