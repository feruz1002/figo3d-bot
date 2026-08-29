"""Admin (yoki 3D-print hamkor) uchun buyruqlar:
- Buyurtmani bosqichma-bosqich yuritish: Qabul qilish -> Yig'ish -> Chiqarib
  yuborilgan -> Arxiv (yoki istalgan bosqichda Muammo deb belgilash)
- Shaxsiy buyurtma bo'yicha mijoz bilan bog'langanini belgilash
- Yangi promo-kod yaratish (/promo buyrug'i orqali)

DIQQAT: har bir bosqich o'tishda xabarning `reply_markup`i ANIQ (aniq
qiymat bilan) qayta yuboriladi - agar `reply_markup` berilmasa, Telegram
buni "klaviaturani o'zgarishsiz qoldirish" deb tushunadi, ya'ni ESKI
tugma (masalan "✅ Qabul qildim") xabarda QOLIB KETADI va admin uni
yana bossa, chalkashlik chiqishi mumkin edi. Shuning uchun har safar
KEYINGI bosqichga mos klaviatura (yoki yakunda bo'sh klaviatura)
ANIQ beriladi."""
from html import escape as _html_escape

from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import admin_service
import db
from config import is_admin as _is_admin
from handlers.catalog import format_price
from handlers.states import AdminOrderStates, AdminTopupStates
from keyboards import (
    BTN_CANCEL,
    admin_order_archive_keyboard,
    admin_order_shipping_keyboard,
    cancel_only_keyboard,
    empty_keyboard,
    main_menu_keyboard,
)

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
    await callback.message.edit_text(
        old_text + "\n\n✅ <b>Qabul qilindi</b> — yig'ilmoqda",
        reply_markup=admin_order_shipping_keyboard(order_id, order["user_id"]),
    )
    await admin_service.notify_customer_order_accepted(bot, order)
    await callback.answer("Belgilandi")


@admin_router.callback_query(F.data.startswith("order_ship:"))
async def order_ship(callback: CallbackQuery, bot: Bot):
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return

    order_id = int(callback.data.split(":", 1)[1])
    order, reason = await admin_service.ship_order(order_id)
    if order is None:
        await callback.answer("Buyurtma topilmadi", show_alert=True)
        return

    old_text = callback.message.html_text or ""
    await callback.message.edit_text(
        old_text + "\n\n🚚 <b>Chiqarib yuborildi</b>",
        reply_markup=admin_order_archive_keyboard(order_id, order["user_id"]),
    )
    await admin_service.notify_customer_order_shipped(bot, order)
    await callback.answer("Belgilandi")


@admin_router.callback_query(F.data.startswith("order_archive:"))
async def order_archive(callback: CallbackQuery, bot: Bot):
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return

    order_id = int(callback.data.split(":", 1)[1])
    order, reason = await admin_service.archive_order(order_id)
    if order is None:
        await callback.answer("Buyurtma topilmadi", show_alert=True)
        return

    old_text = callback.message.html_text or ""
    await callback.message.edit_text(
        old_text + "\n\n📁 <b>Yetkazildi (arxivlandi)</b>",
        reply_markup=empty_keyboard(order["user_id"]),
    )
    await admin_service.notify_customer_order_archived(bot, order)
    await callback.answer("Arxivlandi")


# MUHIM (foydalanuvchi so'rovi bilan 27-avgust kuni qo'shildi): "⚠️ Muammo"
# endi ikki bosqichda ishlaydi - avval sababni (izohni) chatda so'raymiz,
# faqat javob kelgach buyurtma haqiqatan "Muammo" deb belgilanadi. Shu
# sabab bu FSM holati (AdminOrderStates.waiting_problem_reason) orqali
# amalga oshirilgan - callback tugmasi faqat SO'ROVNI boshlaydi, asosiy
# ish pastdagi order_problem_finish/order_problem_cancel'da bajariladi.
@admin_router.callback_query(F.data.startswith("order_problem:"))
async def order_problem_start(callback: CallbackQuery, state: FSMContext):
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return

    order_id = int(callback.data.split(":", 1)[1])
    order = await db.get_order(order_id)
    if not order:
        await callback.answer("Buyurtma topilmadi", show_alert=True)
        return

    await state.set_state(AdminOrderStates.waiting_problem_reason)
    await state.update_data(
        problem_order_id=order_id,
        problem_chat_id=callback.message.chat.id,
        problem_message_id=callback.message.message_id,
        problem_original_text=callback.message.html_text or "",
    )
    await callback.message.answer(
        f"⚠️ #{order_id} buyurtma bo'yicha muammo sababini yozib yuboring "
        "(masalan: \"mijoz javob bermayapti\", \"mahsulot tugagan\" va h.k.).\n\n"
        "Agar sababni yozishni xohlamasangiz, \"-\" deb yuboring.",
        reply_markup=cancel_only_keyboard(),
    )
    await callback.answer()


@admin_router.message(AdminOrderStates.waiting_problem_reason, F.text == BTN_CANCEL)
async def order_problem_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi — buyurtma holati o'zgarmadi.", reply_markup=main_menu_keyboard(is_admin=True))


@admin_router.message(AdminOrderStates.waiting_problem_reason, F.text)
async def order_problem_finish(message: Message, state: FSMContext, bot: Bot):
    if not _is_admin(message.from_user.id):
        await state.clear()
        return

    data = await state.get_data()
    order_id = data.get("problem_order_id")
    chat_id = data.get("problem_chat_id")
    message_id = data.get("problem_message_id")
    original_text = data.get("problem_original_text") or ""
    await state.clear()
    if not order_id:
        return

    raw_reason = message.text.strip()
    reason = None if raw_reason in ("-", "") else raw_reason

    order, err = await admin_service.flag_order_problem(order_id, reason)
    if order is None:
        await message.answer("Buyurtma topilmadi", reply_markup=main_menu_keyboard(is_admin=True))
        return

    status_line = "\n\n⚠️ <b>Muammo deb belgilandi</b>"
    if reason:
        status_line += f"\nSabab: {_html_escape(reason)}"
    if chat_id and message_id:
        try:
            await bot.edit_message_text(
                chat_id=chat_id, message_id=message_id,
                text=original_text + status_line, reply_markup=empty_keyboard(order["user_id"]),
            )
        except Exception:
            pass  # asl xabar allaqachon o'chirilgan/topilmayotgan bo'lishi mumkin - muammo emas

    await message.answer("✅ Belgilandi.", reply_markup=main_menu_keyboard(is_admin=True))
    await admin_service.notify_customer_order_problem(bot, order)


@admin_router.message(AdminOrderStates.waiting_problem_reason)
async def order_problem_need_text(message: Message):
    """Admin matn o'rniga rasm/stiker va h.k. yuborsa - matn (yoki "-")
    kutayotganimizni eslatamiz, holatni bekor qilmaymiz."""
    await message.answer("Iltimos, matn ko'rinishida sabab yozing (yoki sababsiz belgilash uchun \"-\" yuboring).")


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


@admin_router.callback_query(F.data.startswith("resolve_contact:"))
async def resolve_contact_message(callback: CallbackQuery):
    """29-avgust: mijoz murojaatini ("💬 Operatorga yozish") to'g'ridan-
    to'g'ri chatdagi "✅ Bajarildi" tugmasi orqali yopish - admin panelning
    "💬 Murojaatlar" bo'limidagi tugma bilan bir xil natijaga olib keladi
    (db.resolve_contact_message)."""
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return

    message_id = int(callback.data.split(":", 1)[1])
    ok = await db.resolve_contact_message(message_id)
    if not ok:
        await callback.answer("Bu murojaat allaqachon bajarilgan yoki topilmadi", show_alert=True)
        return

    old_text = callback.message.html_text or ""
    await callback.message.edit_text(old_text + "\n\n✅ Bajarildi")
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


# ---------- 29-avgust: hisob to'ldirishni "boshqa summa" bilan tasdiqlash ----------
# MUHIM: skrinshotda/tranzaksiyada ko'rsatilgan summa mijoz botga yozgan
# summadan farq qilishi mumkin (kam/ko'p tushgan yoki tranzaksiyada
# xatolik bo'lgan) - shu holatlarda "✅ Tasdiqlash" (bu doim so'ralgan
# summani qo'shadi) o'rniga admin shu tugma orqali haqiqiy summani QO'LDA
# kiritib tasdiqlaydi. Asl xabar (screenshot/caption) O'ZGARTIRILMAYDI -
# tasdiqlangach, ALOHIDA yangi xabar bilan tasdiqlanadi (soddaroq va
# ishonchliroq, xabarni tahrirlash uchun message_id/chat_id'ni FSM orqali
# tashib yurish shart emas).
@admin_router.callback_query(F.data.startswith("topup_custom_amount:"))
async def topup_custom_amount_start(callback: CallbackQuery, state: FSMContext):
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return

    request_id = int(callback.data.split(":", 1)[1])
    req = await db.get_topup_request(request_id)
    if not req:
        await callback.answer("So'rov topilmadi", show_alert=True)
        return
    if req["status"] != "kutilmoqda":
        await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan", show_alert=True)
        return

    await state.set_state(AdminTopupStates.waiting_custom_amount)
    await state.update_data(request_id=request_id)
    await callback.message.answer(
        f"✏️ So'rov #{request_id} — mijoz {format_price(req['amount'])} so'm so'ragan edi.\n\n"
        "Tranzaksiya/skrinshot asosida haqiqatda necha so'm tasdiqlaysiz? Raqam bilan yozing:",
        reply_markup=cancel_only_keyboard(),
    )
    await callback.answer()


@admin_router.message(F.text == BTN_CANCEL, StateFilter(AdminTopupStates))
async def topup_custom_amount_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=main_menu_keyboard(is_admin=True))


@admin_router.message(AdminTopupStates.waiting_custom_amount)
async def topup_custom_amount_submit(message: Message, state: FSMContext, bot: Bot):
    text = (message.text or "").replace(" ", "").replace("so'm", "").strip()
    if not text.isdigit() or int(text) <= 0:
        await message.answer("Iltimos, faqat musbat son kiriting (masalan: 90000).")
        return

    data = await state.get_data()
    request_id = data.get("request_id")
    amount = int(text)
    await state.clear()

    req, new_balance, reason = await admin_service.approve_topup(request_id, amount=amount)
    if req is None:
        msg = "So'rov topilmadi" if reason == "not_found" else "Bu so'rov allaqachon ko'rib chiqilgan"
        await message.answer(f"⚠️ {msg}.", reply_markup=main_menu_keyboard(is_admin=True))
        return

    await message.answer(
        f"✅ So'rov #{request_id} — {format_price(amount)} so'm tasdiqlandi "
        f"(mijoz {format_price(req['amount'])} so'm so'ragan edi).",
        reply_markup=main_menu_keyboard(is_admin=True),
    )
    await admin_service.notify_customer_topup_approved(bot, req, new_balance)


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
