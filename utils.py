import logging
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from database import find_user_by_username

def create_keyboard(buttons):
    """Создает клавиатуру с кнопками."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn)] for btn in buttons],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def create_inline_keyboard(buttons: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    """Создает инлайн-клавиатуру из списка кнопок (текст, callback_data)"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data=data) for text, data in buttons]
    ])

async def check_user_exists(username: str, bot) -> tuple[bool, int | None]:
    username = username.lstrip('@')
    # Проверка в базе данных
    user = find_user_by_username(username)
    if user:
        return True, user["id"]
    try:
        # Проверка через Telegram API
        chat = await bot.get_chat(f"@{username}")
        if chat.type != "private":
            return False, None
        # Проверка возможности отправки сообщений
        await bot.send_chat_action(chat.id, "typing")
        return True, chat.id
    except TelegramBadRequest as e:
        if "user not found" in str(e).lower():
            return False, None
        elif "bot was blocked" in str(e).lower():
            return False, None
        else:
            logging.error(f"Ошибка: {e}")
            return False, None
    except Exception as e:
        logging.error(f"Неизвестная ошибка: {e}")
        return False, None