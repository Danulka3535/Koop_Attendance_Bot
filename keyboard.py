from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    """Возвращает главное меню бота."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Новые дела", callback_data="add_task")],
        [InlineKeyboardButton(text="📋 Мои дела", callback_data="show_tasks")],
        [InlineKeyboardButton(text="🎲 Случайные дела", callback_data="random_task")],
        [InlineKeyboardButton(text="⏳ Рабочий перерывчик", callback_data="start_break")],
        [InlineKeyboardButton(text="📈 Как дела?", callback_data="stats")],
        [InlineKeyboardButton(text="🗑️ Всё выкинуть", callback_data="clear_tasks")],
    ])
    return keyboard

def get_cancel_button():
    """Возвращает кнопку отмены."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отбой", callback_data="cancel")],
    ])
    return keyboard

def get_priority_options(task_id=None):
    """Возвращает клавиатуру для выбора приоритета."""
    callback_prefix = f"priority_{task_id}_" if task_id else "priority_"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔴 Высокий", callback_data=f"{callback_prefix}high")],
        [InlineKeyboardButton(text="🟡 Средний", callback_data=f"{callback_prefix}medium")],
        [InlineKeyboardButton(text="🟢 Низкий", callback_data=f"{callback_prefix}low")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
    ])
    return keyboard

def get_tasks_pagination(tasks, page=0, tasks_per_page=5, sort_by_priority=False):
    """Возвращает клавиатуру с задачами и пагинацией."""
    start = page * tasks_per_page
    end = start + tasks_per_page
    task_chunk = tasks[start:end]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for task in task_chunk:
        status = "✅" if task["done"] else "⚡"
        priority = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task["priority"], "🟡")
        # Уменьшаем длину текста задачи до 15 символов, чтобы минимизировать ширину
        task_text = f"{status} {priority} {task['text'][:15]}..."
        # Объединяем все кнопки управления в одну строку
        buttons = [
            InlineKeyboardButton(text="✅", callback_data=f"mark_{task['_id']}"),
            InlineKeyboardButton(text="✏️", callback_data=f"edit_{task['_id']}"),
            InlineKeyboardButton(text="🗑️", callback_data=f"delete_{task['_id']}"),
            InlineKeyboardButton(text="⏰", callback_data=f"remind_{task['_id']}"),
            InlineKeyboardButton(text="⭐", callback_data=f"set_priority_{task['_id']}"),
        ]
        keyboard.inline_keyboard.append([InlineKeyboardButton(text=task_text, callback_data=f"show_task_{task['_id']}")])
        keyboard.inline_keyboard.append(buttons)  # Кнопки теперь в одной строке

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"page_{page-1}_{'priority' if sort_by_priority else 'normal'}"))
    if end < len(tasks):
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"page_{page+1}_{'priority' if sort_by_priority else 'normal'}"))
    if nav_buttons:
        keyboard.inline_keyboard.append(nav_buttons)

    keyboard.inline_keyboard.append([InlineKeyboardButton(text="🏠", callback_data="main_menu")])
    return keyboard

def get_reminder_options(task_id):
    """Возвращает клавиатуру для выбора времени напоминания."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏰ 1 ч", callback_data=f"remind_{task_id}_3600")],
        [InlineKeyboardButton(text="⏰ 2 ч", callback_data=f"remind_{task_id}_7200")],
        [InlineKeyboardButton(text="⏰ Своё", callback_data=f"remind_{task_id}_custom")],
        [InlineKeyboardButton(text="❌", callback_data="cancel")],
    ])
    return keyboard