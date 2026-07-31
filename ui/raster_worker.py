from __future__ import annotations

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage
import numpy as np


class RasterWorker(QThread):
    finished = Signal(QImage)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._task = None

    def set_task(self, task_callable):
        self._task = task_callable

    def run(self) -> None:
        if self._task is None:
            return
        # task_callable should return a QImage
        try:
            img = self._task()
            if isinstance(img, QImage):
                self.finished.emit(img)
        except Exception:
            pass
