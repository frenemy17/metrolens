import pytest
from fastapi.testclient import TestClient
from main import app
import cv2
import numpy as np
import io
import os

client = TestClient(app)

# Helper to get a token
def get_auth_headers():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "inspector1", "password": "secret"} # using the hardcoded pass in auth.py
    )
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}

def create_dummy_image():
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    # Add some details so blur/glare don't fail completely with division by zero
    cv2.rectangle(img, (20, 20), (80, 80), (255, 255, 255), -1)
    is_success, buffer = cv2.imencode(".jpg", img)
    return io.BytesIO(buffer)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200

def test_create_inspection():
    headers = get_auth_headers()
    response = client.post(
        "/api/v1/inspections",
        json={"category": "food", "channel": "retail"},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "DRAFT"
    assert "id" in data
    
def test_upload_image():
    headers = get_auth_headers()
    
    # Create inspection first
    resp1 = client.post("/api/v1/inspections", json={}, headers=headers)
    insp_id = resp1.json()["id"]
    
    # Upload image
    img_io = create_dummy_image()
    files = {"file": ("test.jpg", img_io, "image/jpeg")}
    data = {"image_type": "PRIMARY_PANEL"}
    
    response = client.post(
        f"/api/v1/inspections/{insp_id}/images",
        files=files,
        data=data,
        headers=headers
    )
    
    assert response.status_code == 200
    res_data = response.json()
    assert "blur_score" in res_data
    assert "glare_score" in res_data
    assert "id" in res_data
