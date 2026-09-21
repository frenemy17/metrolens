import cv2
import numpy as np

def get_ink_row_height_px(roi_image: np.ndarray, dark_pixel_threshold_ratio: float = 0.05) -> int:
    """
    Calculate the ink-row height of the text inside the ROI in pixels.
    Detects text polarity (dark-on-light vs light-on-dark) automatically:
    1. Sample perimeter pixels to establish background tone.
    2. Apply Otsu thresholding with proper polarity so text ink is foreground (255).
    3. Sum ink pixels per row.
    4. Find the first and last rows where ink count > dark_pixel_threshold_ratio of width.
    """
    if roi_image is None or roi_image.size == 0:
        return 0

    if len(roi_image.shape) == 3:
        gray = cv2.cvtColor(roi_image, cv2.COLOR_BGR2GRAY)
    else:
        gray = roi_image

    h, w = gray.shape[:2]
    if h <= 1 or w <= 1:
        return int(h)

    # Sample outer perimeter border pixels to determine background luminosity
    border_pixels = np.concatenate([
        gray[0, :], gray[-1, :], gray[:, 0], gray[:, -1]
    ])
    is_dark_background = float(np.median(border_pixels)) < 128.0

    # Polarity-aware Otsu thresholding:
    # If dark background: text is bright -> cv2.THRESH_BINARY (text becomes 255)
    # If light background: text is dark -> cv2.THRESH_BINARY_INV (text becomes 255)
    thresh_flag = cv2.THRESH_BINARY if is_dark_background else cv2.THRESH_BINARY_INV
    _, thresh = cv2.threshold(gray, 0, 255, thresh_flag + cv2.THRESH_OTSU)

    # Sum ink pixels (255) per row
    row_sums = np.sum(thresh == 255, axis=1)
    threshold_count = max(1, w * dark_pixel_threshold_ratio)

    active_rows = np.where(row_sums > threshold_count)[0]
    if len(active_rows) == 0:
        return 0

    first_row = active_rows[0]
    last_row = active_rows[-1]

    height_px = last_row - first_row + 1
    return int(height_px)

def calculate_measured_height_mm(height_px: int, mm_per_px: float) -> float:
    """
    Convert the pixel height to mm.
    """
    if height_px <= 0 or mm_per_px <= 0:
        return 0.0
    return float(round(height_px * mm_per_px, 2))

def evaluate_guard_band(measured_value: float, threshold: float, confidence_flag: str, base_uncertainty: float = 0.15) -> str:
    """
    ILAC G8 style guard-band decision rule.
    uncertainty U = 0.15mm, doubled if calibration UNRELIABLE.
    |measured - threshold| < U -> CANNOT_DETERMINE.
    If measured >= threshold -> PASS.
    If measured < threshold - U -> FAIL.
    """
    uncertainty = base_uncertainty
    if str(confidence_flag).upper() in ("UNRELIABLE", "ESTIMATED"):
        uncertainty *= 2.0

    if measured_value >= threshold:
        return "PASS"
    elif abs(measured_value - threshold) < uncertainty:
        return "CANNOT_DETERMINE"
    else:
        return "FAIL"
