# DrawBro

DrawBro is a production-quality desktop painting application prototype focusing on a tiled infinite canvas, layers, animation, and modern UI using PySide6.

This repository is organized into packages:
- core/ : fundamental data model (canvas, tiles, layers, frames, history, viewport)
- tools/: tool implementations (pen, eraser, shape tools...) — planned
- ui/: Qt-based UI (main window, panels, widgets)
- animation/: timeline, onion skin, playback — planned
- export/: PNG/GIF/spritesheet exporters — planned
- reference/: reference-image system (OpenCV perspective warp) — planned

Goals and design principles:
- Infinite tiled canvas (tiles allocated on demand, default tile size 1024)
- Layer/frame model with animation support
- Command-based undo/redo
- Modular, testable code with type hints and documentation

Getting started (development):
1. Create and activate a virtualenv (Python 3.12+).
2. pip install -r requirements.txt
3. python main.py

Planned next steps:
- Implement CanvasWidget (Qt) and hook viewport transforms
- Implement core drawing tools (Pen/Eraser) and basic brush shapes
- Implement layer panel, timeline widget, and onion skin rendering
- Add reference image system using OpenCV

Contributions and roadmap are welcome — open an issue or PR describing the area you'd like to work on.
