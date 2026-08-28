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


class ProfileEditStates(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_address = State()


class TopupStates(StatesGroup):
    waiting_amount = State()
    waiting_proof = State()


class AdminProductStates(StatesGroup):
    """Admin /admin buyrug'i orqali yangi mahsulot qo'shayotgandagi bosqichlar."""
    waiting_category = State()
    waiting_name = State()
    waiting_description = State()
    waiting_price = State()
    waiting_photos = State()
    waiting_video = State()
    confirming = State()


class AdminOrderStates(StatesGroup):
    """Admin buyurtmani "⚠️ Muammo" deb belgilaganda, sababni (izohni)
    chatda so'rab olish uchun (handlers/admin.py'ga qarang)."""
    waiting_problem_reason = State()
