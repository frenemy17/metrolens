import cv2
import numpy as np
from typing import Optional

def recover_scale_aruco(image: np.ndarray, marker_size_mm: float = 50.0) -> Optional[float]:
    """
    Detects an ArUco marker in the image and returns the mm_per_pixel scale.
    Searches across common ArUco dictionaries (DICT_4X4_50, DICT_5X5_50, etc.).
    Returns scale float (mm/px), or None if no marker is found.
    """
    if image is None or not hasattr(cv2, 'aruco'):
        return None
        
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Search standard ArUco dictionaries
    dict_candidates = [
        cv2.aruco.DICT_4X4_50,
        cv2.aruco.DICT_4X4_100,
        cv2.aruco.DICT_5X5_50,
        cv2.aruco.DICT_6X6_50,
    ]

    for dict_id in dict_candidates:
        try:
            aruco_dict = cv2.aruco.getPredefinedDictionary(dict_id)
            parameters = cv2.aruco.DetectorParameters()
            
            # OpenCV 4.7+ API
            if hasattr(cv2.aruco, "ArucoDetector"):
                detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)
                corners, ids, _ = detector.detectMarkers(gray)
            else:
                # Older OpenCV API
                corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
                
            if ids is not None and len(corners) > 0:
                marker_corners = corners[0][0]
                
                # Calculate pixel length of the marker (average of 4 edges)
                side1 = np.linalg.norm(marker_corners[0] - marker_corners[1])
                side2 = np.linalg.norm(marker_corners[1] - marker_corners[2])
                side3 = np.linalg.norm(marker_corners[2] - marker_corners[3])
                side4 = np.linalg.norm(marker_corners[3] - marker_corners[0])
                
                avg_pixel_length = float((side1 + side2 + side3 + side4) / 4.0)
                if avg_pixel_length > 0:
                    return float(marker_size_mm / avg_pixel_length)
        except Exception:
            continue
            
    return None

def _srgb_to_linear(c: np.ndarray) -> np.ndarray:
    """WCAG 2.1 sRGB to linear conversion."""
    c_norm = np.clip(c / 255.0, 0.0, 1.0)
    return np.where(c_norm <= 0.04045, c_norm / 12.92, ((c_norm + 0.055) / 1.055) ** 2.4)

def compute_contrast_ratio(image: np.ndarray, x: int, y: int, w: int, h: int) -> float:
    """
    Computes WCAG 2.1 relative luminance contrast ratio between foreground (text)
    and background within the bounding box using Otsu bimodal segmentation.
    Returns ratio >= 1.0 (e.g., 4.5 for 4.5:1).
    """
    if image is None or image.size == 0 or w <= 0 or h <= 0:
        return 1.0

    img_h, img_w = image.shape[:2]
    x1, y1 = max(0, int(x)), max(0, int(y))
    x2, y2 = min(img_w, int(x + w)), min(img_h, int(y + h))

    if x2 <= x1 or y2 <= y1:
        return 1.0

    roi = image[y1:y2, x1:x2]
    if roi.size == 0:
        return 1.0

    # Color space conversions
    if len(roi.shape) == 3:
        rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    else:
        rgb = cv2.cvtColor(roi, cv2.COLOR_GRAY2RGB)
        gray = roi

    # Calculate per-pixel linear luminance per WCAG 2.1: L = 0.2126*R + 0.7152*G + 0.0722*B
    rgb_lin = _srgb_to_linear(rgb.astype(np.float32))
    lum = 0.2126 * rgb_lin[:, :, 0] + 0.7152 * rgb_lin[:, :, 1] + 0.0722 * rgb_lin[:, :, 2]

    # Segment foreground vs background using Otsu thresholding
    thresh_val, _ = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    bright_mask = gray >= thresh_val
    dark_mask = ~bright_mask

    total_px = roi.shape[0] * roi.shape[1]
    bright_count = np.sum(bright_mask)
    dark_count = total_px - bright_count

    # If both clusters have sufficient representation (> 3% of area), use their median luminance
    if bright_count > 0.03 * total_px and dark_count > 0.03 * total_px:
        l_bright = float(np.median(lum[bright_mask]))
        l_dark = float(np.median(lum[dark_mask]))
    else:
        # Fallback to robust percentiles (10th vs 90th) to ignore sensor noise outliers
        l_bright = float(np.percentile(lum, 90))
        l_dark = float(np.percentile(lum, 10))

    hi = max(l_bright, l_dark)
    lo = min(l_bright, l_dark)

    contrast = (hi + 0.05) / (lo + 0.05)
    return round(float(contrast), 2)
