import cv2
import numpy as np

def calculate_blur_score(image: np.ndarray) -> float:
    """
    Calculate blur score using the variance of the Laplacian.
    Higher variance -> sharper image.
    Lower variance -> blurrier image.
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    return float(variance)

def calculate_glare_score(image: np.ndarray, threshold: int = 253) -> float:
    """
    Calculate the ratio of saturated pixels (glare).
    Returns a value between 0.0 and 1.0.
    Higher score -> more glare.
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
        
    saturated_pixels = np.sum(gray > threshold)
    total_pixels = gray.size
    
    if total_pixels == 0:
        return 0.0
        
    return float(saturated_pixels / total_pixels)
