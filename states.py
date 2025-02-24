from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    waiting_for_group = State()
    waiting_for_student_name_registration = State()
    waiting_for_curator_group = State()
    waiting_for_headman_group = State()
    waiting_for_headman_name = State()
    waiting_for_student_name = State()
    waiting_for_absent_student_name = State()
    waiting_for_late_student_name = State()
    waiting_for_late_minutes = State()
    waiting_for_absent_reason = State()
    waiting_for_late_pair_student_name = State()