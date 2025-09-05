# repositories/user_repository.py
from typing import Optional, Dict, Any
from bson import ObjectId
from datetime import datetime
from db import get_database

# Async repository functions using Motor (awaitable)


async def find_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Return the raw user document (including password) or None.
    """
    db = get_database()
    doc = await db["users"].find_one({"email": email})
    return doc


async def insert_user(user_doc: Dict[str, Any]) -> ObjectId:
    """
    Insert a user doc and return the inserted_id (ObjectId).
    """
    db = get_database()
    res = await db["users"].insert_one(user_doc)
    return res.inserted_id


async def find_user_by_id(oid: str) -> Optional[Dict[str, Any]]:
    db = get_database()
    try:
        obj = ObjectId(oid)
    except Exception:
        return None
    doc = await db["users"].find_one({"_id": obj})
    return doc
