from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def check_user_exists_by_id(user_id: int, bot: Bot) -> bool:
    try:
        await bot.send_chat_action(user_id, "typing")
        return True
    except:
        return False

def create_inline_keyboard(buttons: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text=text, callback_data=data)]
        for text, data in buttons
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)