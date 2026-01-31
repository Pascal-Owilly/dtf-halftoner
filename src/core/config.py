# src/core/config.py
import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, Any

@dataclass
class DTFConfig:
    """Configuration for DTF halftoning"""
    # General
    dpi: int = 600
    lpi: int = 55
    output_format: str = "tiff"
    
    # Channel angles (to avoid moiré patterns)
    angles: Dict[str, float] = None
    
    # Halftone method
    method: str = "ordered"  # "ordered", "error_diffusion", "hybrid"
    matrix_size: int = 8  # For ordered dithering
    
    # White layer
    white_method: str = "edge_enhanced"  # "full", "halftone", "edge_enhanced", "custom"
    white_threshold: float = 0.75
    
    # Color separation
    black_generation: str = "GCR"  # "GCR", "UCR"
    total_ink_limit: float = 280.0  # Percent
    dot_gain: float = 0.12
    
    # Output
    save_separate_channels: bool = True
    compression: str = "LZW"
    
    def __post_init__(self):
        if self.angles is None:
            self.angles = {
                "cyan": 15.0,
                "magenta": 75.0,
                "yellow": 0.0,
                "black": 45.0,
                "white": 30.0
            }
    
    def save(self, path: str):
        """Save configuration to JSON file"""
        with open(path, 'w') as f:
            json.dump(asdict(self), f, indent=4)
    
    @classmethod
    def load(cls, path: str):
        """Load configuration from JSON file"""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(**data)
    
    @classmethod
    def get_default_presets(cls):
        """Return default preset configurations"""
        return {
            "Epson_Standard": cls(
                dpi=600,
                lpi=55,
                white_method="edge_enhanced",
                dot_gain=0.15
            ),
            "High_Detail": cls(
                dpi=600,
                lpi=65,
                white_method="full",
                dot_gain=0.10
            ),
            "Fast_Production": cls(
                dpi=300,
                lpi=45,
                white_method="halftone",
                dot_gain=0.20
            )
        }