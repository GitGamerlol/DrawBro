"""
PNG export utilities and helpers for rendering frames to PIL Image.
"""
from __future__ import annotations
from PIL import Image
import numpy as np
from core.project import Project


def render_frame_image(project: Project, frame_index: int) -> Image.Image:
    frame = project.frames[frame_index]
    w, h = project.width, project.height
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for layer in frame.layers:
        if not layer.visible:
            continue
        layer_img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        for tile in layer.canvas.iter_tiles_in_rect(0, 0, w, h):
            if tile.data is None:
                continue
            tx, ty = tile.coord
            tile_x = tx * layer.canvas.tile_size
            tile_y = ty * layer.canvas.tile_size
            h_t, w_t, _ = tile.data.shape
            arr = tile.data
            img = Image.frombytes("RGBA", (w_t, h_t), arr.tobytes())
            layer_img.paste(img, (tile_x, tile_y), img)
        # apply layer opacity
        if layer.opacity < 1.0:
            alpha = layer_img.split()[-1]
            alpha = alpha.point(lambda p: int(p * layer.opacity))
            layer_img.putalpha(alpha)
        out = Image.alpha_composite(out, layer_img)
    return out
