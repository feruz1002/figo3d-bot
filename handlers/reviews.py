"""Mahsulotga baho (1-5 yulduz) va izoh qoldirish, sharhlarni ko'rish."""
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import db
from handlers.states import ReviewStates
from keyboards import rating_keyboard, skip_comment_keyboard

reviews_router = Router()


@reviews_router.callback_query(F.data.startswith("review:"))
async def start_review(callback: CallbackQuery):
    product_id = int(callback.data.split(":", 1)[1])
    await callback.message.answer(
        "Mahsulotga bahoyingizni tanlang:", reply_markup=rating_keyboard(product_id)
    )
    await callback.answer()


@reviews_router.callback_query(F.data.startswith("rate:"))
async def process_rating(callback: CallbackQuery, state: FSMContext):
    _, product_id, rating = callback.data.split(":")
    await state.set_state(ReviewStates.waiting_comment)
    await state.update_data(product_id=int(product_id), rating=int(rating))
    await callback.message.edit_text(
        f"Bahoyingiz: {'⭐' * int(rating)}\n\n"
        "Istasangiz qisqa izoh yozing, yoki pastdagi tugmani bosib izohsiz saqlang:",
        reply_markup=skip_comment_keyboard(),
    )
    await callback.answer()


async def _save_review(user_id: int, user_name: str, state: FSMContext, comment: str | None):
    data = await state.get_data()
    await db.add_review(data["product_id"], user_id, user_name, data["rating"], comment)
    await state.clear()


@reviews_router.callback_query(F.data == "skip_comment", ReviewStates.waiting_comment)
async def skip_comment(callback: CallbackQuery, state: FSMContext):
    await _save_review(callback.from_user.id, callback.from_user.full_name, state, None)
    await callback.message.edit_text("✅ Rahmat! Bahoyingiz saqlandi.")
    await callback.answer()


@reviews_router.message(ReviewStates.waiting_comment)
async def process_comment(message: Message, state: FSMContext):
    await _save_review(message.from_user.id, message.from_user.full_name, state, message.text)
    await message.answer("✅ Rahmat! Sharhingiz saqlandi.")


@reviews_router.callback_query(F.data.startswith("viewreviews:"))
async def view_reviews(callback: CallbackQuery):
    product_id = int(callback.data.split(":", 1)[1])
    reviews = await db.get_reviews(product_id, limit=5)
    if not reviews:
        await callback.answer("Hali sharhlar yo'q", show_alert=True)
        return

    lines = ["💬 <b>So'nggi sharhlar:</b>"]
    for r in reviews:
        stars = "⭐" * r["rating"]
        name = r["user_name"] or "Mijoz"
        entry = f"\n{stars} — {name}"
        if r["comment"]:
            entry += f"\n«{r['comment']}»"
        lines.append(entry)

    await callback.message.answer("\n".join(lines))
    await callback.answer()
