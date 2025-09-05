# test_connection_final.py
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from urllib.parse import quote_plus

username = quote_plus('manojmottyar_db_user')
password = quote_plus('EIriG6lD7WOYziiI')

# Your connection string
connection_string = f"mongodb+srv://{username}:{password}@manosaycluster.rn8atty.mongodb.net/?retryWrites=true&w=majority&appName=ManoSayCluster"

try:
    print("Testing connection after IP whitelist...")
    
    client = MongoClient(
        connection_string,
        server_api=ServerApi('1'),
        serverSelectionTimeoutMS=10000
    )
    
    # Test the connection
    client.admin.command('ping')
    print("✅ SUCCESS: Connected to MongoDB Atlas!")
    
    # Show available databases
    databases = client.list_database_names()
    print(f"Available databases: {databases}")
    
    # Test your specific database
    db = client['myDatabase']
    collections = db.list_collection_names()
    print(f"Collections in myDatabase: {collections}")
    
    client.close()
    print("Connection test completed successfully!")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")