from PySide6.QtGui import QImage
from PySide6.QtCore import Qt

class Layer:
    def __init__(self,name="Layer",w=1024,h=1024):
        self.name=name
        self.visible=True
        self.locked=False
        self.opacity=1.0
        self.image=QImage(w,h,QImage.Format_ARGB32)
        self.image.fill(Qt.transparent)
