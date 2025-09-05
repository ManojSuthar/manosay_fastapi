# routes/admin.py
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from models.user_models import RegisterIn
from services.auth_service import find_user_by_email, create_user, get_current_user
from db import get_database

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/create-admin")
async def create_admin_account(payload: RegisterIn):
    # Check if admin already exists
    existing_admin = await find_user_by_email(payload.email)
    if existing_admin:
        return JSONResponse(
            status_code=400,
            content={"success": False,
                     "message": "Admin account already exists"}
        )

    try:
        # Create admin account
        admin_id = await create_user(payload.name, payload.email, payload.password)
        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "message": "Admin account created successfully",
                "admin_id": admin_id
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to create admin account")
