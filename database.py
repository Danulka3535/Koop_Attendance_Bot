# database.py
from pymongo import MongoClient

# Подключение к MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["users_db"]  # Создание базы данных
users_collection = db["users"]  # Коллекция пользователей
registered_users_collection = db["registered_users"]  # Коллекция зарегистрированных пользователей

def register_user(user_id, username):
    users_collection.update_one(
        {"id": user_id},
        {"$set": {"username": username}},
        upsert=True
    )

def find_user_by_username(username: str) -> dict | None:
    """
    Ищет пользователя по username в базе данных MongoDB.
    :param username: Username пользователя (без @)
    :return: Данные пользователя или None, если пользователь не найден
    """
    user = users_collection.find_one({"username": username})
    return user

def get_registered_users():
    """
    Возвращает список зарегистрированных пользователей.
    :return: Словарь {username: user_id}
    """
    users = registered_users_collection.find()
    return {user["username"]: user["id"] for user in users}