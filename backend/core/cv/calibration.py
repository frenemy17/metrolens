import cv2
import numpy as np
from typing import Tuple, List, Dict, Any

def get_euclidean_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    return float(np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2))

def calibrate_scale(
    image: np.ndarray, 
    corners: List[Tuple[float, float]], 
    reference_size_mm: float = 30.0
) -> Dict[str, Any]:
    """
    Calibrate the scale (mm per pixel) based on 4 tapped corners of a reference card.
    
    Expected order of corners: top-left, top-right, bottom-right, bottom-left.
    """
    if len(corners) != 4:
        raise ValueError("Exactly 4 corners must be provided for calibration.")
        
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Convert corners to float32 numpy array
    corners_np = np.array(corners, dtype=np.float32).reshape(-1, 1, 2)
    
    # 1. Refine the tapped corners
    # Define criteria for cornerSubPix
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    win_size = (5, 5)
    zero_zone = (-1, -1)
    
    refined_corners = cv2.cornerSubPix(gray, corners_np, win_size, zero_zone, criteria)
    refined_pts = refined_corners.reshape(4, 2)
    
    tl, tr, br, bl = refined_pts
    
    # 2. Check for extreme perspective distortion (Confidence check)
    # Re-measure opposite sides (using the refined points in the original image)
    top_width = get_euclidean_distance(tl, tr)
    bottom_width = get_euclidean_distance(bl, br)
    left_height = get_euclidean_distance(tl, bl)
    right_height = get_euclidean_distance(tr, br)
    
    width_mismatch = abs(top_width - bottom_width) / max(top_width, bottom_width)
    height_mismatch = abs(left_height - right_height) / max(left_height, right_height)
    
    confidence_flag = "RELIABLE"
    if width_mismatch > 0.08 or height_mismatch > 0.08:
        confidence_flag = "UNRELIABLE"
        
    # 3. Rectification and Scale Calculation
    # We map the refined corners to a perfect square to find the average pixel size.
    max_width = max(int(top_width), int(bottom_width))
    max_height = max(int(left_height), int(right_height))
    # We expect a square, so we can take the max of width and height
    side_px = max(max_width, max_height)
    
    dst_pts = np.array([
        [0, 0],
        [side_px - 1, 0],
        [side_px - 1, side_px - 1],
        [0, side_px - 1]
    ], dtype=np.float32)
    
    # Compute the perspective transform matrix
    transform_matrix = cv2.getPerspectiveTransform(refined_pts, dst_pts)
    
    # Calculate mm per pixel
    mm_per_px = reference_size_mm / side_px
    
    return {
        "mm_px_scale": mm_per_px,
        "confidence_flag": confidence_flag,
        "transform_matrix": transform_matrix.tolist(),
        "rectified_side_px": side_px,
        "refined_corners": refined_pts.tolist(),
        "mismatches": {
            "width_mismatch": float(width_mismatch),
            "height_mismatch": float(height_mismatch)
        }
    }
