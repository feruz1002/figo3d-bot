"""Admin (yoki 3D-print hamkor) uchun buyruqlar:
- Buyurtmani 'Qabul qildim' deb belgilash
- Shaxsiy buyurtma bo'yicha mijoz bilan bog'langanini belgilash
- Yangi promo-kod yaratish (/promo buyrug'i orqali)
"""
from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message

import admin_service
import db
from config import is_admin as _is_admin

admin_router = Router()


@admin_router.callback_query(F.data.startswith("order_accept:"))
async def order_accept(callback: CallbackQuery, bot: Bot):
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return

    order_id = int(callback.data.split(":", 1)[1])
    order, reason = await admin_service.accept_order(order_id)
    if order is None:
        await callback.answer("Buyurtma topilmadi", show_alert=True)
        return

    # html_text - Telegram formatlashini (qalin harflar va h.k.) HTML ko'rinishida qayta tiklaydi
    old_text = callback.message.html_text or ""
    await callback.message.edit_text(old_text + "\n\n✅ <b>Qabul qilindi</b>")
    await admin_service.notify_customer_order_accepted(bot, order)
    await callback.answer("Belgilandi")


@admin_router.callback_query(F.data.startswith("custom_contacted:"))
async def custom_order_contacted(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return

    custom_order_id = int(callback.data.split(":", 1)[1])
    order, reason = await admin_service.mark_custom_order_contacted(custom_order_id)
    if order is None:
        await callback.answer("Buyurtma topilmadi", show_alert=True)
        return

    # DIQQAT: aiogram caption uchun html_text kabi tayyor "html_caption" bermaydi,
    # shuning uchun oddiy (formatlanmagan) matnga qo'shib qo'yamiz - bu yerda
    # caption'da maxsus HTML belgilar ishlatilmagani uchun xavfsiz.
    old_caption = callback.message.caption or ""
    await callback.message.edit_caption(caption=old_caption + "\n\n✅ Bog'lanildi")
    await callback.answer("Belgilandi")


@admin_router.callback_query(F.data.startswith("topup_approve:"))
async def topup_approve(callback: CallbackQuery, bot: Bot):
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return

    request_id = int(callback.data.split(":", 1)[1])
    req, new_balance, reason = await admin_service.approve_topup(request_id)
    if req is None:
        msg = "So'rov topilmadi" if reason == "not_found" else "Bu so'rov allaqachon ko'rib chiqilgan"
        await callback.answer(msg, show_alert=True)
        return

    if callback.message.photo:
        old_caption = callback.message.caption or ""
        await callback.message.edit_caption(caption=old_caption + "\n\n✅ Tasdiqlandi")
    else:
        old_text = callback.message.html_text or ""
        await callback.message.edit_text(old_text + "\n\n✅ Tasdiqlandi")

    await admin_service.notify_customer_topup_approved(bot, req, new_balance)
    await callback.answer("Tasdiqlandi")


@admin_router.callback_query(F.data.startswith("topup_reject:"))
async def topup_reject(callback: CallbackQuery, bot: Bot):
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return

    request_id = int(callback.data.split(":", 1)[1])
    req, reason = await admin_service.reject_topup(request_id)
    if req is None:
        msg = "So'rov topilmadi" if reason == "not_found" else "Bu so'rov allaqachon ko'rib chiqilgan"
        await callback.answer(msg, show_alert=True)
        return

    if callback.message.photo:
        old_caption = callback.message.caption or ""
        await callback.message.edit_caption(caption=old_caption + "\n\n❌ Rad etildi")
    else:
        old_text = callback.message.html_text or ""
        await callback.message.edit_text(old_text + "\n\n❌ Rad etildi")

    await admin_service.notify_customer_topup_rejected(bot, req)
    await callback.answer("Rad etildi")


@admin_router.message(Command("promo"))
async def create_promo_command(message: Message, command: CommandObject):
    """Faqat admin uchun: /promo KOD FOIZ [MAX_ISHLATISH]
    Masalan: /promo YANGI10 10 50  -> "YANGI10" kodi 10% chegirma beradi, 50 marta ishlatilishi mumkin
             /promo YANGI10 10     -> cheklovsiz (istalgancha marta ishlatilishi mumkin)"""
    if not _is_admin(message.from_user.id):
        return  # oddiy foydalanuvchilarga bu buyruq ko'rinmasin/ishlamasin

    if not command.args:
        await message.answer(
            "Foydalanish: <code>/promo KOD FOIZ [MAX_ISHLATISH]</code>\n"
            "Masalan: <code>/promo YANGI10 10 50</code>"
        )
        return

    parts = command.args.split()
    if len(parts) not in (2, 3):
        await message.answer(
            "Noto'g'ri format. Foydalanish: <code>/promo KOD FOIZ [MAX_ISHLATISH]</code>"
        )
        return

    code = parts[0].upper()
    try:
        percent = int(parts[1])
        max_uses = int(parts[2]) if len(parts) == 3 else None
    except ValueError:
        await message.answer("FOIZ va MAX_ISHLATISH butun son bo'lishi kerak.")
        return

    if not (1 <= percent <= 100):
        await message.answer("FOIZ 1 dan 100 gacha bo'lishi kerak.")
        return

    await db.create_promo(code, percent, max_uses)
    limit_text = f"{max_uses} marta" if max_uses else "cheklovsiz"
    await message.answer(
        f"✅ Promo-kod yaratildi: <b>{code}</b> — {percent}% chegirma, {limit_text} ishlatiladi."
    )
