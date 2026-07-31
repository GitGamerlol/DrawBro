"""
Layer model.

Each layer contains its own TiledCanvas (so layers are composited on render).
Layer metadata: name, opacity, visibility, lock, blend mode (future).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from .canvas import TiledCanvas


@dataclass
class Layer:
    name: str = "Layer"
    opacity: float = 1.0  # 0.0 - 1.0
    visible: bool = True
    locked: bool = False
    canvas: TiledCanvas = field(default_factory=TiledCanvas)
    metadata: dict = field(default_factory=dict)

    def duplicate(self) -> "Layer":
        # Note: shallow copy of tiles for now; deep-copy implemented later for copy-on-write.
        new_layer = Layer(
            name=f"{self.name} copy",
            opacity=self.opacity,
            visible=self.visible,
            locked=self.locked,
            canvas=TiledCanvas(tile_size=self.canvas.tile_size),
            metadata=self.metadata.copy(),
        )
        # Copy tile pixel data
        for tile in self.canvas.iter_tiles():
            t = new_layer.canvas.get_tile(tile.coord[0], tile.coord[1], create=True)
            if tile.data is not None:
                t.data = tile.data.copy()
        return new_layer
