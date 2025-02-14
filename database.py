from pymongo import MongoClient
from bson import ObjectId
import datetime
import logging
from pymongo.errors import PyMongoError

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Подключение к MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
db = mongo_client["users_db"]
users_collection = db["users"]
registered_users_collection = db["registered_users"]
pending_requests_collection = db["pending_requests"]
attendance_collection = db["attendance"]

def init_db():
    """Инициализация индексов базы данных"""
    try:
        # Удаляем старые индексы при необходимости
        users_collection.drop_indexes()
        
        # Создаем новые уникальные индексы
        users_collection.create_index("id", unique=True)
        users_collection.create_index("username", unique=True)
        registered_users_collection.create_index("username", unique=True)
        pending_requests_collection.create_index("sender_id")
        pending_requests_collection.create_index("recipient_id")
        logger.info("Database indexes created successfully")
    except PyMongoError as e:
        logger.error(f"Error creating indexes: {e}")

def register_user(user_id: int, username: str) -> bool:
    """Регистрация/обновление пользователя с улучшенным логированием"""
    try:
        if not username:
            logger.warning(f"Empty username for user {user_id}")
            return False
            
        result = users_collection.update_one(
            {"id": user_id},
            {
                "$set": {"username": username},
                "$setOnInsert": {"id": user_id}
            },
            upsert=True
        )
        
        # Детальное логирование
        logger.info(
            f"User operation | ID: {user_id} | Username: {username} | "
            f"Matched: {result.matched_count} | Modified: {result.modified_count} | "
            f"Upserted: {bool(result.upserted_id)}"
        )
        return True
        
    except PyMongoError as e:
        logger.error(f"MongoDB error in register_user: {e}")
        return False

def find_user_by_username(username: str) -> dict | None:
    """Поиск пользователя по username"""
    try:
        return users_collection.find_one({"username": username})
    except PyMongoError as e:
        logger.error(f"Error finding user: {e}")
        return None

def create_pending_request(sender_id: int, recipient_id: int) -> str | None:
    """Создание запроса на подключение"""
    try:
        result = pending_requests_collection.insert_one({
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "status": "pending",
            "created_at": datetime.datetime.now()
        })
        logger.info(f"New request created: {result.inserted_id}")
        return str(result.inserted_id)
    except PyMongoError as e:
        logger.error(f"Error creating request: {e}")
        return None

def get_pending_request(request_id: str) -> dict | None:
    """Получение запроса по ID"""
    try:
        return pending_requests_collection.find_one({"_id": ObjectId(request_id)})
    except Exception as e:
        logger.error(f"Error getting request: {e}")
        return None

def update_pending_request(request_id: str, status: str) -> bool:
    """Обновление статуса запроса"""
    try:
        result = pending_requests_collection.update_one(
            {"_id": ObjectId(request_id)},
            {"$set": {"status": status}}
        )
        if result.modified_count > 0:
            logger.info(f"Request {request_id} updated to {status}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error updating request: {e}")
        return False

def save_attendance_data(sender_id: int, recipient_id: int, students: list) -> bool:
    """Сохранение данных о посещаемости"""
    try:
        attendance_collection.insert_one({
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "students": students,
            "created_at": datetime.datetime.now()
        })
        logger.info(f"Attendance data saved by {sender_id}")
        return True
    except PyMongoError as e:
        logger.error(f"Error saving attendance: {e}")
        return False