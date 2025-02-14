from pymongo import MongoClient
from bson import ObjectId  # Добавлен импорт ObjectId
import datetime
import logging  # Добавлен импорт logging
from pymongo.errors import PyMongoError

mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["users_db"]
users_collection = db["users"]
registered_users_collection = db["registered_users"]
pending_requests_collection = db["pending_requests"]  # Коллекция для запросов
attendance_collection = db["attendance"]  # Коллекция для данных о посещаемости

def init_db():
    users_collection.create_index("id", unique=True)
    users_collection.create_index("username", unique=True)
    registered_users_collection.create_index("username", unique=True)
    pending_requests_collection.create_index("sender_id")
    pending_requests_collection.create_index("recipient_id")

def register_user(user_id, username):
    users_collection.update_one(
        {"id": user_id},
        {"$set": {"username": username}},
        upsert=True
    )

def find_user_by_username(username: str) -> dict | None:
    return users_collection.find_one({"username": username})

def create_pending_request(sender_id, recipient_id) -> str:
    """Создает запрос и возвращает его ID в виде строки."""
    result = pending_requests_collection.insert_one({
        "sender_id": sender_id,
        "recipient_id": recipient_id,
        "status": "pending",
        "created_at": datetime.datetime.now()
    })
    return str(result.inserted_id)  # Возвращаем ID как строку

def get_pending_request(request_id: str) -> dict | None:
    """Получает запрос по его ID."""
    try:
        # Преобразуем request_id в ObjectId
        return pending_requests_collection.find_one({"_id": ObjectId(request_id)})
    except Exception as e:
        logging.error(f"Ошибка при поиске запроса: {e}")
        return None

def update_pending_request(request_id: str, status: str):
    """Обновляет статус запроса."""
    try:
        pending_requests_collection.update_one(
            {"_id": ObjectId(request_id)},
            {"$set": {"status": status}}
        )
    except Exception as e:
        logging.error(f"Ошибка при обновлении запроса: {e}")

def save_attendance_data(sender_id, recipient_id, students):
    """Сохраняет данные о посещаемости."""
    attendance_collection.insert_one({
        "sender_id": sender_id,
        "recipient_id": recipient_id,
        "students": students,
        "created_at": datetime.datetime.now()
    })

def get_pending_request(request_id: str):
    try:
        return pending_requests_collection.find_one({"_id": ObjectId(request_id)})
    except PyMongoError as e:
        logging.error(f"DB error: {e}")
        return None