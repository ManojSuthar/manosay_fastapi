# services/auth_service.py
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import bcrypt
import jwt
from dotenv import load_dotenv

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# async repository functions (Motor)
from repositories.user_repository import find_by_email, insert_user

load_dotenv()

# JWT config
JWT_SECRET = os.getenv("JWT_SECRET", "change_this_in_prod")
JWT_ALGORITHM = "HS256"
JWT_EXP_HOURS = int(os.getenv("JWT_EXP_HOURS", "24"))

security = HTTPBearer()


# -------------------------
# Low-level helpers
# -------------------------
def _hash_password_sync(password: str) -> bytes:
    """Return bcrypt hash bytes (sync)."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt)


def _verify_password_sync(plain: str, hashed: str) -> bool:
    """Verify plaintext against stored bcrypt hash (stored as UTF-8 string)."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        # fallback if stored is bytes-like
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), bytes(hashed))
        except Exception:
            return False


# -------------------------
# Public service functions (names expected by routes)
# -------------------------
async def find_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Return raw user document (including password) or None.
    Uses async repository function find_by_email.
    """
    return await find_by_email(email)


async def create_user(name: str, email: str, password: str, role: str = "admin") -> str:
    """
    Create a new user (with bcrypt-hashed password) and return inserted_id as string.
    """
    # Hash synchronously (bcrypt is CPU-bound). If high throughput needed, run in executor.
    hashed_bytes = _hash_password_sync(password)
    hashed_str = hashed_bytes.decode("utf-8")

    user_doc = {
        "name": name,
        "email": email,
        "password": hashed_str,
        "role": role,
        "created_at": datetime.utcnow(),
    }

    inserted_id = await insert_user(user_doc)
    return str(inserted_id)


async def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Verify credentials and return sanitized user dict (no password) on success.
    """
    user = await find_by_email(email)
    if not user:
        return None

    stored = user.get("password", "")
    ok = _verify_password_sync(password, stored)
    if not ok:
        return None

    # sanitize
    return {
        "_id": str(user.get("_id")),
        "name": user.get("name"),
        "email": user.get("email"),
        "role": user.get("role"),
        "created_at": user.get("created_at"),
    }


def create_access_token(data: Dict[str, Any], expires_hours: int = JWT_EXP_HOURS) -> str:
    """
    Create JWT token (string) containing `data` and exp claim.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=expires_hours)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token if isinstance(token, str) else token.decode("utf-8")


# -------------------------
# Dependency to get user from Bearer token
# -------------------------
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
