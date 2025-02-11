from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from states import Form

router = Router()

@router.message(Form.waiting_for_recipient_response, F.text.in_(["Принять", "Отклонить"]))
async def handle_response(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    sender_id = data.get("sender_id")
    
    if message.text == "Принять":
        await bot.send_message(
            sender_id,
            "✅ Получатель принял ваш запрос!",
            reply_markup=ReplyKeyboardRemove()
        )
        # Отправка данных (добавьте свою логику)
    else:
        await bot.send_message(sender_id, "❌ Запрос отклонен.")
    
    await state.clear()