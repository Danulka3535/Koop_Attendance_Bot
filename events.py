from aiogram import types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from datetime import datetime, timedelta

# Список для хранения напоминалок (временное решение)
reminders = []
reviews = []

# Обработчик команды /add_reminder
async def add_reminder(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Через 1 день"))
    builder.add(types.KeyboardButton(text="Через 3 дня"))
    builder.add(types.KeyboardButton(text="Через 7 дней"))
    builder.adjust(2)  # Располагаем кнопки в 2 колонки

    await message.answer(
        "Выбери, через сколько дней напомнить:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

# Обработчик выбора времени напоминания
async def handle_reminder_time(message: types.Message):
    try:
        # Получаем выбранное время
        time_text = message.text
        if time_text == "Через 1 день":
            delta = timedelta(days=1)
        elif time_text == "Через 3 дня":
            delta = timedelta(days=3)
        elif time_text == "Через 7 дней":
            delta = timedelta(days=7)
        else:
            await message.answer("Пожалуйста, выбери время из предложенных вариантов.")
            return

        # Добавляем напоминание
        reminder_time = datetime.now() + delta
        reminders.append((message.from_user.id, reminder_time))
        await message.answer(f"Напоминание установлено на {reminder_time.strftime('%Y-%m-%d %H:%M')}.")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

# Обработчик команды /add_review
async def add_review(message: types.Message):
    await message.answer("Напиши свой отзыв о игре:")

# Обработчик текстового сообщения с отзывом
async def handle_review(message: types.Message):
    reviews.append((message.from_user.id, message.text))
    await message.answer("Спасибо за твой отзыв! Он был сохранен.")

# Обработчик команды /view_reviews
async def view_reviews(message: types.Message):
    if not reviews:
        await message.answer("Пока нет отзывов.")
        return

    response = "Последние отзывы:\n"
    for user_id, review in reviews[-5:]:  # Показываем последние 5 отзывов
        response += f"- {review}\n"
    await message.answer(response)

# Обработчик команды /poll
async def create_poll(message: types.Message):
    await message.answer_poll(
        question="Какая игра года?",
        options=["Elden Ring", "God of War: Ragnarok", "Horizon Forbidden West", "Другая"],
        is_anonymous=False
    )

# Функция для регистрации обработчиков
def register_events(dp):
    dp.message.register(add_reminder, Command("add_reminder"))
    dp.message.register(handle_reminder_time, F.text.in_(["Через 1 день", "Через 3 дня", "Через 7 дней"]))
    dp.message.register(add_review, Command("add_review"))
    dp.message.register(handle_review, F.text)
    dp.message.register(view_reviews, Command("view_reviews"))
    dp.message.register(create_poll, Command("poll"))