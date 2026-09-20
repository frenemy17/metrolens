import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch
import numpy as np
import cv2
import io

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
def test_evaluation_and_report_flow(mock_run_ocr):
    headers = get_auth_headers()
    
    # 1. Create inspection
    insp = client.post("/api/v1/inspections", json={"category": "food"}, headers=headers).json()
    insp_id = insp["id"]
    
    # 2. Upload image
    files = {"file": ("test.jpg", create_dummy_image(), "image/jpeg")}
    img_res = client.post(
        f"/api/v1/inspections/{insp_id}/images",
        files=files,
        data={"image_type": "PRIMARY_PANEL"},
        headers=headers
    ).json()
    img_id = img_res["id"]
    
    # 3. Calibrate
    calib_payload = {
        "image_id": img_id,
        "corners": [
            {"x": 10, "y": 10}, {"x": 90, "y": 10},
            {"x": 90, "y": 90}, {"x": 10, "y": 90}
        ],
        "reference_size_mm": 30.0
    }
    client.post(f"/api/v1/inspections/{insp_id}/calibrate", json=calib_payload, headers=headers)
    
    # 4. Measure
    mock_run_ocr.return_value = {"value": "Net Weight minimum 500g", "confidence": 0.95}
    meas_payload = {
        "image_id": img_id,
        "roi_top_left": {"x": 20, "y": 20},
        "roi_bottom_right": {"x": 80, "y": 80},
        "declaration_type": "r6-1c-net-quantity",
        "printing_method": "PRINTED"
    }
    meas_res = client.post(f"/api/v1/inspections/{insp_id}/measurements", json=meas_payload, headers=headers).json()
    meas_id = meas_res["id"]
    
    # 5. Confirm Measurement
    client.patch(
        f"/api/v1/inspections/measurements/{meas_id}",
        json={"confirmed_text": "Net Weight minimum 500g"},
        headers=headers
    )
    
    # 6. Evaluate Inspection
    eval_payload = {
        "pdp_area_cm2": 50.0,
        "inspection_context": {}
    }
    eval_res = client.post(
        f"/api/v1/inspections/{insp_id}/evaluate",
        json=eval_payload,
        headers=headers
    )
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    # It contains misleading word "minimum" which triggers SUSPECTED_NON_STANDARD.
    # It also might fail mandatory declarations (e.g. missing mfr-name)
    assert eval_data["verdict"] in ["FAIL", "SUSPECTED_NON_STANDARD"]
    
    # 7. Generate Report
    report_res = client.get(f"/api/v1/inspections/{insp_id}/report", headers=headers)
    assert report_res.status_code == 200
    report_data = report_res.json()
    assert report_data["inspection_metadata"]["inspection_id"] == insp_id
    assert len(report_data["chain_of_custody_audit_trail"]) == 2 # 1 confirm, 1 evaluate
