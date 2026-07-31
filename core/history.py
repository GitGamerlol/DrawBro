"""
Command-based history manager skeleton.

Commands should implement .undo() and .redo().
HistoryManager tracks stacks and memory limit. The commands themselves
are responsible for efficient state deltas (not snapshotting full images).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, List, Optional


class Command(Protocol):
    def redo(self) -> None:
        ...

    def undo(self) -> None:
        ...


@dataclass
class HistoryManager:
    undo_stack: List[Command] = None
    redo_stack: List[Command] = None
    memory_limit_bytes: int | None = None  # optional bound (not enforced yet)

    def __post_init__(self) -> None:
        self.undo_stack = [] if self.undo_stack is None else self.undo_stack
        self.redo_stack = [] if self.redo_stack is None else self.redo_stack

    def push(self, cmd: Command) -> None:
        cmd.redo()
        self.undo_stack.append(cmd)
        self.redo_stack.clear()
        # TODO: enforce memory limit if needed

    def undo(self) -> None:
        if not self.undo_stack:
            return
        cmd = self.undo_stack.pop()
        cmd.undo()
        self.redo_stack.append(cmd)

    def redo(self) -> None:
        if not self.redo_stack:
            return
        cmd = self.redo_stack.pop()
        cmd.redo()
        self.undo_stack.append(cmd)
