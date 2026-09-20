import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch
import numpy as np
import cv2
import io
import json

client = TestClient(app)

def get_auth_headers():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "inspector1", "password": "secret"}
    )
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}

def create_dummy_image():
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.rectangle(img, (20, 20), (80, 80), (255, 255, 255), -1)
    is_success, buffer = cv2.imencode(".jpg", img)
    return io.BytesIO(buffer)

@patch("api.v1.inspections.run_ocr")
def test_calibrate_and_measure(mock_run_ocr):
    headers = get_auth_headers()
    
    # Setup: Create inspection and upload image
    insp = client.post("/api/v1/inspections", json={}, headers=headers).json()
    insp_id = insp["id"]
    
    files = {"file": ("test.jpg", create_dummy_image(), "image/jpeg")}
    img_res = client.post(
        f"/api/v1/inspections/{insp_id}/images",
        files=files,
        data={"image_type": "PRIMARY_PANEL"},
        headers=headers
    ).json()
    img_id = img_res["id"]
    
    # Calibrate
    calib_payload = {
        "image_id": img_id,
        "corners": [
            {"x": 10, "y": 10},
            {"x": 90, "y": 10},
            {"x": 90, "y": 90},
            {"x": 10, "y": 90}
        ],
        "reference_size_mm": 30.0
    }
    
    calib_res = client.post(
        f"/api/v1/inspections/{insp_id}/calibrate",
        json=calib_payload,
        headers=headers
    )
    assert calib_res.status_code == 200
    assert "mm_px_scale" in calib_res.json()
    
    # Measure
    # Mock OCR response
    mock_run_ocr.return_value = {"value": "Net Weight 500g", "confidence": 0.95}
    
    meas_payload = {
        "image_id": img_id,
        "roi_top_left": {"x": 20, "y": 20},
        "roi_bottom_right": {"x": 80, "y": 80},
        "declaration_type": "r6-1c-net-quantity",
        "printing_method": "PRINTED"
    }
    
    meas_res = client.post(
        f"/api/v1/inspections/{insp_id}/measurements",
        json=meas_payload,
        headers=headers
    )
    
    assert meas_res.status_code == 200
    meas_data = meas_res.json()
    assert "height_mm" in meas_data
    assert meas_data["ocr_suggestion"]["value"] == "Net Weight 500g"
    assert meas_data["confirmed_text"] is None
    
    # Confirm
    meas_id = meas_data["id"]
    confirm_res = client.patch(
        f"/api/v1/inspections/measurements/{meas_id}", # Oops, the path in routes was /measurements/{meas_id} not /inspections/measurements
        json={"confirmed_text": "Net Weight 500g"},
        headers=headers
    )
    # The route in the app is just /measurements/{id} but it's mounted under /api/v1/inspections
    # Wait, the route is @router.patch("/measurements/{meas_id}") mounted on /api/v1/inspections
    # So the URL is /api/v1/inspections/measurements/{meas_id}
    assert confirm_res.status_code == 200
    assert confirm_res.json()["confirmed_text"] == "Net Weight 500g"
