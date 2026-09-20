import pytest
from fastapi import HTTPException
from core.security import create_access_token, verify_password, get_password_hash
from api.deps import get_current_user_payload, RoleChecker

def test_password_hashing():
    pwd = "secretpassword"
    hashed = get_password_hash(pwd)
    
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

@pytest.mark.asyncio
async def test_jwt_token_validation():
    token = create_access_token(subject="user123", role="INSPECTOR")
    
    payload = await get_current_user_payload(token)
    assert payload["user_id"] == "user123"
    assert payload["role"] == "INSPECTOR"

@pytest.mark.asyncio
async def test_role_checker():
    # Only supervisors allowed
    supervisor_checker = RoleChecker(["SUPERVISOR"])
    
    payload_inspector = {"user_id": "1", "role": "INSPECTOR"}
    payload_supervisor = {"user_id": "2", "role": "SUPERVISOR"}
    
    # Should pass
    result = supervisor_checker(user_payload=payload_supervisor)
    assert result == payload_supervisor
    
    # Should raise HTTP 403
    with pytest.raises(HTTPException) as excinfo:
        supervisor_checker(user_payload=payload_inspector)
        
    assert excinfo.value.status_code == 403
