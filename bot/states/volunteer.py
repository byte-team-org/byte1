from aiogram.fsm.state import State, StatesGroup


class VolunteerForm(StatesGroup):
    language = State()
    photo = State()
    full_name = State()
    phone = State()
    username = State()
    birth_date = State()
    region = State()
