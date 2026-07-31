"""
Reference image utilities and perspective correction helpers.

ReferenceImage encapsulates a loaded image and user-specified destination corners in world
coordinates. It provides a method to produce a warped RGBA numpy array suitable for drawing
on the CanvasWidget. OpenCV is used for perspective transforms.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Tuple, List
import numpy as np
import cv2
from PIL import Image


@dataclass
class ReferenceImage:
    path: Optional[str] = None
    # original image as numpy RGBA (H,W,4) uint8
    src_rgba: Optional[np.ndarray] = None
    # corners in world coordinates: list of four (x,y) points in order: TL,TR,BR,BL
    corners: Optional[List[Tuple[float, float]]] = None
    opacity: float = 0.75
    visible: bool = True
    locked: bool = False
    transform_matrix: Optional[np.ndarray] = None

    @classmethod
    def load_from_file(cls, path: str) -> "ReferenceImage":
        img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        if img is None:
            raise IOError(f"Could not load image: {path}")
        # Ensure we have 4 channels RGBA
        if img.ndim == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
        elif img.shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        # Convert BGRA to RGBA
        img = img[..., [2, 1, 0, 3]]
        return cls(path=path, src_rgba=img)

    def set_corners(self, corners: List[Tuple[float, float]]) -> None:
        if len(corners) != 4:
            raise ValueError("Expected 4 corner points")
        self.corners = corners
        self._update_transform()

    def _update_transform(self) -> None:
        if self.src_rgba is None or self.corners is None:
            self.transform_matrix = None
            return
        h, w, _ = self.src_rgba.shape
        src_pts = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype=np.float32)
        dst_pts = np.array(self.corners, dtype=np.float32)
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        self.transform_matrix = M

    def get_warped_rgba(self, canvas_width: int, canvas_height: int) -> Optional[np.ndarray]:
        """Return a full-canvas RGBA uint8 numpy array with the reference image warped into place.

        This places the warped image onto a transparent canvas the size of the project canvas so
        callers can alpha-composite it easily.
        """
        if self.src_rgba is None or self.transform_matrix is None or not self.visible:
            return None
        # Warp source into destination canvas size
        h_src, w_src, _ = self.src_rgba.shape
        # transform expects input in width x height destination
        canvas_size = (canvas_width, canvas_height)
        # OpenCV expects BGRA, so convert back
        src_bgra = self.src_rgba[..., [2, 1, 0, 3]]
        warped = cv2.warpPerspective(src_bgra, self.transform_matrix, canvas_size, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
        # Convert BGRA to RGBA
        warped = warped[..., [2, 1, 0, 3]]
        # Apply opacity by scaling alpha channel
        alpha = warped[..., 3].astype(np.float32) * float(self.opacity)
        warped[..., 3] = np.clip(alpha, 0, 255).astype(np.uint8)
        return warped

    def get_pil_preview(self) -> Optional[Image.Image]:
        if self.src_rgba is None:
            return None
        h, w, _ = self.src_rgba.shape
        return Image.frombytes("RGBA", (w, h), self.src_rgba.tobytes())
