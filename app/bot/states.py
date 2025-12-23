from aiogram.fsm.state import StatesGroup, State

class CalcFSM(StatesGroup):
    product = State()
    quantity = State()
    material = State()
    modifiers = State()
