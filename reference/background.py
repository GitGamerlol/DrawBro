"""
OpenCV-based reference image utilities (perspective correction).
"""
from __future__ import annotations
import numpy as np
import cv2


def load_image(path: str) -> np.ndarray:
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(path)
    # convert BGR to RGBA if needed
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGBA)
    elif img.shape[2] == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
    return img


def perspective_warp(img: np.ndarray, src_pts: list[tuple[float, float]], dst_size: tuple[int, int]) -> np.ndarray:
    """Warp the image by mapping src_pts (4 points) to the corners of dst_size (w,h)."""
    if len(src_pts) != 4:
        raise ValueError("src_pts must be 4 points")
    w, h = dst_size
    dst_pts = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype=np.float32)
    src = np.array(src_pts, dtype=np.float32)
    M = cv2.getPerspectiveTransform(src, dst_pts)
    warped = cv2.warpPerspective(img, M, (w, h), flags=cv2.INTER_LINEAR)
    return warped
