from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    waiting_for_recipient_username = State()
    waiting_for_confirmation = State()
    waiting_for_recipient_response = State()
    waiting_for_student_name = State()
    waiting_for_schedule_photo = State()
    waiting_for_schedule = State()
    waiting_for_add_more = State()  # Добавлено новое состояние