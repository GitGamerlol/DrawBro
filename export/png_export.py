"""
PNG export utilities.
"""
from __future__ import annotations
from PIL import Image
import numpy as np
from core.project import Project


def export_frame_to_png(project: Project, frame_index: int, path: str) -> None:
    frame = project.frames[frame_index]
    w, h = project.width, project.height
    # create transparent background
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # naive compositing: iterate layers and paste their full images
    # For now, assume layer canvases are sparse and smaller than project size.
    # Build each layer into a full image by iterating tiles
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
        out = Image.alpha_composite(out, layer_img)
    out.save(path)
