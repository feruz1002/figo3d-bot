"""Ruxsat etilgan barcha adminlarga (config.ADMIN_IDS) xabar yuborish uchun
umumiy funksiya - endi bitta emas, bir nechta odam admin bo'lishi mumkin
(masalan siz + 3D-print hamkoringiz), shuning uchun yangi buyurtma/so'rov
haqidagi xabar HAMMASIGA yetib borishi kerak."""
from config import ADMIN_IDS


async def notify_admins(bot, text: str | None = None, photo=None, caption: str | None = None, reply_markup=None):
    """ADMIN_IDS ro'yxatidagi har bir odamga xabar yuboradi. Agar `photo`
    berilsa - rasm+caption, aks holda oddiy matn yuboriladi. Ulardan
    bittasi botni bloklagan yoki hali /start bosmagan bo'lsa ham, bu boshqa
    adminlarga xabar yetib borishiga to'sqinlik qilmaydi."""
    for admin_id in ADMIN_IDS:
        try:
            if photo is not None:
                await bot.send_photo(admin_id, photo=photo, caption=caption, reply_markup=reply_markup)
            else:
                await bot.send_message(admin_id, text, reply_markup=reply_markup)
        except Exception:
            pass
