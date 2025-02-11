from pymongo import MongoClient

mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["users_db"]
users_collection = db["users"]
registered_users_collection = db["registered_users"]

def init_db():
    users_collection.create_index("id", unique=True)
    users_collection.create_index("username", unique=True)
    registered_users_collection.create_index("username", unique=True)

def register_user(user_id, username):
    users_collection.update_one(
        {"id": user_id},
        {"$set": {"username": username}},
        upsert=True
    )

def find_user_by_username(username: str) -> dict | None:
    return users_collection.find_one({"username": username})