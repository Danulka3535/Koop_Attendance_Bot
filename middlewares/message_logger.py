import datetime
from pathlib import Path
from aiogram import BaseMiddleware
from aiogram.types import Message

class MessageLoggerMiddleware(BaseMiddleware):
    def __init__(self, log_file: str = "user_messages.txt"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(exist_ok=True, parents=True)

    async def __call__(self, handler, event: Message, data):
        # Запись сообщения в файл
        log_entry = (
            f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n"
            f"User ID: {event.from_user.id}\n"
            f"Username: @{event.from_user.username}\n"
            f"Message: {event.text}\n"
            "-----------------------------\n"
        )

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)

        return await handler(event, data)