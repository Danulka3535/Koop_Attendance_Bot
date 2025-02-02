from dotenv import load_dotenv
load_dotenv()

import os
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramBadRequest

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Загрузка токена из переменной окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден! Проверьте .env файл.")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Создание базы данных пользователей
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT
    )
""")
conn.commit()

# Регистрация нового пользователя
def register_user(user_id, username):
    cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()

# Поиск пользователя по username
def find_user_by_username(username):
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    return result[0] if result else None

# Список заранее зарегистрированных получателей
REGISTERED_USERS = {
    "user1": 123456789,  # username: user_id
    "user2": 987654321,
}

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

async def check_user_exists(username: str) -> tuple[bool, str | None]:
    """
    Проверяет, существует ли пользователь с указанным username.
    
    :param username: Username пользователя (без @)
    :return: Кортеж (существует ли пользователь, ID пользователя или None)
    """
    try:
        escaped_username = username.replace("_", "\\_")  # Экранируем специальные символы
        chat = await bot.get_chat(f"@{escaped_username}")
        if chat.type == "private":
            return True, chat.id  # Пользователь найден, возвращаем его ID
        logging.warning(f"Пользователь @{username} найден, но это не личный чат.")
        return False, None  # Это не личный аккаунт
    except Exception as e:
        if "chat not found" in str(e).lower():
            logging.error(f"Ошибка при проверке пользователя {username}: Пользователь не найден.")
            return False, None  # Пользователь не найден
        logging.error(f"Ошибка при проверке пользователя {username}: {e}")
        return False, None  # Другая ошибка

@dp.message(Command("start"))
async def cmd_start(message: Message, command: CommandObject, state: FSMContext):
    args = command.args
    
    if args and args.startswith("auth_"):
        unique_code = args[5:]
        AUTHORIZED_USERS = {}
        AUTHORIZED_USERS[message.from_user.id] = message.from_user.username
        await message.answer("Вы успешно зарегистрировались как получатель данных!")
        return
    
    register_user(message.from_user.id, message.from_user.username)
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"@{username}", callback_data=f"select:{user_id}")]
            for username, user_id in REGISTERED_USERS.items()
        ] + [
            [InlineKeyboardButton(text="Ввести вручную", callback_data="manual_input")]
        ]
    )
    
    await state.clear()
    await message.answer(
        "Привет! Давайте начнем учет посещаемости.\nВыберите получателя данных или введите вручную:",
        reply_markup=keyboard
    )

@dp.callback_query(F.data.startswith("select:"))
async def select_recipient(callback: CallbackQuery, state: FSMContext):
    recipient_id = int(callback.data.split(":")[1])
    if not recipient_id:
        await callback.answer("Пользователь не найден.")
        return
    
    await state.update_data(recipient_id=recipient_id)
    await callback.message.edit_text(
        f"✅ Вы выбрали получателя с ID: {recipient_id}\nПодтвердите отправку данных:",
        reply_markup=create_keyboard(["Подтвердить", "Отменить"])
    )
    await state.set_state(Form.waiting_for_confirmation)

@dp.callback_query(F.data == "manual_input")
async def manual_input(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите username получателя (например, @username):")
    await state.set_state(Form.waiting_for_recipient)

@dp.message(Form.waiting_for_recipient)
async def process_recipient(message: Message, state: FSMContext):
    recipient_username = message.text.strip().lstrip("@")
    
    if not recipient_username.replace("_", "").isalnum() or len(recipient_username) < 5:
        await message.answer("❌ Некорректный формат username. Пример: @username")
        return
    
    # Проверяем наличие в заранее зарегистрированных пользователях
    for user_id, username in REGISTERED_USERS.items():
        if username == recipient_username:
            await state.update_data(recipient_id=user_id)
            await message.answer(
                f"✅ Вы выбрали: @{recipient_username}\nПодтвердите отправку данных:",
                reply_markup=create_keyboard(["Подтвердить", "Отменить"])
            )
            await state.set_state(Form.waiting_for_confirmation)
            return
    
    # Проверяем в базе данных
    recipient_id = find_user_by_username(recipient_username)
    if recipient_id:
        await state.update_data(recipient_id=recipient_id)
        await message.answer(
            f"✅ Вы выбрали: @{recipient_username}\nПодтвердите отправку данных:",
            reply_markup=create_keyboard(["Подтвердить", "Отменить"])
        )
        await state.set_state(Form.waiting_for_confirmation)
        return
    
    # Автоматическое исправление username
    if "_" in recipient_username or "-" in recipient_username:
        corrected_username = recipient_username.replace("_", "").replace("-", "")
        await message.answer(
            f"⚠️ Username содержит специальные символы. Попробуем найти пользователя без них: @{corrected_username}."
        )
        exists, recipient_id = await check_user_exists(corrected_username)
        if exists:
            await state.update_data(recipient_id=recipient_id)
            await message.answer(
                f"✅ Вы выбрали: @{corrected_username}\nПодтвердите отправку данных:",
                reply_markup=create_keyboard(["Подтвердить", "Отменить"])
            )
            await state.set_state(Form.waiting_for_confirmation)
            return
    
    # Проверяем через API
    exists, recipient_id = await check_user_exists(recipient_username)
    if exists:
        await state.update_data(recipient_id=recipient_id)
        await message.answer(
            f"✅ Вы выбрали: @{recipient_username}\nПодтвердите отправку данных:",
            reply_markup=create_keyboard(["Подтвердить", "Отменить"])
        )
        await state.set_state(Form.waiting_for_confirmation)
        return
    
    # Если пользователь не найден
    await message.answer(
        "❌ Пользователь не найден или аккаунт приватный.\n"
        "Убедитесь, что:\n"
        "1. Username введен правильно (например, @username)\n"
        "2. Пользователь уже начал диалог с ботом.\n"
        "3. Пользователь не менял свой username недавно.\n"
        "4. Если username содержит символы `_` или `-`, попробуйте ввести его без них.\n"
        "Предложите пользователю перейти по ссылке: https://t.me/your_bot\n"
        "Если проблема persists, попробуйте позже или выберите другого получателя."
    )

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
    
    try:
        await bot.send_message(
            recipient_id,
            "Вам хотят отправить данные по учету посещаемости. Принимаете?",
            reply_markup=create_keyboard(["Принять", "Отклонить"])
        )
    except TelegramBadRequest:
        await message.answer("❌ Не удалось связаться с получателем. Возможно, он заблокировал бота.")
        await state.clear()
        return
    
    await state.update_data(sender_id=message.from_user.id)
    await state.set_state(Form.waiting_for_student_name)

@dp.message(F.text.in_(["Принять", "Отклонить"]))
async def recipient_response(message: Message, state: FSMContext):
    if message.text == "Отклонить":
        sender_data = await state.get_data()
        sender_id = sender_data.get("sender_id")
        if sender_id:
            try:
                await bot.send_message(sender_id, "Получатель отклонил ваш запрос.", reply_markup=ReplyKeyboardRemove())
            except TelegramBadRequest:
                pass
        await message.answer("Вы отклонили запрос.", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return
    
    await message.answer("Вы приняли запрос. Ожидайте данные.", reply_markup=ReplyKeyboardRemove())
    sender_data = await state.get_data()
    sender_id = sender_data.get("sender_id")
    if sender_id:
        try:
            await bot.send_message(sender_id, "Получатель принял ваш запрос. Можете начинать вводить данные.", reply_markup=ReplyKeyboardRemove())
        except TelegramBadRequest:
            pass
        await state.set_state(Form.waiting_for_student_name)

@dp.message(Form.waiting_for_student_name)
async def process_student_name(message: Message, state: FSMContext):
    if message.text in ["Завершить", "Добавить"]:
        return
    
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
    
    student_list = "\n".join([f"{i+1}. {student}" for i, student in enumerate(students)])
    
    try:
        await bot.send_message(recipient_id, f"Список учеников:\n{student_list}")
    except TelegramBadRequest:
        await message.answer("❌ Не удалось отправить данные получателю. Возможно, он заблокировал бота.")
        await state.clear()
        return
    
    await message.answer("Данные успешно отправлены!", reply_markup=ReplyKeyboardRemove())
    await state.clear()

if __name__ == "__main__":
    dp.run_polling(bot)
