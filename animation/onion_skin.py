"""
Onion skin utilities.
Create overlay images for previous and next frames for display as semi-transparent tinted layers.
"""
from __future__ import annotations
from typing import List, Tuple
from PIL import Image, ImageOps, ImageEnhance
import numpy as np
from export.png_export import render_frame_image


def make_onion_overlays(project, index: int, prev_count: int = 1, next_count: int = 1, opacity: float = 0.4, mode: str = "color") -> List[Tuple[Image.Image, int, int]]:
    """Return list of (PIL.Image RGBA, top_left_x, top_left_y) overlays.

    mode: 'grayscale' or 'color' (color will tint prev red and next blue)
    """
    overlays = []
    w, h = project.width, project.height
    # Previous frames (older)
    for i in range(index - prev_count, index):
        if i < 0 or i >= len(project.frames):
            continue
        img = render_frame_image(project, i)
        if mode == "grayscale":
            img = ImageOps.grayscale(img).convert("RGBA")
        else:
            # tint red
            r, g, b, a = img.split()
            zero = Image.new("L", img.size, 0)
            red_img = Image.merge("RGBA", (r, zero, zero, a))
            img = red_img
        img = ImageEnhance.Brightness(img).enhance(1.0)
        img.putalpha(int(255 * opacity))
        overlays.append((img, 0, 0))
    # Next frames (newer)
    for i in range(index + 1, index + 1 + next_count):
        if i < 0 or i >= len(project.frames):
            continue
        img = render_frame_image(project, i)
        if mode == "grayscale":
            img = ImageOps.grayscale(img).convert("RGBA")
        else:
            # tint blue
            r, g, b, a = img.split()
            zero = Image.new("L", img.size, 0)
            blue_img = Image.merge("RGBA", (zero, zero, b, a))
            img = blue_img
        img.putalpha(int(255 * opacity))
        overlays.append((img, 0, 0))
    return overlays
