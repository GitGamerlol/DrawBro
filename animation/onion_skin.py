"""
Onion skin utilities: produce composited overlay images for previous/next frames.
"""
from __future__ import annotations
import numpy as np
from core.frame import Frame


def compose_onion(frames: list[Frame], index: int, prev_count: int = 1, next_count: int = 1, opacity: float = 0.5):
    # return a list of (offset_index, numpy_rgba_array)
    results = []
    # For simplicity, assume frames share a coordinate grid and tile size and that we can composite full images.
    # Producing full images is memory-heavy but acceptable for the initial implementation.
    for i in range(index - prev_count, index):
        if i < 0 or i >= len(frames):
            continue
        # naive composition: produce a full image by iterating tiles (not implemented fully here)
        results.append((i, None))
    for i in range(index + 1, index + 1 + next_count):
        if i < 0 or i >= len(frames):
            continue
        results.append((i, None))
    return results
