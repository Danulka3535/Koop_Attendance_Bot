import logging
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from database import find_user_by_username

def create_keyboard(buttons):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=button)] for button in buttons],
        resize_keyboard=True,
        one_time_keyboard=True
    )

async def check_user_exists(username: str, bot):  # Добавляем bot как параметр
    """
    Проверяет существование пользователя через Telegram API.
    """
    # Проверка в базе данных
    user = find_user_by_username(username)
    if user:
        return True, user["id"]

    # Проверка через API Telegram
    try:
        chat = await bot.get_chat(f"@{username}")
        if chat.type == "private":
            return True, chat.id
        logging.warning(f"Пользователь @{username} найден, но это не личный чат.")
        return False, None
    except Exception as e:
        if "chat not found" in str(e).lower():
            logging.error(f"Ошибка при проверке пользователя {username}: Пользователь не найден.")
            return False, None
        logging.error(f"Ошибка при проверке пользователя {username}: {e}")
        return False, None