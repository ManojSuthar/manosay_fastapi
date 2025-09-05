# routes/auth.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from models.user_models import RegisterIn, LoginIn, UserOut
from services.auth_service import find_user_by_email, create_user, authenticate_user, create_access_token
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/api", tags=["auth"])

def serialize_user(user_doc):
    """Convert MongoDB document to JSON-serializable format"""
    if not user_doc:
        return None
    
    user_dict = dict(user_doc)
    # Convert ObjectId to string
    if '_id' in user_dict:
        user_dict['_id'] = str(user_dict['_id'])
    
    # Convert datetime objects to ISO format strings
    for key, value in user_dict.items():
        if isinstance(value, datetime):
            user_dict[key] = value.isoformat()
    
    return user_dict

@router.post("/register", status_code=201)
async def register(payload: RegisterIn):
    existing = await find_user_by_email(payload.email)
    if existing:
        return JSONResponse(status_code=400, content={"success": False, "message": "Email already registered"})
    try:
        user_id = await create_user(payload.name, payload.email, payload.password)
        return JSONResponse(status_code=201, content={"success": True, "message": "User registered", "user_id": user_id})
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to register user")

@router.post("/login")
async def login(payload: LoginIn):
    user = await authenticate_user(payload.email, payload.password)
    if not user:
        return JSONResponse(status_code=401, content={"success": False, "message": "Invalid credentials"})
    
    # Create JWT token
    access_token = create_access_token({"sub": user["email"], "id": str(user["_id"])})
    
    return JSONResponse(
        status_code=200, 
        content={
            "success": True, 
            "message": "Login successful", 
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user["_id"]),
                "name": user["name"],
                "email": user["email"]
            }
        }
    )