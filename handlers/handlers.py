from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram import Bot
from states import Form
from database import (
    get_groups,
    register_student,
    is_student_registered,
    register_curator,
    register_headman,
    get_students_by_group,
    save_attendance,
    get_attendance_history,
    get_all_students,
    get_curator_group,
    get_headman_group,
    get_curator_id_by_group
)
from utils import create_inline_keyboard
import logging

router = Router()

# Middleware для авторизации и ролей
class AuthMiddleware:
    def __init__(self):
        self.allowed_users = self.load_allowed_users()

    def load_allowed_users(self, file_path: str = "allowed_users.txt") -> dict:
        """Загрузка Telegram ID и ролей из файла с кодировкой UTF-8"""
        allowed_users = {}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split(":")
                    if len(parts) == 2 and parts[0].isdigit():
                        user_id, role = int(parts[0]), parts[1]
                        allowed_users[user_id] = role
        except FileNotFoundError:
            allowed_users = {123456789: "admin"}  # Замени на свой ID как admin
            logging.warning("Файл allowed_users.txt не найден, используется дефолтный admin.")
        except UnicodeDecodeError:
            logging.error("Ошибка декодирования файла allowed_users.txt. Используется UTF-8.")
            allowed_users = {123456789: "admin"}  # Замени на свой ID
        return allowed_users

    async def __call__(self, handler, event: Message | CallbackQuery, data: dict):
        user_id = event.from_user.id
        if event.text == "/register_student":
            return await handler(event, data)  # Разрешаем регистрацию студентам без проверки
        if user_id not in self.allowed_users:
            if isinstance(event, Message):
                await event.answer("❌ У тебя нет доступа. Обратитесь к администратору.")
            elif isinstance(event, CallbackQuery):
                await event.answer("❌ У тебя нет доступа.", show_alert=True)
            return
        data["role"] = self.allowed_users[user_id]
        return await handler(event, data)

router.message.middleware(AuthMiddleware())
router.callback_query.middleware(AuthMiddleware())

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, role: str, bot: Bot):
    if role == "admin":
        await message.answer("👑 Вы админ. Используйте /admin_view для просмотра всех данных.")
    elif role == "curator":
        group_name = get_curator_group(message.from_user.id)
        buttons = [(f"1. {group_name}", f"group_{group_name}")]
        await message.answer(
            f"📚 Ваша группа: {group_name}\nВыберите для учета:",
            reply_markup=create_inline_keyboard(buttons)
        )
    elif role == "headman":
        group_name = get_headman_group(message.from_user.id)
        buttons = [(f"1. {group_name}", f"headman_group_{group_name}")]
        await message.answer(
            f"👨‍🏫 Ваша группа: {group_name}\nВыберите для отметки:",
            reply_markup=create_inline_keyboard(buttons)
        )
    else:
        if is_student_registered(message.from_user.id):
            await message.answer("🎓 Вы уже зарегистрированы как студент. Обратитесь к куратору или старосте.")
        else:
            await message.answer("🎓 Вы студент? Зарегистрируйтесь с /register_student")
    await state.clear()

@router.message(Command("register_student"))
async def register_student_cmd(message: Message, state: FSMContext):
    """Регистрация студента (доступна всем, но только один раз)"""
    user_id = message.from_user.id
    if is_student_registered(user_id):
        await message.answer("❌ Вы уже зарегистрированы как студент. Данные нельзя изменить.")
        return
    groups = get_groups()
    group_list = "\n".join(f"{i+1}. {group['name']}" for i, group in enumerate(groups))
    await message.answer(f"🎓 Введите номер своей группы:\n{group_list}")
    await state.set_state(Form.waiting_for_group)

@router.message(Form.waiting_for_group)
async def process_group(message: Message, state: FSMContext):
    groups = get_groups()
    try:
        group_idx = int(message.text.strip()) - 1
        if 0 <= group_idx < len(groups):
            group_name = groups[group_idx]["name"]
            await state.update_data(group_name=group_name)
            await message.answer(f"📋 Вы выбрали {group_name}. Введите своё ФИО:")
            await state.set_state(Form.waiting_for_student_name_registration)
        else:
            raise ValueError
    except ValueError:
        await message.answer("❌ Неверный номер группы. Попробуйте снова.")

@router.message(Form.waiting_for_student_name_registration)
async def process_student_name_registration(message: Message, state: FSMContext):
    fio = message.text.strip()
    data = await state.get_data()
    group_name = data["group_name"]
    register_student(message.from_user.id, group_name, fio)
    await message.answer(f"✅ Вы зарегистрированы как {fio} в группе {group_name}! Данные нельзя изменить.")
    await state.clear()

@router.message(Command("register_curator"))
async def register_curator_cmd(message: Message, state: FSMContext, role: str):
    if role not in ["curator", "admin"]:
        await message.answer("❌ У вас нет прав для этой команды.")
        return
    groups = get_groups()
    group_list = "\n".join(f"{i+1}. {group['name']}" for i, group in enumerate(groups))
    await message.answer(f"📚 Введите номер группы, которую курируете:\n{group_list}")
    await state.set_state(Form.waiting_for_curator_group)

@router.message(Form.waiting_for_curator_group)
async def process_curator_group(message: Message, state: FSMContext, role: str):
    groups = get_groups()
    try:
        group_idx = int(message.text.strip()) - 1
        if 0 <= group_idx < len(groups):
            group_name = groups[group_idx]["name"]
            register_curator(message.from_user.id, group_name)
            await message.answer(f"✅ Вы назначены куратором группы {group_name}!")
            await state.clear()
        else:
            raise ValueError
    except ValueError:
        await message.answer("❌ Неверный номер группы. Попробуйте снова.")

@router.message(Command("register_headman"))
async def register_headman_cmd(message: Message, state: FSMContext, role: str):
    if role not in ["headman", "admin"]:
        await message.answer("❌ У вас нет прав для этой команды.")
        return
    groups = get_groups()
    group_list = "\n".join(f"{i+1}. {group['name']}" for i, group in enumerate(groups))
    await message.answer(f"👨‍🏫 Введите номер группы, где вы староста:\n{group_list}")
    await state.set_state(Form.waiting_for_headman_group)

@router.message(Form.waiting_for_headman_group)
async def process_headman_group(message: Message, state: FSMContext, role: str):
    groups = get_groups()
    try:
        group_idx = int(message.text.strip()) - 1
        if 0 <= group_idx < len(groups):
            group_name = groups[group_idx]["name"]
            await state.update_data(group_name=group_name)
            await message.answer(f"📋 Вы выбрали {group_name}. Введите своё ФИО:")
            await state.set_state(Form.waiting_for_headman_name)
        else:
            raise ValueError
    except ValueError:
        await message.answer("❌ Неверный номер группы. Попробуйте снова.")

@router.message(Form.waiting_for_headman_name)
async def process_headman_name(message: Message, state: FSMContext):
    fio = message.text.strip()
    data = await state.get_data()
    group_name = data["group_name"]
    register_headman(message.from_user.id, group_name, fio)
    await message.answer(f"✅ Вы зарегистрированы как староста {fio} группы {group_name}!")
    await state.clear()

@router.message(Command("admin_view"))
async def admin_view(message: Message, state: FSMContext, role: str):
    if role != "admin":
        await message.answer("❌ Эта команда только для админа.")
        return
    students = get_all_students()
    response = "📋 Все студенты:\n"
    for student in students:
        response += f"ID: {student['telegram_id']}, ФИО: {student['name']}, Группа: {student['group_name']}\n"
    await message.answer(response)
    await state.clear()

@router.message(Command("history"))
async def cmd_history(message: Message, state: FSMContext, role: str):
    user_id = message.from_user.id
    if role == "admin":
        history = get_attendance_history(None)
    elif role == "curator":
        group_name = get_curator_group(user_id)
        history = get_attendance_history(user_id) if group_name else []
    else:
        history = []
    if not history:
        await message.answer("📜 История пуста.")
        return
    response = "📜 История посещаемости:\n"
    for entry in history:
        students = "\n".join(f"{i+1}. {student['name']} ({student.get('minutes', '0')} мин, {student.get('hours', '0')} ч, {student.get('reason', 'нет причины')})" 
                            for i, student in enumerate(entry["students"]))
        response += (
            f"Дата: {entry['timestamp']}\n"
            f"Группа: {entry['group_name']}\n"
            f"Статус: {entry['status']}\n"
            f"Студенты:\n{students}\n\n"
        )
    await message.answer(response)
    await state.clear()

@router.callback_query(F.data.startswith("group_"))
async def show_students(callback: CallbackQuery, state: FSMContext, bot: Bot, role: str):
    group_name = callback.data.split("_", 1)[1]
    if role == "curator" and get_curator_group(callback.from_user.id) != group_name:
        await callback.answer("❌ Это не ваша группа!", show_alert=True)
        return
    students = get_students_by_group(group_name)
    student_list = "\n".join(f"{i+1}. {student['name']}" for i, student in enumerate(students))
    buttons = [
        ("Отметить присутствующих", f"mark_{group_name}"),
        ("Назад", "back_to_groups")
    ]
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"📋 Группа: {group_name}\nСтуденты:\n{student_list}",
        reply_markup=create_inline_keyboard(buttons)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("headman_group_"))
async def headman_show_students(callback: CallbackQuery, state: FSMContext, bot: Bot, role: str):
    group_name = callback.data.split("_", 2)[2]
    if role == "headman" and get_headman_group(callback.from_user.id) != group_name:
        await callback.answer("❌ Это не ваша группа!", show_alert=True)
        return
    students = get_students_by_group(group_name)
    student_list = "\n".join(f"{i+1}. {student['name']}" for i, student in enumerate(students))
    buttons = [
        ("Отметить опоздавших", f"headman_late_{group_name}"),
        ("Отметить не явившихся", f"headman_absent_{group_name}"),
        ("Пришедшие на 2-3 пару", f"headman_late_pair_{group_name}"),
        ("Назад", "back_to_groups")
    ]
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"📋 Группа: {group_name}\nСтуденты:\n{student_list}",
        reply_markup=create_inline_keyboard(buttons)
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_groups")
async def back_to_groups(callback: CallbackQuery, state: FSMContext, bot: Bot, role: str):
    if role == "admin":
        groups = get_groups()
        buttons = [(f"{i+1}. {group['name']}", f"group_{group['name']}") for i, group in enumerate(groups)]
    elif role == "curator":
        group_name = get_curator_group(callback.from_user.id)
        buttons = [(f"1. {group_name}", f"group_{group_name}")]
    else:  # headman
        group_name = get_headman_group(callback.from_user.id)
        buttons = [(f"1. {group_name}", f"headman_group_{group_name}")]
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="📚 Выберите группу для учета:",
        reply_markup=create_inline_keyboard(buttons)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("mark_"))
async def mark_attendance(callback: CallbackQuery, state: FSMContext, bot: Bot, role: str):
    group_name = callback.data.split("_", 1)[1]
    if role == "curator" and get_curator_group(callback.from_user.id) != group_name:
        await callback.answer("❌ Это не ваша группа!", show_alert=True)
        return
    await state.update_data(group_name=group_name, students=[])
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"📋 Введите ФИО студентов группы {group_name}, которые присутствовали (по одному):"
    )
    await state.set_state(Form.waiting_for_student_name)

@router.callback_query(F.data.startswith("headman_late_"))
async def headman_mark_late(callback: CallbackQuery, state: FSMContext, bot: Bot, role: str):
    group_name = callback.data.split("_", 2)[2]
    if role == "headman" and get_headman_group(callback.from_user.id) != group_name:
        await callback.answer("❌ Это не ваша группа!", show_alert=True)
        return
    await state.update_data(group_name=group_name, late_students=[])
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"📋 Введите ФИО студента группы {group_name}, который опоздал (по одному):"
    )
    await state.set_state(Form.waiting_for_late_student_name)

@router.callback_query(F.data.startswith("headman_absent_"))
async def headman_mark_absent(callback: CallbackQuery, state: FSMContext, bot: Bot, role: str):
    group_name = callback.data.split("_", 2)[2]
    if role == "headman" and get_headman_group(callback.from_user.id) != group_name:
        await callback.answer("❌ Это не ваша группа!", show_alert=True)
        return
    await state.update_data(group_name=group_name, absent_students=[])
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"📋 Введите ФИО студента группы {group_name}, который не явился (по одному):"
    )
    await state.set_state(Form.waiting_for_absent_student_name)

@router.callback_query(F.data.startswith("headman_late_pair_"))
async def headman_mark_late_pair(callback: CallbackQuery, state: FSMContext, bot: Bot, role: str):
    group_name = callback.data.split("_", 3)[3]
    if role == "headman" and get_headman_group(callback.from_user.id) != group_name:
        await callback.answer("❌ Это не ваша группа!", show_alert=True)
        return
    await state.update_data(group_name=group_name, late_pair_students=[])
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"📋 Введите ФИО студента группы {group_name}, который пришел на 2-3 пару (по одному):"
    )
    await state.set_state(Form.waiting_for_late_pair_student_name)

@router.message(Form.waiting_for_student_name)
async def process_student_name(message: Message, state: FSMContext):
    student_name = message.text.strip()
    data = await state.get_data()
    students = data.get("students", [])
    students.append({"name": student_name})
    await state.update_data(students=students)
    buttons = [
        ("Добавить ещё", "add_more"),
        ("Завершить", "finish")
    ]
    await message.answer(
        f"👤 Присутствовал: {student_name}\nЧто дальше?",
        reply_markup=create_inline_keyboard(buttons)
    )

@router.message(Form.waiting_for_late_student_name)
async def process_late_student_name(message: Message, state: FSMContext):
    student_name = message.text.strip()
    data = await state.get_data()
    late_students = data.get("late_students", [])
    late_students.append({"name": student_name})
    await state.update_data(late_students=late_students, current_student=student_name)
    await message.answer(
        f"👤 Опоздал: {student_name}\nНа сколько минут опоздал?",
        reply_markup=None
    )
    await state.set_state(Form.waiting_for_late_minutes)

@router.message(Form.waiting_for_late_minutes)
async def process_late_minutes(message: Message, state: FSMContext):
    try:
        minutes = int(message.text.strip())
        data = await state.get_data()
        late_students = data["late_students"]
        current_student = data["current_student"]
        for student in late_students:
            if student["name"] == current_student:
                student["minutes"] = minutes
        await state.update_data(late_students=late_students)
        buttons = [
            ("Добавить ещё", "headman_add_more_late"),
            ("Завершить", "headman_finish_late")
        ]
        await message.answer(
            f"👤 Опоздал: {current_student} на {minutes} мин\nЧто дальше?",
            reply_markup=create_inline_keyboard(buttons)
        )
        await state.set_state(Form.waiting_for_late_student_name)
    except ValueError:
        await message.answer("❌ Введите число минут!")

@router.message(Form.waiting_for_absent_student_name)
async def process_absent_student_name(message: Message, state: FSMContext):
    student_name = message.text.strip()
    data = await state.get_data()
    absent_students = data.get("absent_students", [])
    absent_students.append({"name": student_name, "hours": 6})
    await state.update_data(absent_students=absent_students, current_student=student_name)
    buttons = [
        ("Указать причину", "absent_reason"),
        ("Добавить ещё", "headman_add_more_absent"),
        ("Завершить", "headman_finish_absent")
    ]
    await message.answer(
        f"👤 Не явился: {student_name} (6 ч)\nЧто дальше?",
        reply_markup=create_inline_keyboard(buttons)
    )

@router.callback_query(F.data == "absent_reason")
async def absent_reason(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    current_student = data["current_student"]
    await bot.send_message(
        callback.message.chat.id,
        f"📋 Укажите причину отсутствия для {current_student}:"
    )
    await state.set_state(Form.waiting_for_absent_reason)
    await callback.answer()

@router.message(Form.waiting_for_absent_reason)
async def process_absent_reason(message: Message, state: FSMContext):
    reason = message.text.strip()
    data = await state.get_data()
    absent_students = data["absent_students"]
    current_student = data["current_student"]
    for student in absent_students:
        if student["name"] == current_student:
            student["reason"] = reason
    await state.update_data(absent_students=absent_students)
    buttons = [
        ("Добавить ещё", "headman_add_more_absent"),
        ("Завершить", "headman_finish_absent")
    ]
    await message.answer(
        f"👤 Не явился: {current_student} (6 ч, причина: {reason})\nЧто дальше?",
        reply_markup=create_inline_keyboard(buttons)
    )
    await state.set_state(Form.waiting_for_absent_student_name)

@router.message(Form.waiting_for_late_pair_student_name)
async def process_late_pair_student_name(message: Message, state: FSMContext):
    student_name = message.text.strip()
    data = await state.get_data()
    late_pair_students = data.get("late_pair_students", [])
    late_pair_students.append({"name": student_name})
    await state.update_data(late_pair_students=late_pair_students, current_student=student_name)
    buttons = [
        ("2 пара", "pair_2"),
        ("3 пара", "pair_3")
    ]
    await message.answer(
        f"👤 Пришел: {student_name}\nНа какую пару?",
        reply_markup=create_inline_keyboard(buttons)
    )

@router.callback_query(F.data.in_(["pair_2", "pair_3"]))
async def process_late_pair_number(callback: CallbackQuery, state: FSMContext, bot: Bot):
    pair = 2 if callback.data == "pair_2" else 3
    hours = (pair - 1) * 2
    data = await state.get_data()
    late_pair_students = data["late_pair_students"]
    current_student = data["current_student"]
    for student in late_pair_students:
        if student["name"] == current_student:
            student["pair"] = pair
            student["hours"] = hours
    await state.update_data(late_pair_students=late_pair_students)
    buttons = [
        ("Добавить ещё", "headman_add_more_late_pair"),
        ("Завершить", "headman_finish_late_pair")
    ]
    await bot.send_message(
        callback.message.chat.id,
        f"👤 Пришел на {pair} пару: {current_student} ({hours} ч прогула)\nЧто дальше?",
        reply_markup=create_inline_keyboard(buttons)
    )
    await state.set_state(Form.waiting_for_late_pair_student_name)
    await callback.answer()

@router.callback_query(F.data == "add_more")
async def add_more_students(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    group_name = data["group_name"]
    await bot.send_message(
        callback.message.chat.id,
        f"📋 Введите следующего студента для группы {group_name}:"
    )
    await callback.answer()

@router.callback_query(F.data == "headman_add_more_absent")
async def headman_add_more_absent(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    group_name = data["group_name"]
    await bot.send_message(
        callback.message.chat.id,
        f"📋 Введите следующего не явившегося студента для группы {group_name}:"
    )
    await callback.answer()

@router.callback_query(F.data == "headman_add_more_late")
async def headman_add_more_late(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    group_name = data["group_name"]
    await bot.send_message(
        callback.message.chat.id,
        f"📋 Введите следующего опоздавшего студента для группы {group_name}:"
    )
    await callback.answer()

@router.callback_query(F.data == "headman_add_more_late_pair")
async def headman_add_more_late_pair(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    group_name = data["group_name"]
    await bot.send_message(
        callback.message.chat.id,
        f"📋 Введите следующего студента, пришедшего на 2-3 пару для группы {group_name}:"
    )
    await callback.answer()

@router.callback_query(F.data == "finish")
async def finish_attendance(callback: CallbackQuery, state: FSMContext, bot: Bot, role: str):
    data = await state.get_data()
    group_name = data["group_name"]
    students = data.get("students", [])
    if not students:
        await bot.send_message(
            callback.message.chat.id,
            "❌ Список пуст! Начните заново с /start."
        )
        await state.clear()
        return
    save_attendance(callback.from_user.id, group_name, students, "present")
    student_list = "\n".join(f"{i+1}. {student['name']}" for i, student in enumerate(students))
    await bot.send_message(
        callback.message.chat.id,
        f"✅ Присутствующие для группы {group_name} сохранены:\n{student_list}"
    )
    buttons = [(f"1. {group_name}", f"group_{group_name}")]
    await bot.send_message(
        callback.message.chat.id,
        "📚 Выберите группу для следующей отметки:",
        reply_markup=create_inline_keyboard(buttons)
    )
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "headman_finish_absent")
async def headman_finish_absent(callback: CallbackQuery, state: FSMContext, bot: Bot, role: str):
    data = await state.get_data()
    group_name = data["group_name"]
    absent_students = data.get("absent_students", [])
    if not absent_students:
        await bot.send_message(
            callback.message.chat.id,
            "❌ Список пуст! Начните заново с /start."
        )
        await state.clear()
        return
    save_attendance(callback.from_user.id, group_name, absent_students, "absent")
    absent_list = "\n".join(f"{i+1}. {student['name']} ({student.get('reason', 'нет причины')})" 
                            for i, student in enumerate(absent_students))
    curator_id = get_curator_id_by_group(group_name)
    if curator_id:
        await bot.send_message(
            curator_id,
            f"📋 От Ромы (староста группы {group_name}):\nНе явились (6 ч):\n{absent_list}"
        )
    await bot.send_message(
        callback.message.chat.id,
        f"✅ Данные об отсутствующих для группы {group_name} отправлены куратору:\n{absent_list}"
    )
    buttons = [(f"1. {group_name}", f"headman_group_{group_name}")]
    await bot.send_message(
        callback.message.chat.id,
        "📚 Выберите группу для следующей отметки:",
        reply_markup=create_inline_keyboard(buttons)
    )
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "headman_finish_late")
async def headman_finish_late(callback: CallbackQuery, state: FSMContext, bot: Bot, role: str):
    data = await state.get_data()
    group_name = data["group_name"]
    late_students = data.get("late_students", [])
    if not late_students:
        await bot.send_message(
            callback.message.chat.id,
            "❌ Список пуст! Начните заново с /start."
        )
        await state.clear()
        return
    save_attendance(callback.from_user.id, group_name, late_students, "late")
    late_list = "\n".join(f"{i+1}. {student['name']} ({student['minutes']} мин)" 
                          for i, student in enumerate(late_students))
    curator_id = get_curator_id_by_group(group_name)
    if curator_id:
        await bot.send_message(
            curator_id,
            f"📋 От Ромы (староста группы {group_name}):\nОпоздали:\n{late_list}"
        )
    await bot.send_message(
        callback.message.chat.id,
        f"✅ Данные об опоздавших для группы {group_name} отправлены куратору:\n{late_list}"
    )
    buttons = [(f"1. {group_name}", f"headman_group_{group_name}")]
    await bot.send_message(
        callback.message.chat.id,
        "📚 Выберите группу для следующей отметки:",
        reply_markup=create_inline_keyboard(buttons)
    )
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "headman_finish_late_pair")
async def headman_finish_late_pair(callback: CallbackQuery, state: FSMContext, bot: Bot, role: str):
    data = await state.get_data()
    group_name = data["group_name"]
    late_pair_students = data.get("late_pair_students", [])
    if not late_pair_students:
        await bot.send_message(
            callback.message.chat.id,
            "❌ Список пуст! Начните заново с /start."
        )
        await state.clear()
        return
    save_attendance(callback.from_user.id, group_name, late_pair_students, "late_pair")
    late_pair_list = "\n".join(f"{i+1}. {student['name']} (пришел на {student['pair']} пару, {student['hours']} ч)" 
                               for i, student in enumerate(late_pair_students))
    curator_id = get_curator_id_by_group(group_name)
    if curator_id:
        await bot.send_message(
            curator_id,
            f"📋 От Ромы (староста группы {group_name}):\nПришедшие на 2-3 пару:\n{late_pair_list}"
        )
    await bot.send_message(
        callback.message.chat.id,
        f"✅ Данные о пришедших на 2-3 пару для группы {group_name} отправлены куратору:\n{late_pair_list}"
    )
    buttons = [(f"1. {group_name}", f"headman_group_{group_name}")]
    await bot.send_message(
        callback.message.chat.id,
        "📚 Выберите группу для следующей отметки:",
        reply_markup=create_inline_keyboard(buttons)
    )
    await state.clear()
    await callback.answer()