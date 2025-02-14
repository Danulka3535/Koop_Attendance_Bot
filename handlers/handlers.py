from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram import Bot
from aiogram.fsm.storage.base import StorageKey
from states import Form
from database import create_pending_request, get_pending_request, update_pending_request, save_attendance_data
from utils import check_user_exists, create_keyboard, create_inline_keyboard
import datetime
import logging

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await message.answer("Привет! Давайте начнем учет посещаемости.\nКому вы хотите отправить эти данные? Введите username получателя (например, @username):")
    await state.set_state(Form.waiting_for_recipient_username)

@router.message(Form.waiting_for_recipient_username)
async def process_recipient_username(message: Message, state: FSMContext, bot: Bot):
    recipient_username = message.text.strip().lstrip('@')
    exists, user_id = await check_user_exists(recipient_username, bot)
    
    if not exists or user_id is None:
        await message.answer("❌ Пользователь не найден. Введите правильный username:")
        return
    
    request_id = create_pending_request(message.from_user.id, user_id)
    await state.update_data(recipient_id=user_id, request_id=str(request_id))
    
    buttons = [("Принять", f"accept_{request_id}"), ("Отклонить", f"decline_{request_id}")]
    await bot.send_message(
        chat_id=user_id,
        text=f"🔔 Пользователь @{message.from_user.username} хочет отправить вам данные посещаемости. Подтвердите запрос:",
        reply_markup=create_inline_keyboard(buttons)
    )
    await message.answer("✅ Запрос отправлен. Ожидаем подтверждения...")
    await state.set_state(Form.waiting_for_confirmation)

@router.callback_query(F.data.startswith("accept_") | F.data.startswith("decline_"))
async def handle_confirmation(
    callback: CallbackQuery, 
    bot: Bot,
    state: FSMContext
):
    try:
        # Преобразуем время callback в offset-naive (без временной зоны)
        callback_time = callback.message.date.replace(tzinfo=None)
        current_time = datetime.datetime.now()  # Текущее время (offset-naive)

        # Проверка на устаревший callback (более 48 часов)
        if (current_time - callback_time).total_seconds() > 172800:
            await callback.answer("❌ Время ответа истекло!")
            return

        action, request_id = callback.data.split("_", 1)
        request = get_pending_request(request_id)
        
        if not request:
            await callback.answer("⚠️ Запрос не найден!")
            return
            
        if callback.from_user.id != request["recipient_id"]:
            await callback.answer("⚠️ Вы не получатель!")
            return
            
        # Обновляем статус запроса
        update_pending_request(request_id, "accepted" if action == "accept" else "rejected")
        
        # Получаем storage из текущего состояния
        storage = state.storage
        
        # Управление состоянием отправителя
        sender_id = request["sender_id"]
        sender_state = FSMContext(
            storage=storage,
            key=StorageKey(chat_id=sender_id, user_id=sender_id, bot_id=bot.id)
        )
        
        if action == "accept":
            await sender_state.set_state(Form.waiting_for_student_name)
            await bot.send_message(sender_id, "✅ Введите ФИО учащегося:")
        else:
            await sender_state.set_state(Form.waiting_for_recipient_username)
            await bot.send_message(sender_id, "❌ Введите новый username:")
            
        await callback.answer()
        await callback.message.delete()
        
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await callback.answer("⚠️ Ошибка обработки!")

@router.message(Form.waiting_for_student_name)
async def process_student_name(message: Message, state: FSMContext):
    student_name = message.text.strip()
    data = await state.get_data()
    students = data.get("students", [])
    students.append(student_name)
    
    await state.update_data(students=students)
    await message.answer(f"👤 Добавлен: {student_name}\nДобавить ещё или завершить?",
                        reply_markup=create_keyboard(["Добавить", "Завершить"]))
    await state.set_state(Form.waiting_for_add_more)

@router.message(Form.waiting_for_add_more)
async def process_add_more(message: Message, state: FSMContext, bot: Bot):
    if message.text == "Добавить":
        await message.answer("Введите ФИО следующего учащегося:")
        await state.set_state(Form.waiting_for_student_name)
    elif message.text == "Завершить":
        data = await state.get_data()
        students = data.get("students", [])
        
        if not students:
            await message.answer("❌ Список пуст! Начните заново.")
            await state.clear()
            return
            
        save_attendance_data(
            sender_id=message.from_user.id,
            recipient_id=data["recipient_id"],
            students=students
        )
        
        await bot.send_message(
            data["recipient_id"],
            f"📊 Данные от @{message.from_user.username}:\n" + "\n".join(f"• {s}" for s in students)
        )
        
        await message.answer("✅ Данные отправлены!")
        await state.clear()