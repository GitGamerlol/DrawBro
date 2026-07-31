"""
Project container: manages frames, sprite settings, document metadata, and export options.

Added current_frame index and frame management helpers.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from .frame import Frame


@dataclass
class Project:
    name: str = "Untitled"
    frames: List[Frame] = field(default_factory=lambda: [Frame()])
    width: int = 1024
    height: int = 1024
    fps: float = 12.0
    background_color: tuple[int, int, int, int] = (0, 0, 0, 0)
    # sprite mode: when enabled all frames share same size
    sprite_mode: bool = True
    metadata: dict = field(default_factory=dict)

    # current active frame index
    current_frame: int = 0

    def add_frame(self, index: int | None = None, frame: Frame | None = None) -> int:
        f = frame or Frame()
        if index is None:
            self.frames.append(f)
            idx = len(self.frames) - 1
            self.current_frame = idx
            return idx
        else:
            self.frames.insert(index, f)
            self.current_frame = index
            return index

    def remove_frame(self, index: int) -> Frame:
        if index < 0 or index >= len(self.frames):
            raise IndexError("frame index out of range")
        removed = self.frames.pop(index)
        # adjust current_frame
        if self.current_frame >= len(self.frames):
            self.current_frame = max(0, len(self.frames) - 1)
        return removed

    def duplicate_frame(self, index: int) -> int:
        src = self.frames[index]
        # naive deep copy (layers will duplicate their canvas)
        import copy
        dup = copy.deepcopy(src)
        self.frames.insert(index + 1, dup)
        self.current_frame = index + 1
        return index + 1

    def set_current_frame(self, index: int) -> None:
        if index < 0 or index >= len(self.frames):
            raise IndexError("frame index out of range")
        self.current_frame = index
