from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage  # Импорт MemoryStorage
from middlewares.message_logger import MessageLoggerMiddleware
from handlers import router  # Импорт роутера из handlers.py
from database import init_db
from config import BOT_TOKEN
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация хранилища состояний
storage = MemoryStorage()  # Определяем storage

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)  # Передаем storage в диспетчер

# Инициализация базы данных
init_db()

# Подключение мидлвари
dp.update.outer_middleware(MessageLoggerMiddleware())

# Подключение роутера
dp.include_router(router)

# Запуск бота
if __name__ == "__main__":
    dp.run_polling(bot)