import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2
import pytest

from core.cv.calibration import calibrate_scale, get_euclidean_distance
from core.cv.measurement import get_ink_row_height_px, calculate_measured_height_mm, evaluate_guard_band

def create_synthetic_image():
    # Create a blank white image 800x800
    img = Image.new('L', (800, 800), color=255)
    draw = ImageDraw.Draw(img)
    
    # Draw a black square to represent the 30x30mm calibration card
    # Let's say 1mm = 10 pixels. So square is 300x300 pixels.
    # Top left at (100, 100), bottom right at (400, 400).
    draw.rectangle([100, 100, 400, 400], fill=0)
    
    # Inside the square or outside, draw some text
    # Let's draw a dark text block outside the square.
    # We'll just draw a precise filled rectangle to represent a block of text,
    # or use actual font. A precise filled rectangle is easier to measure deterministically.
    # We want text height to be 4mm (40 pixels).
    # Text block top-left (500, 200), bottom-right (600, 240).
    # Wait, the Otsu threshold uses > 5% dark pixels per row.
    # A solid rectangle will have 100% dark pixels for those rows.
    # So the rows from 200 to 239 (40 pixels total) will be active.
    draw.rectangle([500, 200, 700, 239], fill=0)
    
    # Add a little noise so cornerSubPix has gradients to work with, 
    # but PIL drawing is perfectly sharp so it might be fine or we might want to blur slightly.
    # cv2.cornerSubPix can struggle with perfectly sharp artificial corners (no gradient),
    # so we can apply a tiny gaussian blur.
    
    img_cv = np.array(img)
    img_cv = cv2.GaussianBlur(img_cv, (3, 3), 0)
    return img_cv

def test_deterministic_cv_pipeline():
    img_cv = create_synthetic_image()
    
    # The true corners of the drawn square are:
    # (100, 100), (400, 100), (400, 400), (100, 400)
    # We supply slightly perturbed points to simulate a human tap
    tapped_corners = [
        (102.0, 98.0),
        (398.0, 101.0),
        (401.0, 399.0),
        (99.0, 402.0)
    ]
    
    calibration_result = calibrate_scale(img_cv, tapped_corners, reference_size_mm=30.0)
    
    assert calibration_result["confidence_flag"] == "RELIABLE"
    
    # Since the square was 300x300 pixels, mm_px_scale should be 30.0 / 300 = 0.1 mm/px
    mm_per_px = calibration_result["mm_px_scale"]
    assert np.isclose(mm_per_px, 0.1, atol=0.005)
    
    # Now measure the text block
    # Text block is at [500:700 (x), 200:240 (y)]
    # We simulate dragging an ROI around it: top-left (490, 190), bottom-right (710, 250)
    roi_crop = img_cv[190:250, 490:710]
    
    height_px = get_ink_row_height_px(roi_crop, dark_pixel_threshold_ratio=0.05)
    
    # We drew the rectangle from 200 to 239 -> exactly 40 pixels tall
    assert height_px == 40
    
    height_mm = calculate_measured_height_mm(height_px, mm_per_px)
    
    # 40 pixels * 0.1 mm/px = 4.0 mm
    assert np.isclose(height_mm, 4.0, atol=0.1)
    
    # Evaluate the guard-band rule
    # The requirement is 4.0mm height minimum.
    # Measured is 4.0mm. Should PASS.
    verdict_pass = evaluate_guard_band(height_mm, threshold=4.0, confidence_flag="RELIABLE")
    assert verdict_pass == "PASS"
    
    # If the threshold was 4.1mm, difference is 0.1mm which is < 0.15mm (uncertainty)
    verdict_cannot_determine = evaluate_guard_band(height_mm, threshold=4.1, confidence_flag="RELIABLE")
    assert verdict_cannot_determine == "CANNOT_DETERMINE"
    
    # If the threshold was 4.2mm, difference is 0.2mm, which is > 0.15mm. Measured < Threshold - U. Should FAIL.
    verdict_fail = evaluate_guard_band(height_mm, threshold=4.2, confidence_flag="RELIABLE")
    assert verdict_fail == "FAIL"

def test_unreliable_calibration_guard_band():
    # If unreliable, uncertainty doubles from 0.15 to 0.30
    verdict_cannot_determine = evaluate_guard_band(4.0, threshold=4.2, confidence_flag="UNRELIABLE")
    # difference is 0.2, which is < 0.30 -> CANNOT_DETERMINE
    assert verdict_cannot_determine == "CANNOT_DETERMINE"
    
    # If difference is 0.4 > 0.30 -> FAIL
    verdict_fail = evaluate_guard_band(4.0, threshold=4.4, confidence_flag="UNRELIABLE")
    assert verdict_fail == "FAIL"
