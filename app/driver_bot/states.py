from aiogram.fsm.state import State, StatesGroup

class DriverRegistration(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_contact_number = State()
    waiting_for_car_model = State()
