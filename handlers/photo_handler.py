from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from states import Form

router = Router()

@router.message(Form.waiting_for_schedule_photo, F.photo)
async def handle_schedule_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    recipient_id = data.get("recipient_id")
    photo_id = message.photo[-1].file_id  # ID фото в высоком качестве

    try:
        await message.bot.send_photo(
            chat_id=recipient_id,
            photo=photo_id,
            caption="📅 Расписание"
        )
        await message.answer("✅ Расписание успешно отправлено!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
    
    await state.clear()