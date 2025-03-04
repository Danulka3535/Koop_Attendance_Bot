from pymongo import MongoClient
from config import MONGO_URI, MONGO_DB
from datetime import datetime, timedelta

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
tasks_collection = db["tasks"]

def add_task(user_id, task_text, priority="medium"):
    """Добавляет новую задачу с указанным приоритетом."""
    task = {
        "user_id": user_id,
        "text": task_text,
        "done": False,
        "priority": priority,  # low, medium, high
        "created_at": datetime.now(),
        "completed_at": None,
        "reminder_at": None
    }
    tasks_collection.insert_one(task)

def get_tasks(user_id, sort_by_priority=False):
    """Получает список задач пользователя, с опциональной сортировкой по приоритету."""
    query = {"user_id": user_id}
    if sort_by_priority:
        # Сортировка: high -> medium -> low
        return list(tasks_collection.find(query).sort([("priority", -1), ("created_at", 1)]))
    return list(tasks_collection.find(query).sort("created_at", 1))

def mark_task_done(user_id, task_id):
    """Отмечает задачу как выполненную."""
    tasks_collection.update_one(
        {"user_id": user_id, "_id": task_id},
        {"$set": {"done": True, "completed_at": datetime.now()}}
    )

def delete_task(user_id, task_id):
    """Удаляет задачу."""
    tasks_collection.delete_one({"user_id": user_id, "_id": task_id})

def clear_tasks(user_id):
    """Удаляет все задачи пользователя."""
    tasks_collection.delete_many({"user_id": user_id})

def set_task_reminder(user_id, task_id, seconds):
    """Устанавливает время напоминания для задачи."""
    reminder_time = datetime.now() + timedelta(seconds=seconds)
    tasks_collection.update_one(
        {"user_id": user_id, "_id": task_id},
        {"$set": {"reminder_at": reminder_time}}
    )

def edit_task(user_id, task_id, new_text):
    """Редактирует текст задачи."""
    tasks_collection.update_one(
        {"user_id": user_id, "_id": task_id},
        {"$set": {"text": new_text}}
    )

def set_task_priority(user_id, task_id, priority):
    """Устанавливает приоритет для задачи."""
    tasks_collection.update_one(
        {"user_id": user_id, "_id": task_id},
        {"$set": {"priority": priority}}
    )