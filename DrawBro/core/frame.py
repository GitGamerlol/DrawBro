from .layer import Layer

class Frame:
    def __init__(self,w=1024,h=1024):
        self.layers=[Layer("Layer 1",w,h)]
