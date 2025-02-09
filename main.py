import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import (
    start_handler,
    recipient_handler,
    student_handler,
    photo_handler
)
from database import init_db

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "Твой_Токен_Дружище"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

init_db()

dp.include_router(start_handler.router)
dp.include_router(recipient_handler.router)
dp.include_router(student_handler.router)
dp.include_router(photo_handler.router)

if __name__ == "__main__":
    dp.run_polling(bot)