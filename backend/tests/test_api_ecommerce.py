import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def get_auth_headers():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "inspector1", "password": "secret"}
    )
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}

def test_ecommerce_audit():
    headers = get_auth_headers()
    
    # Passing e-commerce case
    # r6-1d (mfg date) is missing, but it's e-commerce, so it should PASS
    payload_pass = {
        "url": "https://example.com/product/1",
        "extracted_declarations": [
            "r6-1a-mfr-name-address",
            "r6-1b-generic-name",
            "r6-1c-net-quantity",
            "r6-1e-mrp",
            "r6-2-consumer-care",
            "r6-10-ecommerce-declarations"
        ],
        "context": {}
    }
    
    res1 = client.post("/api/v1/ecommerce/audit", json=payload_pass, headers=headers)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["verdict"] == "PASS"
    assert data1["channel"] == "e-commerce"
    
    # Failed e-commerce case
    # Missing generic name (r6-1b)
    payload_fail = {
        "url": "https://example.com/product/2",
        "extracted_declarations": [
            "r6-1a-mfr-name-address",
            "r6-1c-net-quantity"
        ],
        "context": {}
    }
    
    res2 = client.post("/api/v1/ecommerce/audit", json=payload_fail, headers=headers)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["verdict"] == "FAIL"
