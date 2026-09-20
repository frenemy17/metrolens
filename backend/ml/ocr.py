import cv2
import numpy as np
import pytesseract
from typing import Dict, Any, Union

def run_ocr_with_bboxes(image: np.ndarray, lang: str = "eng+hin") -> Dict[str, Any]:
    """
    Run Tesseract OCR on the given image region.
    Returns extracted text, average confidence, and a list of bounding boxes for each word.
    """
    if len(image.shape) == 3:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    else:
        rgb = image
        
    data = pytesseract.image_to_data(rgb, lang=lang, output_type=pytesseract.Output.DICT)
    
    text_parts = []
    confidences = []
    bboxes = []
    
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        conf = float(data['conf'][i])
        
        if text and conf > 0:
            text_parts.append(text)
            confidences.append(conf)
            
            x = data['left'][i]
            y = data['top'][i]
            w = data['width'][i]
            h = data['height'][i]
            bboxes.append({
                "text": text,
                "x": x,
                "y": y,
                "w": w,
                "h": h,
                "confidence": conf
            })
            
    extracted_text = " ".join(text_parts)
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    
    return {
        "value": extracted_text,
        "confidence": avg_conf,
        "bboxes": bboxes
    }

def run_ocr(image: np.ndarray, lang: str = "eng+hin") -> Dict[str, Union[str, float]]:
    # Legacy wrapper for backward compatibility
    res = run_ocr_with_bboxes(image, lang)
    return {
        "value": res["value"],
        "confidence": res["confidence"]
    }
