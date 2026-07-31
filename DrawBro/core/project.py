from dataclasses import dataclass, field

@dataclass
class Project:
    name:str="Untitled"
    width:int=1024
    height:int=1024
    fps:int=12
    current_frame:int=0
