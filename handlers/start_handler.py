# handlers/start_handler.py
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from database import register_user, get_registered_users
from states import Form

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, command: CommandObject, state: FSMContext):
    args = command.args
    if args and args.startswith("auth_"):
        unique_code = args[5:]
        AUTHORIZED_USERS = {}
        AUTHORIZED_USERS[message.from_user.id] = message.from_user.username
        await message.answer("Вы успешно зарегистрировались как получатель данных!")
        return

    register_user(message.from_user.id, message.from_user.username)
    registered_users = get_registered_users()  # Получаем зарегистрированных пользователей из базы данных
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"@{username}", callback_data=f"select:{user_id}")]
            for username, user_id in registered_users.items()
        ] + [
            [InlineKeyboardButton(text="Ввести вручную", callback_data="manual_input")]
        ]
    )
    await state.clear()
    await message.answer(
        "Привет! Давайте начнем учет посещаемости.\nКому вы хотите отправить эти данные? Введите username получателя (например, @username):",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Form.waiting_for_recipient_username)