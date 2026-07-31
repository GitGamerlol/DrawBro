"""
Frame model. A frame contains an ordered list of layers.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
from .layer import Layer


@dataclass
class Frame:
    layers: List[Layer] = field(default_factory=list)
    name: str = "Frame"

    def add_layer(self, layer: Layer | None = None, index: int | None = None) -> Layer:
        l = layer or Layer()
        if index is None:
            self.layers.append(l)
        else:
            self.layers.insert(index, l)
        return l

    def remove_layer(self, index: int) -> Layer:
        return self.layers.pop(index)

    def duplicate_layer(self, index: int) -> int:
        src = self.layers[index]
        dup = src.duplicate()
        self.layers.insert(index + 1, dup)
        return index + 1

    def reorder_layer(self, src_index: int, dst_index: int) -> None:
        layer = self.layers.pop(src_index)
        self.layers.insert(dst_index, layer)
