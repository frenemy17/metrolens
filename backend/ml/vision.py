import cv2
import numpy as np

def recover_scale_aruco(image: np.ndarray, marker_size_mm: float = 50.0) -> float:
    """
    Detects an ArUco marker in the image and returns the mm_per_pixel scale.
    Default assumes a 50mm x 50mm marker (e.g. ML-REF-2026-0842).
    Returns a scale float, or None if no marker is found.
    """
    if image is None:
        return None
        
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # ArUco dictionary (we'll assume a common one like DICT_4X4_50)
    # Different OpenCV versions have different ways of getting the dictionary
    try:
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        parameters = cv2.aruco.DetectorParameters()
        
        # New OpenCV 4.7+ API
        detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)
        corners, ids, rejected = detector.detectMarkers(gray)
    except AttributeError:
        # Older OpenCV API
        aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
        parameters = cv2.aruco.DetectorParameters_create()
        corners, ids, rejected = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
        
    if ids is not None and len(corners) > 0:
        # Use the first marker found
        marker_corners = corners[0][0]
        
        # Calculate pixel length of the marker (average of the 4 sides)
        side1 = np.linalg.norm(marker_corners[0] - marker_corners[1])
        side2 = np.linalg.norm(marker_corners[1] - marker_corners[2])
        side3 = np.linalg.norm(marker_corners[2] - marker_corners[3])
        side4 = np.linalg.norm(marker_corners[3] - marker_corners[0])
        
        avg_pixel_length = (side1 + side2 + side3 + side4) / 4.0
        
        if avg_pixel_length > 0:
            return marker_size_mm / avg_pixel_length
            
    return None

def compute_contrast_ratio(image: np.ndarray, x: int, y: int, w: int, h: int) -> float:
    """
    Estimates the contrast ratio between foreground (text) and background
    within a specific bounding box.
    Returns ratio (e.g., 4.5 for 4.5:1).
    """
    roi = image[y:y+h, x:x+w]
    if roi.size == 0:
        return 1.0
        
    # Convert to grayscale
    if len(roi.shape) == 3:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    else:
        gray = roi
        
    # Simple heuristic: max pixel is background (light), min pixel is text (dark)
    # Assumes dark text on light background.
    min_val, max_val, _, _ = cv2.minMaxLoc(gray)
    
    # Calculate relative luminance using a very simplified approximation for demonstration
    # Real contrast ratio (WCAG): (L1 + 0.05) / (L2 + 0.05)
    l1 = (max_val / 255.0)
    l2 = (min_val / 255.0)
    
    # Avoid division by zero
    if l2 + 0.05 == 0:
        return 21.0
        
    contrast = (l1 + 0.05) / (l2 + 0.05)
    
    # If light text on dark background, it might be inverted
    if contrast < 1:
        contrast = 1 / contrast
        
    return float(contrast)
