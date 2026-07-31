from PySide6.QtGui import QImage
from PySide6.QtCore import Qt

TILE_SIZE=1024

class Tile:
    def __init__(self):
        self.image=QImage(TILE_SIZE,TILE_SIZE,QImage.Format_ARGB32)
        self.image.fill(Qt.transparent)

class TileMap:
    def __init__(self):
        self.tiles={}
    def get(self,x,y):
        if (x,y) not in self.tiles:
            self.tiles[(x,y)]=Tile()
        return self.tiles[(x,y)]
