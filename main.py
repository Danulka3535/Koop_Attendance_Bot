from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import router
import asyncio
import logging

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token="7664076869:AAF02jlQCnD7NRVI1v-z9A4uFhIcbClq-bQ")  # Замени на свой токен
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())