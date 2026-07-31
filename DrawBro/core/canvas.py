from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter,QPen,QColor
from PySide6.QtCore import Qt,QPoint
from .frame import Frame
from ..reference.background import BackgroundImage

class Canvas(QWidget):
    def __init__(self):
        super().__init__()
        self.frame=Frame(4096,4096)
        self.bg=BackgroundImage()
        self.last=None
        self.brush=QPen(QColor("black"),4,Qt.SolidLine,Qt.RoundCap)
    def paintEvent(self,e):
        p=QPainter(self)
        self.bg.draw(p)
        for layer in self.frame.layers:
            if layer.visible:
                p.setOpacity(layer.opacity)
                p.drawImage(0,0,layer.image)
    def mousePressEvent(self,e):
        self.last=e.position().toPoint()
    def mouseMoveEvent(self,e):
        if not (e.buttons()&Qt.LeftButton): return
        cur=e.position().toPoint()
        img=self.frame.layers[0].image
        p=QPainter(img)
        p.setPen(self.brush)
        p.drawLine(self.last,cur)
        p.end()
        self.last=cur
        self.update()
