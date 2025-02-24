from pymongo import MongoClient
from typing import List, Dict, Optional
import datetime

client = MongoClient("mongodb://localhost:27017/")  # Замени на свой URI
db = client["attendance_bot"]

def init_db():
    groups_collection = db["groups"]
    students_collection = db["students"]
    headmen_collection = db["headmen"]
    
    if groups_collection.count_documents({}) == 0:
        groups = [
            {"name": "ИСП22-9"},
            {"name": "ИСП23-9"},
            {"name": "ИСП21-9"}
        ]
        groups_collection.insert_many(groups)
    
    if headmen_collection.count_documents({"group_name": "ИСП22-9"}) == 0:
        headmen_collection.insert_one({
            "telegram_id": 1196584113,  # Замени на реальный Telegram ID старосты
            "group_name": "ИСП22-9",
            "name": "Савин Роман Сергеевич"
        })

def get_groups() -> List[Dict]:
    groups_collection = db["groups"]
    return list(groups_collection.find({}))

def register_student(telegram_id: int, group_name: str, name: str):
    """Регистрация студента (только если не зарегистрирован)"""
    students_collection = db["students"]
    if students_collection.find_one({"telegram_id": telegram_id}):
        raise ValueError("Студент уже зарегистрирован. Данные нельзя изменить.")
    students_collection.insert_one({
        "telegram_id": telegram_id,
        "group_name": group_name,
        "name": name
    })

def is_student_registered(telegram_id: int) -> bool:
    """Проверка, зарегистрирован ли студент"""
    students_collection = db["students"]
    return bool(students_collection.find_one({"telegram_id": telegram_id}))

def register_curator(telegram_id: int, group_name: str):
    curators_collection = db["curators"]
    curators_collection.update_one(
        {"telegram_id": telegram_id},
        {"$set": {"telegram_id": telegram_id, "group_name": group_name}},
        upsert=True
    )

def register_headman(telegram_id: int, group_name: str, name: str):
    headmen_collection = db["headmen"]
    headmen_collection.update_one(
        {"telegram_id": telegram_id},
        {"$set": {"telegram_id": telegram_id, "group_name": group_name, "name": name}},
        upsert=True
    )

def get_students_by_group(group_name: str) -> List[Dict]:
    students_collection = db["students"]
    return list(students_collection.find({"group_name": group_name}))

def get_all_students() -> List[Dict]:
    students_collection = db["students"]
    return list(students_collection.find({}))

def get_curator_group(telegram_id: int) -> Optional[str]:
    curators_collection = db["curators"]
    curator = curators_collection.find_one({"telegram_id": telegram_id})
    return curator["group_name"] if curator else None

def get_headman_group(telegram_id: int) -> Optional[str]:
    headmen_collection = db["headmen"]
    headman = headmen_collection.find_one({"telegram_id": telegram_id})
    return headman["group_name"] if headman else None

def get_curator_id_by_group(group_name: str) -> Optional[int]:
    curators_collection = db["curators"]
    curator = curators_collection.find_one({"group_name": group_name})
    return curator["telegram_id"] if curator else None

def save_attendance(user_id: int, group_name: str, students: List[Dict], status: str):
    attendance_collection = db["attendance"]
    attendance_collection.insert_one({
        "user_id": user_id,
        "group_name": group_name,
        "students": students,
        "status": status,
        "timestamp": datetime.datetime.now().isoformat()
    })

def get_attendance_history(user_id: Optional[int]) -> List[Dict]:
    attendance_collection = db["attendance"]
    if user_id is None:
        history = list(attendance_collection.find({}))
    else:
        group_name = get_curator_group(user_id) or get_headman_group(user_id)
        history = list(attendance_collection.find({"group_name": group_name}))
    for entry in history:
        entry.pop("_id")
    return history

init_db()