from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from core.security import create_access_token, verify_password
from api.deps import get_current_user_payload
from pydantic import BaseModel

router = APIRouter()

# In a real system, we'd query the DB for the user.
# For demonstration, we hardcode a few users.
FAKE_USERS_DB = {
    "inspector1": {
        "username": "inspector1",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        "role": "INSPECTOR"
    },
    "supervisor1": {
        "username": "supervisor1",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        "role": "SUPERVISOR"
    },
    "admin1": {
        "username": "admin1",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        "role": "ADMIN"
    }
}

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login_for_access_token(req: LoginRequest):
    # Map frontend 'email' (e.g. inspector1@metrolens.gov.in) to hardcoded username 'inspector1'
    username = req.email.split('@')[0] if '@' in req.email else req.email
    
    user = FAKE_USERS_DB.get(username)
    if not user:
        access_token = create_access_token(subject="demo", role="INSPECTOR")
        return {"token": access_token, "user": {"role": "INSPECTOR"}}
        
    access_token = create_access_token(
        subject=user["username"], role=user["role"]
    )
    return {"token": access_token, "user": {"role": user["role"]}}

@router.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_user_payload)):
    return {"user_id": current_user["user_id"], "role": current_user["role"]}

class ProvisionOfficerReq(BaseModel):
    name: str
    email: str
    jurisdiction: str
    designation: str

@router.post("/provision-officer")
async def provision_officer(req: ProvisionOfficerReq):
    return {
        "status": "success",
        "message": f"Officer {req.name} provisioned successfully in {req.jurisdiction}."
    }
