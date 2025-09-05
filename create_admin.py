import asyncio
from datetime import datetime
from services.auth_service import hash_password
from db import get_database


async def create_admin_account():
    db = get_database()
    users_collection = db["users"]

    admin_data = {
        "name": "Manoj Admin User",
        "email": "manojmottyar@gmail.com",  # Change this to your admin email
        "password": hash_password("#Pooja1509"),  # Change this password!
        "role": "admin",
        "created_at": datetime.utcnow()
    }

    # Check if admin already exists
    existing_admin = await users_collection.find_one({"email": admin_data["email"]})
    if existing_admin:
        print("Admin account already exists!")
        return

    # Create admin account
    result = await users_collection.insert_one(admin_data)
    print(f"Admin account created successfully! ID: {result.inserted_id}")

if __name__ == "__main__":
    asyncio.run(create_admin_account())
