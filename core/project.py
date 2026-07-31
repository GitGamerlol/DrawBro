"""
Project container: manages frames, sprite settings, document metadata, and export options.
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

    def add_frame(self, index: int | None = None, frame: Frame | None = None) -> int:
        f = frame or Frame()
        if index is None:
            self.frames.append(f)
            return len(self.frames) - 1
        else:
            self.frames.insert(index, f)
            return index

    def remove_frame(self, index: int) -> Frame:
        return self.frames.pop(index)

    def duplicate_frame(self, index: int) -> int:
        src = self.frames[index]
        # naive deep copy (layers will duplicate their canvas)
        import copy
        dup = copy.deepcopy(src)
        self.frames.insert(index + 1, dup)
        return index + 1
