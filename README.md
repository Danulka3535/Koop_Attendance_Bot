
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties  # Импортируем DefaultBotProperties

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Токен вашего бота
API_TOKEN = 'YOUR_TOKEN'

# Инициализация бота с использованием DefaultBotProperties
bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)  # Указываем parse_mode здесь
)
dp = Dispatcher()

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Привет! Я твой бот. Напиши мне что-нибудь, и я повторю это.")

# Обработчик текстовых сообщений
@dp.message()
async def echo(message: Message):
    await message.answer(f"Вы написали: {message.text}")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
