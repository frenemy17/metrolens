import pytest
import os
import json
from fastapi.testclient import TestClient
from main import app
import io

client = TestClient(app)

def get_auth_headers(role="ADMIN"):
    username = "admin1" if role == "ADMIN" else "inspector1"
    response = client.post(
        "/api/v1/auth/login",
        json={"email": username, "password": "secret"}
    )
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}

def test_upload_gazette():
    admin_headers = get_auth_headers("ADMIN")
    insp_headers = get_auth_headers("INSPECTOR")
    
    dummy_pdf = io.BytesIO(b"Dummy PDF content representing a gazette")
    files = {"file": ("gazette.pdf", dummy_pdf, "application/pdf")}
    
    # Inspector blocked
    res_403 = client.post("/api/v1/admin/rule-sync/upload", files=files, headers=insp_headers)
    assert res_403.status_code == 403
    
    # Admin success
    files = {"file": ("gazette.pdf", dummy_pdf, "application/pdf")}
    res = client.post("/api/v1/admin/rule-sync/upload", files=files, headers=admin_headers)
    assert res.status_code == 200
    
    data = res.json()
    assert len(data["suggestions"]) > 0
    assert "value" in data["suggestions"][0]
    assert data["suggestions"][0]["value"]["action"] == "ADD_MANDATORY_DECLARATION"

def test_publish_rulepack():
    admin_headers = get_auth_headers("ADMIN")
    
    payload = {
        "new_version_name": "v2",
        "effective_from": "2024-01-01",
        "source_citation": "Mocked 2024 Amendment",
        "approved_changes": [
            {
                "action": "ADD_MANDATORY_DECLARATION",
                "details": {
                    "id": "r6-1g-qr-code",
                    "citation": "Rule 6(1)(g)",
                    "check": "presence",
                    "condition": "commodity_is_electronic"
                }
            }
        ]
    }
    
    res = client.post("/api/v1/admin/rule-sync/publish", json=payload, headers=admin_headers)
    assert res.status_code == 200
    
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["new_version"] == "v2"
    
    # Check if the change was actually applied in the returned structure
    decls = data["rulepack"]["mandatory_declarations"]
    assert any(d.get("id") == "r6-1g-qr-code" for d in decls)
    
    # Cleanup the created JSON file to avoid polluting the workspace permanently
    from api.v1.inspections import rule_engine
    filepath = os.path.join(rule_engine.rulepacks_dir, "v2.json")
    if os.path.exists(filepath):
        os.remove(filepath)
