import cv2
import numpy as np

def get_ink_row_height_px(roi_image: np.ndarray, dark_pixel_threshold_ratio: float = 0.05) -> int:
    """
    Calculate the ink-row height of the text inside the ROI in pixels.
    1. Convert to grayscale.
    2. Apply Otsu thresholding.
    3. Sum dark pixels per row.
    4. Find the first and last rows where the dark pixel count > 5% of the ROI width.
    """
    if len(roi_image.shape) == 3:
        gray = cv2.cvtColor(roi_image, cv2.COLOR_BGR2GRAY)
    else:
        gray = roi_image
        
    # Otsu's thresholding
    # cv2.THRESH_BINARY_INV: dark text on light background becomes white text on black background
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Sum pixels per row. Since foreground is 255, we divide by 255 to get the count of dark pixels.
    row_sums = np.sum(thresh == 255, axis=1)
    
    width = roi_image.shape[1]
    threshold_count = width * dark_pixel_threshold_ratio
    
    # Find rows exceeding the threshold
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
    return float(height_px * mm_per_px)

def evaluate_guard_band(measured_value: float, threshold: float, confidence_flag: str, base_uncertainty: float = 0.15) -> str:
    """
    ILAC G8 style guard-band decision rule.
    uncertainty U = 0.15mm, doubled if calibration UNRELIABLE.
    |measured - threshold| < U -> CANNOT_DETERMINE.
    If measured >= threshold -> PASS.
    If measured < threshold - U -> FAIL.
    """
    uncertainty = base_uncertainty
    if confidence_flag == "UNRELIABLE":
        uncertainty *= 2.0
        
    if measured_value >= threshold:
        return "PASS"
    elif abs(measured_value - threshold) < uncertainty:
        return "CANNOT_DETERMINE"
    else:
        return "FAIL"
