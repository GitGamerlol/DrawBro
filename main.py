#!/usr/bin/env python3
"""
DrawBro - entrypoint
"""
from PySide6.QtWidgets import QApplication
import sys

from ui.main_window import MainWindow


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv
    app = QApplication(argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
