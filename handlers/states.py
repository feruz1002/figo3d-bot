"""Turli jarayonlardagi bosqichlar (FSM holatlari)."""
from aiogram.fsm.state import State, StatesGroup


class OrderStates(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_address = State()
    waiting_promo = State()
    confirming = State()


class ReviewStates(StatesGroup):
    waiting_comment = State()


class CustomOrderStates(StatesGroup):
    waiting_photo = State()
    waiting_description = State()
    waiting_name = State()
    waiting_phone = State()
    waiting_address = State()
