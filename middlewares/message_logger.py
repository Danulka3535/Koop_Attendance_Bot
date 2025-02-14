# middlewares/message_logger.py
import datetime
from pathlib import Path
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update

class MessageLoggerMiddleware(BaseMiddleware):
    def __init__(self, log_file: str = "user_messages.txt"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(exist_ok=True, parents=True)

    async def __call__(self, handler, event: Update, data):
        # Проверяем, является ли событие сообщением или callback-запросом
        if isinstance(event, Message):
            user_id = event.from_user.id
            username = event.from_user.username
            text = event.text or "No text"
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            username = event.from_user.username
            text = event.data
        else:
            # Если событие не содержит from_user, пропускаем его
            return await handler(event, data)
        
        # Логируем информацию
        log_entry = (
            f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n"
            f"User ID: {user_id}\n"
            f"Username: @{username}\n"
            f"Message: {text}\n"
            "\n"
        )
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
        
        # Продолжаем обработку события
        return await handler(event, data)