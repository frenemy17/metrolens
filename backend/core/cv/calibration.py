import cv2
import numpy as np
from typing import Tuple, List, Dict, Any, Union

def get_euclidean_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    return float(np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2))

def calibrate_scale(
    image: np.ndarray, 
    corners: List[Tuple[float, float]], 
    reference_size_mm: Union[float, Tuple[float, float]] = 30.0
) -> Dict[str, Any]:
    """
    Calibrate the scale (mm per pixel) based on 4 corners of a reference object.
    
    Expected order of corners: top-left, top-right, bottom-right, bottom-left.
    Gracefully handles image boundary clamping so cornerSubPix never crashes.
    """
    if len(corners) != 4:
        raise ValueError("Exactly 4 corners must be provided for calibration.")
        
    if image is None or image.size == 0:
        return {
            "mm_px_scale": 0.1,
            "confidence_flag": "UNRELIABLE",
            "transform_matrix": None,
            "rectified_side_px": 0,
            "refined_corners": corners,
            "mismatches": {"width_mismatch": 1.0, "height_mismatch": 1.0}
        }

    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    h_img, w_img = gray.shape[:2]
    win_size = (5, 5)
    pad_x = win_size[0] + 1
    pad_y = win_size[1] + 1

    # Clamp corners to ensure they reside strictly within the image boundary required by cornerSubPix
    clamped_corners = []
    for x, y in corners:
        cx = float(np.clip(x, pad_x, max(pad_x, w_img - 1 - pad_x)))
        cy = float(np.clip(y, pad_y, max(pad_y, h_img - 1 - pad_y)))
        clamped_corners.append([cx, cy])

    corners_np = np.array(clamped_corners, dtype=np.float32).reshape(-1, 1, 2)
    
    # 1. Refine the corners using cornerSubPix
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    zero_zone = (-1, -1)
    
    try:
        refined_corners = cv2.cornerSubPix(gray, corners_np, win_size, zero_zone, criteria)
        refined_pts = refined_corners.reshape(4, 2)
    except cv2.error:
        # Fallback to clamped corners if subpixel refinement fails (e.g. uniform/noisy region)
        refined_pts = np.array(clamped_corners, dtype=np.float32)
    
    tl, tr, br, bl = refined_pts
    
    # 2. Perspective distortion & confidence check
    top_width = get_euclidean_distance(tl, tr)
    bottom_width = get_euclidean_distance(bl, br)
    left_height = get_euclidean_distance(tl, bl)
    right_height = get_euclidean_distance(tr, br)
    
    max_w = max(top_width, bottom_width, 1.0)
    max_h = max(left_height, right_height, 1.0)
    
    width_mismatch = abs(top_width - bottom_width) / max_w
    height_mismatch = abs(left_height - right_height) / max_h
    
    confidence_flag = "RELIABLE"
    if width_mismatch > 0.08 or height_mismatch > 0.08:
        confidence_flag = "UNRELIABLE"
        
    # 3. Rectification and Scale Calculation
    max_width_px = max(int(top_width), int(bottom_width), 1)
    max_height_px = max(int(left_height), int(right_height), 1)

    ref_w_mm = reference_size_mm[0] if isinstance(reference_size_mm, (tuple, list)) else float(reference_size_mm)
    ref_h_mm = reference_size_mm[1] if isinstance(reference_size_mm, (tuple, list)) else ref_w_mm

    side_px = max(max_width_px, max_height_px)
    
    dst_pts = np.array([
        [0, 0],
        [max_width_px - 1, 0],
        [max_width_px - 1, max_height_px - 1],
        [0, max_height_px - 1]
    ], dtype=np.float32)
    
    try:
        transform_matrix = cv2.getPerspectiveTransform(refined_pts, dst_pts)
        t_matrix_list = transform_matrix.tolist()
    except Exception:
        t_matrix_list = None
    
    # Scale in mm per pixel
    mm_per_px_w = ref_w_mm / max_width_px
    mm_per_px_h = ref_h_mm / max_height_px
    mm_per_px = float((mm_per_px_w + mm_per_px_h) / 2.0)
    
    return {
        "mm_px_scale": float(round(mm_per_px, 5)),
        "confidence_flag": confidence_flag,
        "transform_matrix": t_matrix_list,
        "rectified_side_px": side_px,
        "refined_corners": refined_pts.tolist(),
        "mismatches": {
            "width_mismatch": float(round(width_mismatch, 4)),
            "height_mismatch": float(round(height_mismatch, 4))
        }
    }
