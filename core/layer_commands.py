"""
Layer-related commands for undo/redo operations.
Each command implements redo() and undo() and is intended to be used with HistoryManager.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from core.frame import Frame
from core.layer import Layer


class Command:
    def redo(self) -> None:
        raise NotImplementedError

    def undo(self) -> None:
        raise NotImplementedError


@dataclass
class AddLayerCommand(Command):
    frame: Frame
    index: Optional[int] = None
    layer: Optional[Layer] = None

    def redo(self) -> None:
        if self.layer is None:
            self.layer = Layer()
        if self.index is None:
            self.frame.layers.append(self.layer)
            self.index = len(self.frame.layers) - 1
        else:
            self.frame.layers.insert(self.index, self.layer)

    def undo(self) -> None:
        if self.index is None:
            return
        self.frame.layers.pop(self.index)


@dataclass
class RemoveLayerCommand(Command):
    frame: Frame
    index: int
    _backup: Optional[Layer] = None

    def redo(self) -> None:
        self._backup = self.frame.layers.pop(self.index)

    def undo(self) -> None:
        if self._backup is not None:
            self.frame.layers.insert(self.index, self._backup)


@dataclass
class RenameLayerCommand(Command):
    frame: Frame
    index: int
    new_name: str
    _old_name: Optional[str] = None

    def redo(self) -> None:
        layer = self.frame.layers[self.index]
        self._old_name = layer.name
        layer.name = self.new_name

    def undo(self) -> None:
        layer = self.frame.layers[self.index]
        if self._old_name is not None:
            layer.name = self._old_name


@dataclass
class MoveLayerCommand(Command):
    frame: Frame
    src_index: int
    dst_index: int

    def redo(self) -> None:
        layer = self.frame.layers.pop(self.src_index)
        self.frame.layers.insert(self.dst_index, layer)

    def undo(self) -> None:
        # move back
        cur_index = self.dst_index
        layer = self.frame.layers.pop(cur_index)
        self.frame.layers.insert(self.src_index, layer)


@dataclass
class DuplicateLayerCommand(Command):
    frame: Frame
    index: int
    _dup_index: Optional[int] = None

    def redo(self) -> None:
        src = self.frame.layers[self.index]
        dup = src.duplicate()
        self.frame.layers.insert(self.index + 1, dup)
        self._dup_index = self.index + 1

    def undo(self) -> None:
        if self._dup_index is not None:
            self.frame.layers.pop(self._dup_index)


@dataclass
class ChangeLayerOpacityCommand(Command):
    frame: Frame
    index: int
    new_opacity: float
    _old_opacity: Optional[float] = None

    def redo(self) -> None:
        layer = self.frame.layers[self.index]
        self._old_opacity = layer.opacity
        layer.opacity = self.new_opacity

    def undo(self) -> None:
        layer = self.frame.layers[self.index]
        if self._old_opacity is not None:
            layer.opacity = self._old_opacity


@dataclass
class ToggleVisibilityCommand(Command):
    frame: Frame
    index: int
    _old: Optional[bool] = None

    def redo(self) -> None:
        layer = self.frame.layers[self.index]
        self._old = layer.visible
        layer.visible = not layer.visible

    def undo(self) -> None:
        layer = self.frame.layers[self.index]
        if self._old is not None:
            layer.visible = self._old


@dataclass
class ToggleLockCommand(Command):
    frame: Frame
    index: int
    _old: Optional[bool] = None

    def redo(self) -> None:
        layer = self.frame.layers[self.index]
        self._old = layer.locked
        layer.locked = not layer.locked

    def undo(self) -> None:
        layer = self.frame.layers[self.index]
        if self._old is not None:
            layer.locked = self._old
