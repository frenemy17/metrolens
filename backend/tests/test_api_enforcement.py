import pytest
from fastapi.testclient import TestClient
from main import app
from api.v1.inspections import mock_db

client = TestClient(app)

def get_auth_headers(role="SUPERVISOR"):
    username = "supervisor1" if role == "SUPERVISOR" else "inspector1"
    response = client.post(
        "/api/v1/auth/login",
        json={"email": username, "password": "secret"}
    )
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}

def test_enforcement_workflow():
    supervisor_headers = get_auth_headers("SUPERVISOR")
    inspector_headers = get_auth_headers("INSPECTOR")
    
    # Manually inject a failed inspection to test the state machine
    insp_id = "test-insp-fail"
    mock_db["inspections"][insp_id] = {
        "id": insp_id,
        "officer_id": "inspector1",
        "status": "COMPLETED",
        "verdict": "FAIL"
    }
    
    # Inspector should be forbidden (403) from enforcing
    res_forbidden = client.post(
        f"/api/v1/inspections/{insp_id}/enforce",
        json={"action": "IMPROVEMENT_NOTICE_ISSUED"},
        headers=inspector_headers
    )
    assert res_forbidden.status_code == 403
    
    # Supervisor can transition
    res_success = client.post(
        f"/api/v1/inspections/{insp_id}/enforce",
        json={"action": "IMPROVEMENT_NOTICE_ISSUED", "notes": "Notice sent"},
        headers=supervisor_headers
    )
    assert res_success.status_code == 200
    assert res_success.json()["status"] == "IMPROVEMENT_NOTICE_ISSUED"
    
    # Then transition to COMPLIANT
    res_compliant = client.post(
        f"/api/v1/inspections/{insp_id}/enforce",
        json={"action": "COMPLIANT"},
        headers=supervisor_headers
    )
    assert res_compliant.status_code == 200
    assert res_compliant.json()["status"] == "COMPLIANT"
    
    # Invalid transition
    res_invalid = client.post(
        f"/api/v1/inspections/{insp_id}/enforce",
        json={"action": "DIRECT_ENFORCEMENT"},
        headers=supervisor_headers
    )
    assert res_invalid.status_code == 400
