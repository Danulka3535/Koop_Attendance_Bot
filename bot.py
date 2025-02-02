from dotenv import load_dotenv
load_dotenv()
import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramBadRequest

# Настройка логирования
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "7833684593:AAFS5kf94T15kT9cd9DNmk-__tz4oRu8nBc"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class Form(StatesGroup):
    waiting_for_recipient = State()
    waiting_for_confirmation = State()
    waiting_for_student_name = State()

def create_keyboard(buttons):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=button)] for button in buttons],
        resize_keyboard=True,
        one_time_keyboard=True
    )

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Привет! Давайте начнем учет посещаемости.\nКому вы пытаетесь отправить эти данные?")
    await state.set_state(Form.waiting_for_recipient)

# ОБНОВЛЕННЫЙ БЛОК НАЧИНАЕТСЯ ЗДЕСЬ
@dp.message(Form.waiting_for_recipient)
async def process_recipient(message: Message, state: FSMContext):
    recipient_username = message.text.strip().lstrip("@")
    
    # Проверка формата username
    if not recipient_username.isalnum() or len(recipient_username) < 5:
        await message.answer("❌ Некорректный формат username. Пример: @username")
        return

    try:
        # Пытаемся получить информацию о пользователе
        chat = await bot.get_chat(f"@{recipient_username}")
        if chat.type != "private":
            await message.answer("❌ Это не личный аккаунт. Введите username пользователя.")
            return
            
        recipient_id = chat.id
    except TelegramBadRequest as e:
        logging.error(f"Ошибка поиска пользователя: {e}")
        await message.answer("❌ Пользователь не найден или аккаунт приватный. Убедитесь, что:")
        await message.answer("1. Username введен правильно (например, @username)")
        await message.answer("2. Пользователь не скрыл username в настройках приватности")
        return
    except Exception as e:
        logging.error(f"Неизвестная ошибка: {e}")
        await message.answer("🚫 Произошла непредвиденная ошибка. Попробуйте позже.")
        return

    await state.update_data(recipient_id=recipient_id)
    await message.answer(
        f"✅ Вы выбрали: @{recipient_username}\nПодтвердите отправку данных:",
        reply_markup=create_keyboard(["Подтвердить", "Отменить"])
    )
    await state.set_state(Form.waiting_for_confirmation)
# ОБНОВЛЕННЫЙ БЛОК ЗАКАНЧИВАЕТСЯ ЗДЕСЬ

@dp.message(Form.waiting_for_confirmation, F.text.in_(["Подтвердить", "Отменить"]))
async def confirm_action(message: Message, state: FSMContext):
    if message.text == "Отменить":
        await message.answer("Действие отменено.", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    data = await state.get_data()
    recipient_id = data.get("recipient_id")
    if not recipient_id:
        await message.answer("Ошибка: не найден получатель.")
        await state.clear()
        return

    await bot.send_message(
        recipient_id,
        "Вам хотят отправить данные по учету посещаемости. Принимаете?",
        reply_markup=create_keyboard(["Принять", "Отклонить"])
    )
    await state.update_data(sender_id=message.from_user.id)
    await state.set_state(Form.waiting_for_student_name)

@dp.message(F.text.in_(["Принять", "Отклонить"]))
async def recipient_response(message: Message, state: FSMContext):
    if message.text == "Отклонить":
        sender_data = await state.get_data()
        sender_id = sender_data.get("sender_id")
        if sender_id:
            await bot.send_message(sender_id, "Получатель отклонил ваш запрос.", reply_markup=ReplyKeyboardRemove())
        await message.answer("Вы отклонили запрос.", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    await message.answer("Вы приняли запрос. Ожидайте данные.", reply_markup=ReplyKeyboardRemove())
    sender_data = await state.get_data()
    sender_id = sender_data.get("sender_id")
    if sender_id:
        await bot.send_message(sender_id, "Получатель принял ваш запрос. Можете начинать вводить данные.", reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.waiting_for_student_name)

@dp.message(Form.waiting_for_student_name)
async def process_student_name(message: Message, state: FSMContext):
    student_name = message.text.strip()
    if not student_name:
        await message.answer("Пожалуйста, введите корректное ФИО.")
        return

    data = await state.get_data()
    students = data.get("students", [])
    students.append(student_name)
    await state.update_data(students=students)

    await message.answer(
        "Успешно добавлено!\nНужно ли еще кого-то добавить?",
        reply_markup=create_keyboard(["Добавить", "Завершить"])
    )

@dp.message(Form.waiting_for_student_name, F.text.in_(["Добавить", "Завершить"]))
async def finish_input(message: Message, state: FSMContext):
    if message.text == "Добавить":
        await message.answer("Введите ФИО следующего ученика:")
        return

    data = await state.get_data()
    students = data.get("students", [])
    recipient_id = data.get("recipient_id")

    if not students:
        await message.answer("Список учеников пуст. Нечего отправлять.", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    student_list = "\n".join(students)
    await bot.send_message(recipient_id, f"Список учеников:\n{student_list}")
    await message.answer("Данные успешно отправлены!", reply_markup=ReplyKeyboardRemove())
    await state.clear()

if __name__ == "__main__":
    dp.run_polling(bot)
