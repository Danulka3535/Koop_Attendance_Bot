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

# Вставьте сюда ваш API Key (токен бота)
BOT_TOKEN = "YOUT_BOT_TOKEN"

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# FSM States
class Form(StatesGroup):
    waiting_for_recipient = State()
    waiting_for_confirmation = State()
    waiting_for_student_name = State()

# Utility function to create a keyboard
def create_keyboard(buttons):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=button)] for button in buttons],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# Start command handler
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()  # Clear any existing state
    await message.answer("Привет! Давайте начнем учет посещаемости.\nКому вы пытаетесь отправить эти данные?")
    await state.set_state(Form.waiting_for_recipient)

# Recipient username handler
@dp.message(Form.waiting_for_recipient)
async def process_recipient(message: Message, state: FSMContext):
    recipient_username = message.text.strip().lstrip("@")
    if not recipient_username:
        await message.answer("Пожалуйста, укажите корректный username получателя.")
        return

    try:
        recipient_id = (await bot.get_chat(f"@{recipient_username}")).id
    except TelegramBadRequest:
        await message.answer("Не удалось найти пользователя. Попробуйте снова.")
        return

    await state.update_data(recipient_id=recipient_id)
    await message.answer(
        f"Вы хотите отправить данные пользователю @{recipient_username}. Подтвердите действие.",
        reply_markup=create_keyboard(["Подтвердить", "Отменить"])
    )
    await state.set_state(Form.waiting_for_confirmation)

# Confirmation handler
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

# Recipient response handler
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

# Student name handler
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

# Finish input handler
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
