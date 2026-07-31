"""
Viewport transforms: map between world (canvas) and screen coordinates,
supporting pan, zoom, and rotation (degrees).

This module contains a small stateful object used by the UI to drive view transforms.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Tuple


@dataclass
class Viewport:
    pan_x: float = 0.0  # world x coordinate at screen origin (or offset)
    pan_y: float = 0.0
    zoom: float = 1.0  # scale factor (1.0 = 100%)
    rotation_deg: float = 0.0  # clockwise degrees

    def world_to_screen(self, wx: float, wy: float) -> Tuple[float, float]:
        """Map world coordinates to screen coordinates (ignores device pixel ratio)."""
        # Apply zoom
        sx = (wx - self.pan_x) * self.zoom
        sy = (wy - self.pan_y) * self.zoom
        # Apply rotation around origin
        if self.rotation_deg != 0.0:
            theta = math.radians(self.rotation_deg)
            cos_t = math.cos(theta)
            sin_t = math.sin(theta)
            rx = sx * cos_t - sy * sin_t
            ry = sx * sin_t + sy * cos_t
            return rx, ry
        return sx, sy

    def screen_to_world(self, sx: float, sy: float) -> Tuple[float, float]:
        """Inverse of world_to_screen."""
        if self.rotation_deg != 0.0:
            theta = -math.radians(self.rotation_deg)
            cos_t = math.cos(theta)
            sin_t = math.sin(theta)
            rx = sx * cos_t - sy * sin_t
            ry = sx * sin_t + sy * cos_t
        else:
            rx, ry = sx, sy
        wx = rx / self.zoom + self.pan_x
        wy = ry / self.zoom + self.pan_y
        return wx, wy

    def zoom_at(self, factor: float, screen_x: float, screen_y: float) -> None:
        """
        Zoom while keeping the world point under (screen_x, screen_y) stationary.
        """
        before = self.screen_to_world(screen_x, screen_y)
        self.zoom *= factor
        after = self.screen_to_world(screen_x, screen_y)
        # Adjust pan so that before == after
        self.pan_x += before[0] - after[0]
        self.pan_y += before[1] - after[1]
