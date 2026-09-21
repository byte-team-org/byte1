from aiogram.fsm.state import State, StatesGroup


class ParticipantForm(StatesGroup):
    language = State()
    last_name = State()
    first_name = State()
    phone = State()
    username = State()
    birth_date = State()
    region = State()
    payment = State()
