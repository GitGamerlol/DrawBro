"""
Timeline and playback UI widget.
Provides frame list controls, playback, FPS control, loop and ping-pong options, and onion-skin toggles.
Emits signals when frames change and during playback.
"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QSpinBox, QListWidget, QVBoxLayout, QCheckBox
from PySide6.QtCore import Qt, QTimer, Signal
from typing import Optional


class TimelineWidget(QWidget):
    frameChanged = Signal(int)
    playToggled = Signal(bool)

    def __init__(self, project=None, parent=None) -> None:
        super().__init__(parent)
        self.project = project
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        self.playing = False
        self.loop = True
        self.pingpong = False
        self._pingpong_dir = 1

        layout = QVBoxLayout()
        controls = QHBoxLayout()
        self.play_btn = QPushButton("Play")
        self.stop_btn = QPushButton("Stop")
        self.fps_label = QLabel("FPS:")
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 60)
        self.fps_spin.setValue(12)
        self.loop_check = QCheckBox("Loop")
        self.pingpong_check = QCheckBox("PingPong")
        self.onion_check = QCheckBox("Onion Skin")
        self.onion_check.setChecked(False)
        controls.addWidget(self.play_btn)
        controls.addWidget(self.stop_btn)
        controls.addWidget(self.fps_label)
        controls.addWidget(self.fps_spin)
        controls.addWidget(self.loop_check)
        controls.addWidget(self.pingpong_check)
        controls.addWidget(self.onion_check)

        self.frame_list = QListWidget()
        frame_controls = QHBoxLayout()
        self.add_btn = QPushButton("Add Frame")
        self.dup_btn = QPushButton("Duplicate")
        self.remove_btn = QPushButton("Remove")
        frame_controls.addWidget(self.add_btn)
        frame_controls.addWidget(self.dup_btn)
        frame_controls.addWidget(self.remove_btn)

        layout.addLayout(controls)
        layout.addWidget(self.frame_list)
        layout.addLayout(frame_controls)
        self.setLayout(layout)

        # Connect
        self.play_btn.clicked.connect(self._on_play)
        self.stop_btn.clicked.connect(self._on_stop)
        self.fps_spin.valueChanged.connect(self._on_fps_changed)
        self.add_btn.clicked.connect(self._on_add_frame)
        self.dup_btn.clicked.connect(self._on_dup_frame)
        self.remove_btn.clicked.connect(self._on_remove_frame)
        self.frame_list.currentRowChanged.connect(self._on_frame_selected)
        self.loop_check.toggled.connect(self._on_loop_toggled)
        self.pingpong_check.toggled.connect(self._on_pingpong_toggled)
        self.onion_check.toggled.connect(self._on_onion_toggled)

        self._update_ui()

    def set_project(self, project) -> None:
        self.project = project
        self._rebuild_frame_list()

    def _rebuild_frame_list(self) -> None:
        self.frame_list.clear()
        if self.project is None:
            return
        for i, _ in enumerate(self.project.frames):
            self.frame_list.addItem(f"Frame {i}")
        self.frame_list.setCurrentRow(self.project.current_frame)

    def _update_ui(self) -> None:
        self.loop_check.setChecked(self.loop)
        self.pingpong_check.setChecked(self.pingpong)

    def _on_play(self) -> None:
        if self.project is None:
            return
        fps = self.fps_spin.value()
        interval = int(1000 / max(1, fps))
        self.timer.start(interval)
        self.playing = True
        self.playToggled.emit(True)

    def _on_stop(self) -> None:
        self.timer.stop()
        self.playing = False
        self._pingpong_dir = 1
        self.playToggled.emit(False)

    def _on_tick(self) -> None:
        if self.project is None or not self.project.frames:
            return
        idx = self.project.current_frame
        n = len(self.project.frames)
        if self.pingpong:
            # move in direction
            next_idx = idx + self._pingpong_dir
            if next_idx >= n or next_idx < 0:
                self._pingpong_dir *= -1
                next_idx = idx + self._pingpong_dir
            self.project.current_frame = next_idx
        else:
            next_idx = (idx + 1) % n
            if next_idx == 0 and not self.loop:
                self._on_stop()
                return
            self.project.current_frame = next_idx
        self.frame_list.setCurrentRow(self.project.current_frame)
        self.frameChanged.emit(self.project.current_frame)

    def _on_fps_changed(self, v: int) -> None:
        if self.timer.isActive():
            self._on_play()

    def _on_add_frame(self) -> None:
        if self.project is None:
            return
        self.project.add_frame()
        self._rebuild_frame_list()
        self.frameChanged.emit(self.project.current_frame)

    def _on_dup_frame(self) -> None:
        if self.project is None:
            return
        idx = self.frame_list.currentRow()
        if idx < 0:
            idx = self.project.current_frame
        self.project.duplicate_frame(idx)
        self._rebuild_frame_list()
        self.frameChanged.emit(self.project.current_frame)

    def _on_remove_frame(self) -> None:
        if self.project is None or len(self.project.frames) <= 1:
            return
        idx = self.frame_list.currentRow()
        if idx < 0:
            return
        self.project.remove_frame(idx)
        self._rebuild_frame_list()
        self.frameChanged.emit(self.project.current_frame)

    def _on_frame_selected(self, row: int) -> None:
        if self.project is None or row < 0:
            return
        self.project.set_current_frame(row)
        self.frameChanged.emit(row)

    def _on_loop_toggled(self, checked: bool) -> None:
        self.loop = checked

    def _on_pingpong_toggled(self, checked: bool) -> None:
        self.pingpong = checked

    def _on_onion_toggled(self, checked: bool) -> None:
        # toggle handled by CanvasWidget via project metadata or direct signal in future
        pass
