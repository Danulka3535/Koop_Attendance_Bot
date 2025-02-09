# handlers/schedule_handler.py
from aiogram import Router
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from states import Form

def create_schedule_router(bot):
    router = Router()

    @router.message(Form.waiting_for_schedule)
    async def process_schedule(message: Message, state: FSMContext):
        schedule = message.text.strip()
        if not schedule:
            await message.answer("❌ Пожалуйста, введите корректное расписание.")
            return

        data = await state.get_data()
        recipient_id = data.get("recipient_id")
        try:
            await bot.send_message(recipient_id, f"Расписание:\n{schedule}")
        except TelegramBadRequest:
            await message.answer("❌ Не удалось отправить расписание получателю. Возможно, он заблокировал бота.")
            await state.clear()
            return

        await message.answer("Расписание успешно отправлено!", reply_markup=ReplyKeyboardRemove())
        await state.clear()

    return router