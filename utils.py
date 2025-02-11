import logging
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.exceptions import TelegramBadRequest
from database import find_user_by_username

def create_keyboard(buttons):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn)] for btn in buttons],
        resize_keyboard=True,
        one_time_keyboard=True
    )

async def check_user_exists(username: str, bot) -> tuple[bool, int | None]:
    username = username.lstrip('@')
    
    # Проверка в базе данных
    user = find_user_by_username(username)
    if user:
        return True, user["id"]
    
    # Проверка через Telegram API
    try:
        chat = await bot.get_chat(f"@{username}")
        if chat.type != "private":
            return False, None
            
        # Проверка возможности отправки сообщений
        await bot.send_chat_action(chat.id, "typing")
        return True, chat.id
    except TelegramBadRequest as e:
        logging.error(f"Ошибка: {e}")
        return False, None