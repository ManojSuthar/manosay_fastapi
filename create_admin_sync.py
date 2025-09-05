# create_admin_sync.py
"""
Quick sync fix: hashes async password using asyncio.run and uses sync pymongo calls.
Run: python create_admin_sync.py
"""
import asyncio
from datetime import datetime
from utils.security import hash_password  # THIS is async in your repo
from db import get_database

ADMIN_EMAIL = "manojmottyar@gmail.com"
ADMIN_PWD = "#Pooja1509"


def create_admin_account_sync():
    db = get_database()
    users_collection = db["users"]

    # Check if admin already exists
    existing_admin = users_collection.find_one({"email": ADMIN_EMAIL})
    if existing_admin:
        print("Admin account already exists!")
        return

    # Hash password (hash_password is async - run it in event loop)
    hashed = asyncio.run(hash_password(ADMIN_PWD))

    admin_data = {
        "name": "Manoj Admin User",
        "email": ADMIN_EMAIL,
        "password": hashed,
        "role": "admin",
        "created_at": datetime.utcnow()
    }

    # Create admin account
    result = users_collection.insert_one(admin_data)
    print(f"Admin account created successfully! ID: {result.inserted_id}")


if __name__ == "__main__":
    create_admin_account_sync()
