from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from states import Form
from utils import create_keyboard

router = Router()

@router.message(Form.waiting_for_student_name)
async def process_student_name(message: Message, state: FSMContext):
    if message.text == "Расписание":
        await message.answer("📤 Загрузите изображение с расписанием:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.waiting_for_schedule_photo)
        return

    if message.text in ["Завершить", "Добавить"]:
        return

    student_name = message.text.strip()
    if not student_name:
        await message.answer("❌ Пожалуйста, введите корректное ФИО.")
        return

    data = await state.get_data()
    students = data.get("students", [])
    students.append(student_name)
    await state.update_data(students=students)
    await message.answer(
        "✅ Успешно добавлено!\nНужно ли еще кого-то добавить?",
        reply_markup=create_keyboard(["Добавить", "Завершить", "Расписание"])
    )

@router.message(Form.waiting_for_student_name, F.text.in_(["Добавить", "Завершить", "Расписание"]))
async def finish_input(message: Message, state: FSMContext):
    if message.text == "Добавить":
        await message.answer("Введите ФИО следующего ученика:")
        return

    if message.text == "Завершить":
        data = await state.get_data()
        students = data.get("students", [])
        recipient_id = data.get("recipient_id")
        
        if not students:
            await message.answer("❌ Список учеников пуст!", reply_markup=ReplyKeyboardRemove())
            await state.clear()
            return

        student_list = "\n".join([f"{i+1}. {name}" for i, name in enumerate(students)])
        try:
            await message.bot.send_message(recipient_id, f"Список учеников:\n{student_list}")
            await message.answer("✅ Данные отправлены!", reply_markup=ReplyKeyboardRemove())
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")
        
        await state.clear()