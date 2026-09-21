import cv2
import numpy as np

def calculate_blur_score(image: np.ndarray) -> float:
    """
    Calculate blur score using the variance of the Laplacian.
    Normalizes resolution to max dimension 1024px for scale-independent stability.
    Higher variance -> sharper image.
    Lower variance -> blurrier image (threshold typically < 5.0).
    """
    if image is None or image.size == 0:
        return 0.0

    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    h, w = gray.shape[:2]
    max_dim = max(h, w)
    if max_dim > 1024:
        scale = 1024.0 / max_dim
        gray = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    return float(round(variance, 2))

def calculate_glare_score(image: np.ndarray, threshold: int = 253) -> float:
    """
    Calculate the ratio of specular saturated pixels (glare).
    Returns a float between 0.0 and 1.0.
    Higher score -> more glare.
    """
    if image is None or image.size == 0:
        return 0.0

    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    total_pixels = gray.size
    if total_pixels == 0:
        return 0.0

    saturated_pixels = int(np.sum(gray >= threshold))
    return float(round(saturated_pixels / total_pixels, 4))
