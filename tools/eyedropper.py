from __future__ import annotations

from typing import Tuple
from core.canvas import TiledCanvas


class EyedropperTool:
    """Eyedropper: sample topmost visible pixel at a world coordinate from a Project/Frame.

    Usage: color = tool.pick(x, y, project)
    Returns (r,g,b,a) tuple ints 0..255 or None if transparent.
    """

    def pick(self, x: float, y: float, project) -> tuple[int, int, int, int] | None:
        # Search top-down layers in the active frame
        if not project.frames:
            return None
        frame = project.frames[0]
        wx = int(round(x))
        wy = int(round(y))
        for layer in reversed(frame.layers):
            if not layer.visible:
                continue
            try:
                px = layer.canvas.get_pixel(wx, wy)
            except Exception:
                px = (0, 0, 0, 0)
            if px[3] != 0:
                return px
        return (0, 0, 0, 0)
