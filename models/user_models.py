# models/user_models.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class RegisterIn(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=6)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    created_at: Optional[datetime]
