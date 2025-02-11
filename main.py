# main.py
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from middlewares.message_logger import MessageLoggerMiddleware  # Импорт мидлвари
from handlers import (
    start_handler,
    recipient_handler,
    student_handler,
    photo_handler,
    help_handler
)
from database import init_db
from handlers import start_handler, recipient_handler, response_handler

logging.basicConfig(level=logging.INFO)

bot = Bot(token="ВАШ_ТОКЕН")
dp = Dispatcher(storage=MemoryStorage())

init_db()

dp.include_router(start_handler.router)
dp.include_router(recipient_handler.router)
dp.include_router(response_handler.router)

if __name__ == "__main__":
    dp.run_polling(bot)