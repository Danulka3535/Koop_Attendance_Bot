import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from middlewares.message_logger import MessageLoggerMiddleware  # Импорт мидлвари
from handlers import (
    start_handler,
    recipient_handler,
    student_handler,
    photo_handler
)
from database import init_db
from handlers import help_handler 

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "Твой_Токен_Дружище"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Подключение мидлвари
dp.message.middleware(MessageLoggerMiddleware())

# Инициализация базы данных
init_db()

# Регистрация обработчиков
dp.include_router(start_handler.router)
dp.include_router(recipient_handler.router)
dp.include_router(student_handler.router)
dp.include_router(photo_handler.router)
dp.include_router(help_handler.router)

if __name__ == "__main__":
    dp.run_polling(bot)
