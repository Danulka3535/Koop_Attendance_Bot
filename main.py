from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from middlewares.message_logger import MessageLoggerMiddleware
from handlers import router
from database import init_db
from config import BOT_TOKEN
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация хранилища состояний
storage = MemoryStorage()

try:
    # Проверка подключения к MongoDB
    init_db()
    logging.info("Successfully connected to MongoDB")
except Exception as e:
    logging.critical(f"MongoDB connection failed: {e}")
    exit(1)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

# Подключение мидлвари
dp.update.outer_middleware(MessageLoggerMiddleware())

# Подключение роутера
dp.include_router(router)

# Запуск бота
if __name__ == "__main__":
    dp.run_polling(bot)