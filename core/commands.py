"""
Tile edit command: stores per-tile previous and new pixel buffers to allow undo/redo.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
import numpy as np
from .history import Command
from .canvas import TiledCanvas


@dataclass
class TileEditCommand(Command):
    canvas: TiledCanvas
    edits: List[Tuple[int, int, np.ndarray, np.ndarray]]  # (tx, ty, prev, new)

    def redo(self) -> None:
        for tx, ty, prev, new in self.edits:
            tile = self.canvas.get_tile(tx, ty, create=True)
            tile.data = new.copy()

    def undo(self) -> None:
        for tx, ty, prev, new in self.edits:
            tile = self.canvas.get_tile(tx, ty, create=True)
            tile.data = prev.copy()
