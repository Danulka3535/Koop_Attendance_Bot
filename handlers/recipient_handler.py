from aiogram import Router, F, Bot
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from states import Form
from utils import create_keyboard, check_user_exists

router = Router()

@router.message(Form.waiting_for_recipient_username)
async def process_recipient(message: Message, state: FSMContext, bot: Bot):
    recipient_username = message.text.strip().lstrip('@')
    
    exists, recipient_id = await check_user_exists(recipient_username, bot)
    if not exists:
        await message.answer(
            "❌ Пользователь не найден или бот заблокирован.\n"
            "Попросите его перейти: https://t.me/YourBotName",
            parse_mode="Markdown"
        )
        return
    
    await state.update_data(recipient_id=recipient_id)
    await message.answer(
        f"✅ Получатель: @{recipient_username}\nПодтвердите отправку:",
        reply_markup=create_keyboard(["Подтвердить", "Отменить"])
    )
    await state.set_state(Form.waiting_for_confirmation)

@router.message(Form.waiting_for_confirmation, F.text.in_(["Подтвердить", "Отменить"]))
async def confirm_sending(message: Message, state: FSMContext, bot: Bot):
    if message.text == "Отменить":
        await message.answer("❌ Отменено.", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return
    
    data = await state.get_data()
    recipient_id = data["recipient_id"]
    
    try:
        await bot.send_message(
            recipient_id,
            "📨 Вам отправлены данные. Принять?",
            reply_markup=create_keyboard(["Принять", "Отклонить"])
        )
        await message.answer("✅ Запрос отправлен. Ожидайте ответа.")
        await state.set_state(Form.waiting_for_recipient_response)
    except TelegramBadRequest:
        await message.answer("❌ Получатель не доступен.")
        await state.clear()