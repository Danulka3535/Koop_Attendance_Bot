from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from states import Form
from utils import create_keyboard, check_user_exists  # Импортируем check_user_exists

router = Router()

@router.message(Form.waiting_for_recipient_username)
async def process_recipient_username(message: Message, state: FSMContext, bot):  # Добавляем bot
    recipient_username = message.text.strip().lstrip("@")
    if not recipient_username.replace("_", "").isalnum() or len(recipient_username) < 5:
        await message.answer("❌ Некорректный формат username. Пример: @username")
        return

    exists, recipient_id = await check_user_exists(recipient_username, bot)  # Передаем bot
    if not exists:
        await message.answer(
            "❌ Пользователь не найден или аккаунт приватный.\n"
            "Убедитесь, что:\n"
            "1. Username введен правильно (например, @username)\n"
            "2. Пользователь уже начал диалог с ботом.\n"
            "3. Если username содержит символы `_` или `-`, попробуйте ввести его без них.\n"
            "Предложите пользователю перейти по ссылке: https://t.me/your_bot\n"
            "Если проблема persists, попробуйте позже или выберите другого получателя."
        )
        return

    await state.update_data(recipient_id=recipient_id, recipient_username=f"@{recipient_username}")
    await message.answer(
        f"✅ Вы выбрали получателя: {recipient_username}\nПодтвердите отправку данных:",
        reply_markup=create_keyboard(["Подтвердить", "Отменить"])
    )
    await state.set_state(Form.waiting_for_confirmation)

@router.message(Form.waiting_for_confirmation, F.text.in_(["Подтвердить", "Отменить"]))
async def confirm_action(message: Message, state: FSMContext):
    if message.text == "Отменить":
        await message.answer("Действие отменено.", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    data = await state.get_data()
    recipient_id = data.get("recipient_id")
    if not recipient_id:
        await message.answer("❌ Не удалось найти получателя. Попробуйте снова.")
        await state.clear()
        return

    try:
        await message.bot.send_message(  # Используем message.bot вместо глобального bot
            recipient_id,
            f"Вам хотят отправить данные по учету посещаемости от {message.from_user.full_name}. Принимаете?",
            reply_markup=create_keyboard(["Принять", "Отклонить"])
        )
    except TelegramBadRequest:
        await message.answer("❌ Не удалось связаться с получателем. Возможно, он заблокировал бота.")
        await state.clear()
        return

    await state.update_data(sender_id=message.from_user.id)
    await message.answer("Ожидание ответа от получателя...", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.waiting_for_recipient_response)