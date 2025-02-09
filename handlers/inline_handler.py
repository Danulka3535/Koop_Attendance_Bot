from aiogram import Router, F
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from aiogram.fsm.context import FSMContext
from states import Form
from utils import create_keyboard

router = Router()

@router.inline_query()
async def inline_data_request(inline_query: InlineQuery, state: FSMContext):
    user_id = inline_query.from_user.id
    data = await state.get_data()

    # Если у пользователя есть сохраненные данные (например, список учеников)
    students = data.get("students", [])
    if not students:
        results = [
            InlineQueryResultArticle(
                id="1",
                title="Нет данных для отправки",
                input_message_content=InputTextMessageContent(
                    message_text="❌ Вы не добавили ни одного ученика."
                )
            )
        ]
    else:
        student_list = "\n".join(students)
        results = [
            InlineQueryResultArticle(
                id="1",
                title="Отправить данные",
                input_message_content=InputTextMessageContent(
                    message_text=f"📋 Список учеников:\n{student_list}"
                ),
                reply_markup=create_keyboard(["Подтвердить", "Отменить"])
            )
        ]

    await inline_query.answer(results, cache_time=1)