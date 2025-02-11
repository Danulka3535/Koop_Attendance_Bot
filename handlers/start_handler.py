from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from utils import create_keyboard
from states import Form

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await message.answer(
        "Привет! Давайте начнем учет посещаемости.\n"
        "Кому вы хотите отправить данные? Введите username:",
        reply_markup=create_keyboard(["Отмена"])
    )
    await state.set_state(Form.waiting_for_recipient_username)