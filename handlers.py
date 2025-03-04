from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from keyboard import get_main_menu, get_cancel_button, get_tasks_pagination, get_reminder_options, get_priority_options
from database import add_task, get_tasks, mark_task_done, delete_task, clear_tasks, set_task_reminder, edit_task, set_task_priority
from bson.objectid import ObjectId, InvalidId
import asyncio
import random

router = Router()

class TaskStates(StatesGroup):
    waiting_for_task = State()
    waiting_for_edit = State()
    waiting_for_reminder_time = State()
    waiting_for_priority = State()

QUOTES = [
    "Молодец! 🎩",
    "Ещё чуть-чуть! 💪",
    "Ты крут! 🔥",
    "Горы впереди! ⛰️",
    "Пиво бы сейчас! 🍺",
]

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer(
        "✨ Привет, братан! Я твой бот для дел. Считаю прогресс, мотивирую и даю перерывчики!\nЧто делать будем?",
        reply_markup=get_main_menu()
    )

@router.callback_query(F.data == "main_menu")
async def back_to_menu(callback: CallbackQuery):
    try:
        await callback.message.edit_text(
            "✨ Что делать?",
            reply_markup=get_main_menu()
        )
    except TelegramBadRequest:
        await callback.message.answer(
            "✨ Что делать?",
            reply_markup=get_main_menu()
        )

@router.callback_query(F.data == "add_task")
async def add_task_start(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.edit_text(
            "📝 Введи задачу:",
            reply_markup=get_cancel_button()
        )
    except TelegramBadRequest:
        await callback.message.answer(
            "📝 Введи задачу:",
            reply_markup=get_cancel_button()
        )
    await state.set_state(TaskStates.waiting_for_task)

@router.message(TaskStates.waiting_for_task)
async def process_task(message: Message, state: FSMContext):
    await state.update_data(task_text=message.text)
    await message.answer(
        "⭐ Выбери приоритет:",
        reply_markup=get_priority_options()
    )
    await state.set_state(TaskStates.waiting_for_priority)

@router.callback_query(F.data.in_(["priority_high", "priority_medium", "priority_low"]))
async def process_priority(callback: CallbackQuery, state: FSMContext):
    priority = callback.data.split("_")[1]
    data = await state.get_data()
    task_text = data["task_text"]
    add_task(callback.from_user.id, task_text, priority)
    try:
        await callback.message.edit_text(
            f"✅ Задача с приоритетом {priority} добавлена!",
            reply_markup=get_main_menu()
        )
    except TelegramBadRequest:
        await callback.message.answer(
            f"✅ Задача с приоритетом {priority} добавлена!",
            reply_markup=get_main_menu()
        )
    await state.clear()

@router.callback_query(F.data == "show_tasks")
async def show_tasks(callback: CallbackQuery):
    tasks = get_tasks(callback.from_user.id)
    if not tasks:
        try:
            await callback.message.edit_text(
                "📭 Дел нет, отдыхай!",
                reply_markup=get_main_menu()
            )
        except TelegramBadRequest:
            await callback.message.answer(
                "📭 Дел нет, отдыхай!",
                reply_markup=get_main_menu()
            )
    else:
        await display_tasks(callback, tasks)

async def display_tasks(callback: CallbackQuery, tasks):
    total = len(tasks)
    done = len([t for t in tasks if t["done"]])
    progress = (done / total) * 100 if total > 0 else 0
    progress_bar = "█" * int(progress // 10) + "░" * (10 - int(progress // 10))
    keyboard = get_tasks_pagination(tasks, page=0)
    try:
        await callback.message.edit_text(
            f"📋 Твои дела:\nГотово: [{progress_bar}] {progress:.1f}%\n(✅ — закрыть, ✏️ — редакт., 🗑️ — уд., ⏰ — напом., ⭐ — приоритет)",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except TelegramBadRequest:
        await callback.message.answer(
            f"📋 Твои дела:\nГотово: [{progress_bar}] {progress:.1f}%\n(✅ — закрыть, ✏️ — редакт., 🗑️ — уд., ⏰ — напом., ⭐ — приоритет)",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

@router.callback_query(F.data.startswith("page_"))
async def paginate_tasks(callback: CallbackQuery):
    parts = callback.data.split("_")
    page = int(parts[1])
    tasks = get_tasks(callback.from_user.id)
    total = len(tasks)
    done = len([t for t in tasks if t["done"]])
    progress = (done / total) * 100 if total > 0 else 0
    progress_bar = "█" * int(progress // 10) + "░" * (10 - int(progress // 10))
    keyboard = get_tasks_pagination(tasks, page=page)
    try:
        await callback.message.edit_text(
            f"📋 Твои дела:\nГотово: [{progress_bar}] {progress:.1f}%\n(✅ — закрыть, ✏️ — редакт., 🗑️ — уд., ⏰ — напом., ⭐ — приоритет)",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except TelegramBadRequest:
        await callback.message.answer(
            f"📋 Твои дела:\nГотово: [{progress_bar}] {progress:.1f}%\n(✅ — закрыть, ✏️ — редакт., 🗑️ — уд., ⏰ — напом., ⭐ — приоритет)",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

@router.callback_query(F.data.startswith("mark_"))
async def mark_task_done_inline(callback: CallbackQuery):
    task_id = ObjectId(callback.data.split("_")[1])
    mark_task_done(callback.from_user.id, task_id)
    tasks = get_tasks(callback.from_user.id)
    quote = random.choice(QUOTES)
    total = len(tasks)
    done = len([t for t in tasks if t["done"]])
    progress = (done / total) * 100 if total > 0 else 0
    progress_bar = "█" * int(progress // 10) + "░" * (10 - int(progress // 10))
    keyboard = get_tasks_pagination(tasks, page=0)
    try:
        await callback.message.edit_text(
            f"📋 Твои дела:\nГотово: [{progress_bar}] {progress:.1f}%\n{quote}\n(✅ — закрыть, ✏️ — редакт., 🗑️ — уд., ⏰ — напом., ⭐ — приоритет)",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except TelegramBadRequest:
        await callback.message.answer(
            f"📋 Твои дела:\nГотово: [{progress_bar}] {progress:.1f}%\n{quote}\n(✅ — закрыть, ✏️ — редакт., 🗑️ — уд., ⏰ — напом., ⭐ — приоритет)",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

@router.callback_query(F.data.startswith("delete_"))
async def delete_task_inline(callback: CallbackQuery):
    task_id = ObjectId(callback.data.split("_")[1])
    delete_task(callback.from_user.id, task_id)
    tasks = get_tasks(callback.from_user.id)
    await display_tasks(callback, tasks)

@router.callback_query(F.data.startswith("edit_"))
async def edit_task_start(callback: CallbackQuery, state: FSMContext):
    task_id = ObjectId(callback.data.split("_")[1])
    tasks = get_tasks(callback.from_user.id)
    task = next((t for t in tasks if t["_id"] == task_id), None)
    if task:
        try:
            await callback.message.edit_text(
                f"✏️ Новый текст для *{task['text']}*:",
                reply_markup=get_cancel_button(),
                parse_mode="Markdown"
            )
        except TelegramBadRequest:
            await callback.message.answer(
                f"✏️ Новый текст для *{task['text']}*:",
                reply_markup=get_cancel_button(),
                parse_mode="Markdown"
            )
        await state.update_data(task_id=task_id)
        await state.set_state(TaskStates.waiting_for_edit)

@router.message(TaskStates.waiting_for_edit)
async def process_edit_task(message: Message, state: FSMContext):
    data = await state.get_data()
    task_id = data["task_id"]
    edit_task(message.from_user.id, task_id, message.text)
    await message.answer(
        "✏️ Обновлено!",
        reply_markup=get_main_menu()
    )
    await state.clear()

@router.callback_query(F.data.startswith("set_priority_"))
async def set_priority_start(callback: CallbackQuery):
    task_id = ObjectId(callback.data.split("_")[2])
    tasks = get_tasks(callback.from_user.id)
    task = next((t for t in tasks if t["_id"] == task_id), None)
    if task:
        try:
            await callback.message.edit_text(
                f"⭐ Приоритет для *{task['text']}*:\nТекущий: {task['priority']}",
                reply_markup=get_priority_options(task_id),
                parse_mode="Markdown"
            )
        except TelegramBadRequest:
            await callback.message.answer(
                f"⭐ Приоритет для *{task['text']}*:\nТекущий: {task['priority']}",
                reply_markup=get_priority_options(task_id),
                parse_mode="Markdown"
            )

@router.callback_query(F.data.regexp(r"priority_[0-9a-fA-F]{24}_(high|medium|low)"))
async def process_set_priority(callback: CallbackQuery):
    parts = callback.data.split("_")
    task_id = ObjectId(parts[1])
    priority = parts[2]
    set_task_priority(callback.from_user.id, task_id, priority)
    tasks = get_tasks(callback.from_user.id)
    await display_tasks(callback, tasks)

@router.callback_query(F.data == "start_break")
async def start_break(callback: CallbackQuery):
    try:
        await callback.message.edit_text("⏳ 25 мин работы, потом перерыв!")
        await asyncio.sleep(25 * 60)  # 25 минут
        await callback.message.edit_text(
            "⏳ 5 мин отдыха! Чайник ставь.\nВ меню?",
            reply_markup=get_main_menu()
        )
    except TelegramBadRequest:
        await callback.message.answer("⏳ 25 мин работы, потом перерыв!")
        await asyncio.sleep(25 * 60)
        await callback.message.answer(
            "⏳ 5 мин отдыха! Чайник ставь.\nВ меню?",
            reply_markup=get_main_menu()
        )

@router.callback_query(F.data == "stats")
async def show_stats(callback: CallbackQuery):
    tasks = get_tasks(callback.from_user.id)
    total = len(tasks)
    done = len([t for t in tasks if t["done"]])
    progress = (done / total) * 100 if total > 0 else 0
    progress_bar = "█" * int(progress // 10) + "░" * (10 - int(progress // 10))
    stats_text = (
        f"📈 Статистика:\n"
        f"Всего: {total}\n"
        f"Сделано: {done} ✅\n"
        f"Осталось: {total - done} ⚡\n"
        f"Готово: [{progress_bar}] {progress:.1f}%"
    )
    try:
        await callback.message.edit_text(stats_text, reply_markup=get_main_menu(), parse_mode="Markdown")
    except TelegramBadRequest:
        await callback.message.answer(stats_text, reply_markup=get_main_menu(), parse_mode="Markdown")

@router.callback_query(F.data == "clear_tasks")
async def clear_tasks_inline(callback: CallbackQuery):
    clear_tasks(callback.from_user.id)
    try:
        await callback.message.edit_text(
            "🗑️ Всё очищено!",
            reply_markup=get_main_menu()
        )
    except TelegramBadRequest:
        await callback.message.answer(
            "🗑️ Всё очищено!",
            reply_markup=get_main_menu()
        )

@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.edit_text(
            "✨ Отмена!",
            reply_markup=get_main_menu()
        )
    except TelegramBadRequest:
        await callback.message.answer(
            "✨ Отмена!",
            reply_markup=get_main_menu()
        )
    await state.clear()

@router.callback_query(F.data == "random_task")
async def random_task(callback: CallbackQuery):
    tasks = get_tasks(callback.from_user.id)
    undone_tasks = [t for t in tasks if not t["done"]]
    if not undone_tasks:
        try:
            await callback.message.edit_text(
                "📭 Нет задач!",
                reply_markup=get_main_menu()
            )
        except TelegramBadRequest:
            await callback.message.answer(
                "📭 Нет задач!",
                reply_markup=get_main_menu()
            )
    else:
        random_task = random.choice(undone_tasks)
        try:
            await callback.message.edit_text(
                f"🎲 *{random_task['text']}*\nНачинай!",
                reply_markup=get_main_menu(),
                parse_mode="Markdown"
            )
        except TelegramBadRequest:
            await callback.message.answer(
                f"🎲 *{random_task['text']}*\nНачинай!",
                reply_markup=get_main_menu(),
                parse_mode="Markdown"
            )

@router.callback_query(F.data.startswith("remind_"))
async def remind_task(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    if len(parts) < 2:
        await callback.answer("Ошибка. Попробуй позже.")
        return
    try:
        if len(parts) == 2:  # Показываем варианты напоминания
            task_id = ObjectId(parts[1])
            tasks = get_tasks(callback.from_user.id)
            task = next((t for t in tasks if t["_id"] == task_id), None)
            if task and not task["done"]:
                try:
                    await callback.message.edit_text(
                        f"⏰ Напомнить: *{task['text']}*?",
                        reply_markup=get_reminder_options(task_id),
                        parse_mode="Markdown"
                    )
                except TelegramBadRequest:
                    await callback.message.answer(
                        f"⏰ Напомнить: *{task['text']}*?",
                        reply_markup=get_reminder_options(task_id),
                        parse_mode="Markdown"
                    )
        elif parts[2] == "custom":  # Запрашиваем своё время
            task_id = ObjectId(parts[1])
            tasks = get_tasks(callback.from_user.id)
            task = next((t for t in tasks if t["_id"] == task_id), None)
            if task and not task["done"]:
                try:
                    await callback.message.edit_text(
                        f"⏰ Время (мин) для *{task['text']}*:",
                        reply_markup=get_cancel_button(),
                        parse_mode="Markdown"
                    )
                except TelegramBadRequest:
                    await callback.message.answer(
                        f"⏰ Время (мин) для *{task['text']}*:",
                        reply_markup=get_cancel_button(),
                        parse_mode="Markdown"
                    )
                await state.update_data(task_id=task_id)
                await state.set_state(TaskStates.waiting_for_reminder_time)
        else:  # Устанавливаем фиксированное время
            task_id = ObjectId(parts[1])
            seconds = int(parts[2])
            set_task_reminder(callback.from_user.id, task_id, seconds)
            tasks = get_tasks(callback.from_user.id)
            task = next((t for t in tasks if t["_id"] == task_id), None)
            try:
                await callback.message.edit_text(
                    f"⏰ Напомню *{task['text']}* через {seconds // 3600} ч!",
                    reply_markup=get_main_menu(),
                    parse_mode="Markdown"
                )
            except TelegramBadRequest:
                await callback.message.answer(
                    f"⏰ Напомню *{task['text']}* через {seconds // 3600} ч!",
                    reply_markup=get_main_menu(),
                    parse_mode="Markdown"
                )
            await asyncio.sleep(seconds)
            await callback.message.answer(
                f"⏰ Пора: *{task['text']}*!",
                parse_mode="Markdown"
            )
    except (ValueError, InvalidId) as e:
        await callback.answer(f"Ошибка: {str(e)}. Попробуй позже.")

@router.message(TaskStates.waiting_for_reminder_time)
async def process_reminder_time(message: Message, state: FSMContext):
    try:
        minutes = int(message.text)
        if minutes <= 0:
            raise ValueError
        seconds = minutes * 60
        data = await state.get_data()
        task_id = data["task_id"]
        set_task_reminder(message.from_user.id, task_id, seconds)
        tasks = get_tasks(message.from_user.id)
        task = next((t for t in tasks if t["_id"] == task_id), None)
        await message.answer(
            f"⏰ Напомню *{task['text']}* через {minutes} мин!",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
        await asyncio.sleep(seconds)
        await message.answer(
            f"⏰ Пора: *{task['text']}*!",
            parse_mode="Markdown"
        )
    except ValueError:
        await message.answer(
            "⏰ Введи число минут (> 0)!"
        )
    finally:
        await state.clear()

@router.callback_query(F.data.startswith("show_task_"))
async def show_task_details(callback: CallbackQuery):
    task_id = ObjectId(callback.data.split("_")[2])
    tasks = get_tasks(callback.from_user.id)
    task = next((t for t in tasks if t["_id"] == task_id), None)
    if task:
        status = "✅" if task["done"] else "⚡"
        priority = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task["priority"], "🟢")
        try:
            await callback.message.edit_text(
                f"📋 Задача:\nСтатус: {status}\nПриоритет: {priority} {task['priority']}\nТекст: *{task['text']}*",
                reply_markup=get_tasks_pagination(tasks, page=0),
                parse_mode="Markdown"
            )
        except TelegramBadRequest:
            await callback.message.answer(
                f"📋 Задача:\nСтатус: {status}\nПриоритет: {priority} {task['priority']}\nТекст: *{task['text']}*",
                reply_markup=get_tasks_pagination(tasks, page=0),
                parse_mode="Markdown"
            )