# Figo3D bot — @figo3D_bot

Bu bot mijozlarga 3D-print qilingan haykalcha, kalitcha va sovg'a buyumlarini
katalogdan tanlab, buyurtma berish imkonini beradi. Buyurtma qabul qilingach,
sizga (adminga) avtomatik xabar keladi.

**Hozircha ishlaydigan qism:** Bosh menyudagi pastki tugmalar
(**🗂 Katalog, 🛒 Savat, 📦 Buyurtmalarim, 👤 Profil, 🎨 Shaxsiy buyurtma,
☎️ Aloqa**) orqali mijoz **BARCHA** amalni — katalogni ko'rish, savatga
qo'shish, **butun buyurtma berish jarayonini** (ism/telefon/manzil,
promo-kod, to'lov usuli — hamyon/karta/naqd), **profilni** saqlash,
**buyurtmalar tarixini** ko'rish, **shaxsiy (o'z rasmidan) buyurtma
so'rovi** yuborish va **aloqa ma'lumotlarini** ko'rish — oddiy Telegram
xabar almashinuvi orqali qiladi (bu eng barqaror usul). Bundan tashqari,
xabar yozish maydoni yonidagi **"🛍 Do'kon"** tugmasi orqali ochiladigan
veb-do'kon (Mini App) ham bor — u endi FAQAT mahsulotlarni chiroyli
(rasm-kartochka) ko'rinishda ko'rish va savatga qo'shish uchun qulay
muqobil (pastda "Veb-do'kon (Mini App)" bo'limiga qarang). Bundan tashqari:
mijoz sharhlari va reytingi, ichki hamyon (balans), Telegram ichida karta
orqali to'lov (Click/Payme ulangach), **bir nechta admin/hamkorga ruxsat
berish**, va — eng muhimi — endi **admin veb-paneli** orqali buyurtmalarni,
hisob to'ldirish so'rovlarini va mahsulotlarni chatga yozmasdan, chiroyli
veb-sahifadan boshqarish mumkin (pastda "Admin veb-paneli" bo'limiga
qarang).

**Keyingi bosqichda qo'shiladi:** hozircha hisobni to'ldirish (hamyon)
qo'lda admin tasdig'i bilan ishlaydi (mijoz to'lov qilib, chekining
skrinshotini yuboradi, siz "✅ Tasdiqlash" bosasiz). Click provider tokeningiz
kelgach, buyurtmani Telegram ichida to'g'ridan-to'g'ri karta bilan to'lash
ham yoqiladi (4-qadamdagi `PAYMENT_PROVIDER_TOKEN` bo'limiga qarang).

---

## 1-qadam: Bot tokenini toping

Siz allaqachon @BotFather orqali @figo3D_bot botini yaratgansiz. Token esa
BotFather bilan yozishmangizda saqlanган — agar yo'qotgan bo'lsangiz:

1. Telegram'da **@BotFather** ga yozing
2. `/mybots` → **Figo 3D** → **API Token** tugmasini bosing
3. Chiqqan uzun kodni (masalan `7123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)
   nusxalab, xavfsiz joyga saqlab qo'ying — bu keyingi qadamlarda kerak bo'ladi.

## 2-qadam: O'zingizning Telegram ID raqamingizni toping

Buyurtmalar sizga shu ID orqali yuboriladi.

1. Telegram'da **@userinfobot** ga yozing (yoki `/start` bosing)
2. U sizga sizning ID raqamingizni yuboradi (masalan `123456789`)
3. Shu raqamni saqlab qo'ying

## 3-qadam: Kodni GitHub'ga joylashtirish

Render.com kodni GitHub orqali oladi, shuning uchun avval GitHub'da bepul
akkaunt va repository (loyiha "papkasi") kerak.

1. [github.com](https://github.com) saytida ro'yxatdan o'ting (agar hali yo'q bo'lsa)
2. Yuqori o'ng burchakdagi **+** tugmasi → **New repository**
3. Repository nomi: `figo3d-bot` deb yozing → **Create repository**
4. Ochilgan sahifada **"uploading an existing file"** havolasini bosing
5. Shu arxivdagi barcha fayllarni (bot.py, config.py, db.py, products.py,
   keyboards.py, requirements.txt, handlers papkasi va boshqalar) shu yerga
   sudrab tashlang (drag & drop) — **faqat `.env` faylini yuklamang**, u shaxsiy
   tokeningizni saqlaydi
6. Pastda **Commit changes** tugmasini bosing

## 4-qadam: Render.com'da joylashtirish

1. [render.com](https://render.com) saytida ro'yxatdan o'ting — "Sign up with
   GitHub" orqali kirsangiz qulayroq bo'ladi (kredit karta talab qilinmaydi)
2. Dashboard'da **New +** → **Web Service**
3. GitHub'dagi `figo3d-bot` repositoryingizni tanlang va **Connect** bosing
4. Sozlamalarni to'ldiring:
   - **Name:** `figo3d-bot` (yoki xohlagan nom)
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
   - **Instance Type:** Free
5. Pastroqda **Environment Variables** bo'limini toping va qo'shing:
   - `BOT_TOKEN` = 1-qadamda olgan tokeningiz
   - `ADMIN_CHAT_ID` = 2-qadamda olgan ID raqamingiz
   - `ADMIN_IDS` = **ixtiyoriy.** Yana boshqa odamlarga (masalan 3D-print
     hamkoringizga) ham admin ruxsati bermoqchi bo'lsangiz, ularning ID
     raqamlarini vergul bilan ajratib shu yerga yozing (masalan:
     `111111111,222222222`) — pastda "Bir nechta admin qo'shish" bo'limiga
     qarang
   - `CONTACT_INFO` = **ixtiyoriy.** Mini App'ning "Aloqa" bo'limida
     mijozlarga ko'rsatiladigan matn (masalan: `@figo3d_support yoki +998 90
     123 45 67`)
   - `PAYMENT_INFO` = mijozlarga ko'rsatiladigan to'lov rekvizitlaringiz
     (masalan: `Karta: 8600 1234 5678 9012 - F. Familiya (Payme/Click ham shu
     kartaga)`) — bu hisobni to'ldirish so'rovida mijozga ko'rsatiladi
   - `PAYMENT_PROVIDER_TOKEN` = **hozircha bo'sh qoldiring.** Click'dan API
     tokenini olganingizda shu nom bilan qo'shasiz (pastda "Click/Payme
     to'lovini ulash" bo'limiga qarang) — token yo'qligida bot avvalgidek
     hamyon/naqd usullari bilan ishlayveradi, hech narsa buzilmaydi
   - `TURSO_DATABASE_URL` va `TURSO_AUTH_TOKEN` = **tavsiya etiladi**,
     lekin ixtiyoriy — ma'lumotlaringiz (buyurtmalar, hamyon balanslari,
     mahsulotlar) Render diski tozalanganda ham yo'qolib qolmasligi uchun.
     Pastda **"Ma'lumotlar bazasini doimiy saqlash (Turso)"** bo'limida
     qadam-baqadam tushuntirilgan — hozircha bo'sh qoldirsangiz ham bot
     ishlayveradi (avvalgidek, faqat mahalliy fayl bilan)
6. **Create Web Service** tugmasini bosing

Render avtomatik ravishda kodni yuklab oladi, kerakli kutubxonalarni
o'rnatadi va botni ishga tushiradi (bu 2-5 daqiqa vaqt oladi). Jarayonni
"Logs" bo'limidan kuzatib borishingiz mumkin — oxirida
`Webhook rejimi yoqildi: https://...` degan qatorni ko'rsangiz, hammasi
tayyor.

## 5-qadam: Tekshirish

Telegram'da @figo3D_bot'ga o'ting va `/start` bosing — bosh menyu chiqishi
kerak. Katalogdan mahsulot tanlab, savatga qo'shib, buyurtma berib ko'ring —
buyurtma tugagach, sizning shaxsiy Telegram'ingizga (2-qadamda ko'rsatgan ID
orqali) yangi buyurtma haqida xabar kelishi kerak.

**Eslatma:** bepul Render rejasi 15 daqiqa hech kim yozmasa botni "uxlatib
qo'yadi" — keyingi xabarga javob ~30-60 soniya kechikishi mumkin (bu MVP
bosqichida muammo emas).

Shundan so'ng, botga **`/admin`** deb yozib, o'zingizning haqiqiy
mahsulotlaringizni (rasmlari bilan) qo'shishni boshlashingiz mumkin — pastda
"Mahsulot qo'shish/o'chirish" bo'limiga qarang.

---

## Yangi imkoniyatlar qanday ishlatiladi

### 🛍 Veb-do'kon (Mini App) — endi FAQAT katalog va savat uchun

⚠️ **O'zgardi:** avval buyurtma berish, profil, buyurtmalar tarixi, shaxsiy
buyurtma va aloqa — hammasi shu Mini App ichida edi. Amalda bu ba'zan
ishonchsiz chiqib qoldi: mijoz katta tugmani bossa ham serverga hech qanday
so'rov ketmay, savat/buyurtma "qotib qolgandek" ko'rinadigan holatlar
bo'ldi. Shuning uchun endi bu funksiyalarning HAMMASI oddiy, ancha
barqaror Telegram chat tugmalariga (bosh menyuga) qaytarildi — pastdagi
"Pastki tugmalar qaytarildi" bo'limiga qarang.

Xabar yozish maydoni yonidagi doimiy **"🛍 Do'kon"** tugmasi hamon bor va
haqiqiy **veb-sahifa** sifatida ochiladi (Telegram buni "Mini App" deb
ataydi), lekin endi u ancha soddalashtirilgan — faqat:

- Mahsulotlarni rasm-kartochkalar 2 ustunli to'r ko'rinishida ko'rish,
  bo'limlar tepada tab sifatida, mahsulot ustiga bosilganda katta rasm +
  galereya va tavsif
- Savatga qo'shish va savatdagi miqdorni ➕/➖ bilan o'zgartirish

Savat oynasida endi "Buyurtma berish" tugmasi YO'Q — buning o'rniga
mijozga "buyurtmani rasmiylashtirish uchun chatdagi '🛒 Savat' tugmasini
bosing" degan eslatma chiqadi. Bu ataylab shunday: savat bitta umumiy
ma'lumotlar bazasida saqlanadi, shuning uchun Mini App'da qo'shilgan
mahsulot chatdagi "🛒 Savat"da ham darhol ko'rinadi — mijoz shunchaki
Mini App'ni yopib, chatdan davom etadi.

**Muhim:** bu faqat Render'da (haqiqiy https manzil bilan) ishlaydi —
mahalliy kompyuteringizda sinaganingizda (https yo'q joyda) "🛍 Do'kon"
tugmasi umuman ko'rinmaydi — hech narsa buzilmaydi, chunki barcha asosiy
funksiya baribir chat tugmalari orqali ishlayveradi.

### Admin veb-paneli — buyurtma/mahsulotlarni chatsiz, veb-sahifadan boshqarish

Endi `/admin` buyrug'ini yozganda chiqadigan xabarda **"🖥 Boshqaruv panelini
ochish"** tugmasi bor — bu ham xuddi mijozlar do'koni kabi veb-sahifa
(Mini App) ko'rinishida ochiladi, lekin FAQAT sizga (va ruxsat bergan
hamkorlaringizga) mo'ljallangan. Tab'lari:

- **Buyurtmalar** — hali "qabul qilindi"ga o'tmagan buyurtmalar ro'yxati,
  har birida "✅ Qabul qildim" tugmasi
- **Shaxsiy** — hali javob berilmagan shaxsiy buyurtma so'rovlari (rasm bilan)
- **To'ldirish** — kutilayotgan hisob to'ldirish so'rovlari, "✅ Tasdiqlash"/
  "❌ Rad etish" tugmalari bilan
- **Mahsulotlar** — mavjud mahsulotlar ro'yxati + pastki o'ng burchakdagi
  "➕" tugmasi orqali yangi mahsulot qo'shish (bir nechta rasm bilan birga)

**Xavfsizlik:** panelga FAQAT `ADMIN_CHAT_ID`/`ADMIN_IDS` ro'yxatidagi
Telegram ID'lar kira oladi — Telegram'ning o'zi imzolab yuboradigan
maxfiy ma'lumot (`initData`) har bir so'rovda serverning o'zida tekshiriladi,
shuning uchun havolani bilib olgan boshqa odam ham kira olmaydi. Chatdagi
eski usul (`/admin` orqali mahsulot qo'shish, buyurtma tugmalari va h.k.)
ham avvalgidek ishlayveradi — ikkalasidan xohlaganingizni ishlatishingiz
mumkin, ikkalasi bir xil ma'lumot bilan ishlaydi.

**Bu — yangi imkoniyat, ishlatishdan oldin diqqat bilan sinab ko'ring**
(masalan bitta sinov mahsulot qo'shib-o'chirib ko'ring), ayniqsa real
buyurtmalar/to'lovlarni tasdiqlashdan oldin. Va mijozlar do'koni kabi, bu
ham faqat Render'da (haqiqiy https manzil bilan) ishlaydi — mahalliy
kompyuteringizda sinaganingizda "🖥 Boshqaruv panelini ochish" tugmasi
umuman ko'rinmaydi, chatdagi eski `/admin` usuli esa ishlayveradi.

### Bir nechta admin qo'shish

Agar buyurtmalarni siz bilan birga boshqa odam ham (masalan 3D-print
hamkoringiz) ko'rib, qabul qilishini xohlasangiz — Render'ning Environment
Variables bo'limida **YANGI** o'zgaruvchi sifatida `ADMIN_IDS` nomi bilan
(bu `ADMIN_CHAT_ID`dan BOSHQA, alohida nom) ularning Telegram ID
raqamlarini vergul bilan ajratib qo'shing (masalan: `111111111,222222222`).

⚠️ **Muhim:** `ADMIN_CHAT_ID`ni qayta yozmang/o'zgartirmang — u sizda
allaqachon bor, Render esa bir xil nomli o'zgaruvchini ikki marta
qo'shishga ruxsat bermaydi ("Duplicate key... is not allowed" degan xato
shundan). Ikkinchi (va undan ko'p) odamlar UCHUN har doim `ADMIN_IDS`
degan **BOSHQA** nom ishlatiladi — `ADMIN_CHAT_ID` esa o'zgarishsiz qoladi,
u avtomatik ravishda `ADMIN_IDS` ro'yxatiga qo'shib olinadi.

Shundan so'ng: yangi buyurtma, shaxsiy buyurtma so'rovi va hisob to'ldirish
so'rovi haqidagi xabarlar **HAMMA** adminlarga yuboriladi, va hammasi
`/admin` buyrug'i hamda admin veb-paneliga kira oladi.

### Savat: miqdorni ➕/➖ qilish

Endi "Savatga qo'shish" tugmasi bosilganda mahsulot sahifasidagi tugma
darhol o'zgarib, savatda nechta borligini ko'rsatadi (masalan "➕ Yana
qo'shish (savatda: 2 ta)"), va yuqorida qisqa xabar ham chiqadi — shu bilan
qo'shilgani sezilarli bo'ladi. Savat sahifasida ("🛒 Savat" tugmasi) har bir
mahsulot qatorida ➖ va ➕ tugmalari bor — ular orqali miqdorni birma-bir
kamaytirish yoki oshirish mumkin (0 ga tushsa, mahsulot savatdan butunlay
o'chadi). Butunlay o'chirish uchun bir necha marta ➖ bosish kifoya, yoki
"🗑 Savatni tozalash" bilan hammasini bir yo'la tozalash mumkin.

### Pastki tugmalar qaytarildi

Bir muddat (yuqorida tasvirlangan sabab bilan) bosh menyudagi doimiy
matnli tugmalar Render'da (production'da) butunlay olib tashlangan edi —
hammasi Mini App ichida bo'lishi kerak edi. Endi bu **qaytarildi**: bosh
menyuda doim (production'da ham) 🗂 Katalog, 🛒 Savat, 📦 Buyurtmalarim,
👤 Profil, 🎨 Shaxsiy buyurtma, ☎️ Aloqa tugmalari ko'rinadi va BARCHA
amal shular orqali ishlaydi. "🛍 Do'kon" Mini App tugmasi ham qoladi —
u endi faqat katalog+savat uchun qulay qo'shimcha (yuqoridagi bo'limga
qarang).

### Shaxsiy profil va manzilni tasdiqlash

"👤 Profil" tugmasi orqali mijoz o'z ism-familiyasi, telefon raqami va
manzilini bir marta kiritib saqlab qo'yishi mumkin. Keyingi safar buyurtma
berayotganda ("🛒 Savat" → "✅ Buyurtma berish"), bot ism/telefon/manzilni
BARIBIR HAR DOIM birma-bir so'raydi — lekin agar saqlangan qiymat bo'lsa,
u pastdagi tugmada ko'rinadi (masalan avvalgi manzil tugma sifatida
chiqadi) — mijoz shuni bosib bir zumda tasdiqlashi, yoki o'rniga
yangisini yozib yuborishi mumkin (masalan do'stiga sovg'a
yuborayotganda, boshqa manzil bilan). Bu ataylab shunday: manzil
HECH QACHON ko'rsatmasdan, sinovsiz avtomatik ishlatilmaydi — mijoz doim
uni ko'rib, tasdiqlab o'tadi. Har bir muvaffaqiyatli buyurtmadan so'ng eng
oxirgi kiritilgan ma'lumot profilga saqlanib qoladi.

### Ichki hamyon (balans) tizimi

Profil sahifasida mijoz joriy balansini ko'radi. "💰 Hisobni to'ldirish"
tugmasi orqali: qancha to'ldirmoqchiligini yozadi → botning `PAYMENT_INFO`
rekvizitlarini ko'radi → to'lov qilgach, chekning skrinshotini yuboradi
(yoki skrinshotsiz ham davom etishi mumkin). So'rov sizga (admin) darhol
skrinshot va "✅ Tasdiqlash" / "❌ Rad etish" tugmalari bilan keladi.
**Tasdiqlaganingizda** — va faqat shundagina — mablag' mijozning hamyoniga
qo'shiladi. Keyingi buyurtmalarda, agar hamyonda yetarli mablag' bo'lsa,
mijoz "💰 Hamyondan to'lash" tugmasi bilan darhol to'lashi mumkin (operator
bilan alohida kelishmasdan) — bo'lmasa, avvalgidek "💵 Naqd/karta (operator
bilan)" orqali davom etadi. Bu — Payme/Click API ulanmaguncha ishlatiladigan
ichki to'lov tizimi; API ulangach, "Hisobni to'ldirish" qismini avtomatik
to'lovga almashtirish mumkin bo'ladi.

### Mahsulot qo'shish/o'chirish — endi kod bilan ishlash SHART EMAS

**Bu eng muhim o'zgarish.** Avval mahsulot va rasmlarni qo'shish uchun
`products.py` faylini qo'lda tahrirlab, GitHub'ga yuklab, qayta deploy
qilish kerak edi — va aynan shu jarayon sizning "rasmlar har safar
yangilaganimda o'chib ketyapti" degan muammoingizning sababi edi: men har
safar yangi tuzatish yuborganimda, arxivdagi `products.py` doim bo'sh
(namunaviy) rasmlar bilan qaytadan yaratilar edi — va siz butun arxivni
qayta yuklaganingizda, bu sizning avval qo'shgan real rasmlaringizni
tasodifan ustidan bosib, o'chirib qo'yardi. Kodning o'zi yoki Render'ning
aybi emas edi — muammo shu "har safar hammasini qayta yuklash" jarayonida
edi.

Endi mahsulotlar (nomi, narxi, rasmlari, videosi) kodda emas, botning
bazasida saqlanadi — bundan buyon men yuboradigan yangilanishlar
mahsulotlaringizga umuman tegmaydi. Qo'shish uchun:

1. Botga **`/admin`** buyrug'ini yozing (faqat siz — `ADMIN_CHAT_ID` — buni
   ko'rasiz va ishlata olasiz)
2. **"➕ Yangi mahsulot qo'shish"** tugmasini bosing
3. Bo'lim (mavjudidan tanlang yoki yangisini yozing) → nomi → tavsifi →
   narxi → rasmlarni birma-bir yuboring (tugagach "✅ Rasmlar tayyor") →
   xohlasangiz aylanish videosi → "✅ Saqlash"
4. Tayyor — mahsulot **darhol** katalogda ko'rinadi, hech qanday GitHub yoki
   Render bilan ishlash shart emas

Mahsulotni o'chirish uchun `/admin` → **"📋 Mahsulotlar ro'yxati"** →
kerakli mahsulot ostidagi **"🗑 O'chirish"** tugmasi (bosgach, "✅ Ha,
o'chirish" bilan tasdiqlaysiz).

Rasm sifatida yuborilgan har qanday fotosurat, video uchun esa video fayl
(GIF emas) qabul qilinadi. 2 tadan ortiq rasm/video bo'lsa, bot mijozga
ularni avtomatik "albom" ko'rinishida ko'rsatadi.

### Mijoz sharhlari

Mijozlar mahsulot sahifasida "⭐ Baho berish" tugmasi orqali 1-5 yulduz va
ixtiyoriy izoh qoldirishlari mumkin. O'rtacha baho va sharhlar soni mahsulot
sahifasida avtomatik ko'rinadi, qo'shimcha sozlash shart emas.

### Promo-kod (chegirma) yaratish

Faqat siz (admin) botga quyidagi buyruqni yozib, yangi chegirma kodi
yaratishingiz mumkin:

```
/promo YANGI10 10 50
```

Bu yerda `YANGI10` — kod nomi (mijozlar shu so'zni yozadi), `10` — chegirma
foizi, `50` — kod necha marta ishlatilishi mumkinligi (bu qismni
o'chirib qoldirsangiz, kod cheklovsiz ishlatiladi: `/promo YANGI10 10`).
Mijozlar buyurtma berayotganda manzildan keyin promo-kodni kiritish
imkoniyatiga ega bo'ladi.

### Shaxsiy buyurtma (o'z rasmidan)

Mijoz bosh menyudagi "🎨 Shaxsiy buyurtma" tugmasini bosib, o'z rasmini
yuboradi va nima xohlashini yozadi. Bu maxsus buyurtma bo'lgani uchun narx
oldindan belgilanmaydi — so'rov to'g'ridan-to'g'ri sizga (fotosurat bilan
birga) keladi, narxni mijoz bilan siz shaxsan kelishasiz.

### Click/Payme to'lovini ulash (Telegram ichida karta bilan to'lash)

Click'dan API (provider) tokenini olganingizda, buyurtmani Telegram ichida
to'g'ridan-to'g'ri karta bilan to'lash imkoniyatini yoqish uchun:

1. **@BotFather** ga yozing → `/mybots` → **Figo 3D** → **Payments**
2. Ro'yxatdan **Click** (yoki Payme, ikkalasi ham qo'llab-quvvatlanadi)ni
   tanlab, ular bergan sozlash bo'yicha ulaning — oxirida BotFather sizga
   uzun bir **provider token** beradi
3. Shu tokenni nusxalab, Render'ning Environment Variables bo'limiga
   `PAYMENT_PROVIDER_TOKEN` nomi bilan qo'shing → **Save Changes**
   (Render avtomatik qayta ishga tushiradi)

Shundan so'ng, buyurtma tasdiqlash bosqichida mijozlarga avtomatik ravishda
yangi **"💳 Karta orqali (Click/Payme)"** tugmasi ham chiqadi — bosilganda
Telegram'ning o'z to'lov oynasi ochiladi, mijoz karta orqali to'laydi, va
to'lov muvaffaqiyatli bo'lishi bilan buyurtma avtomatik yaratilib, sizga
xabar keladi (hech qanday qo'lda tasdiqlash shart emas — bu hamyonni
to'ldirish jarayonidan farqli o'laroq, to'liq avtomatik).

Token hali yo'q bo'lsa — hech narsa qilish shart emas, bu tugma shunchaki
ko'rinmay turadi, mijozlar hamyon yoki naqd/karta (operator bilan)
usullaridan foydalanaveradi.

---

## Ma'lumotlar bazasini doimiy saqlash (Turso)

Render'ning **bepul** tarifida disk "doimiy" emas — bot qayta ishga
tushganda (masalan, uzoq vaqt ishlatilmay qolgach, yoki texnik sabablarga
ko'ra) `figo3d.db` fayli (demak barcha buyurtmalar, sharhlar, promo-kodlar,
mijozlarning hamyon balanslari, saqlangan profillari va mahsulotlar/
rasmlar) tozalanib ketishi mumkin edi.

✅ **Bu endi hal qilindi** — bot endi ixtiyoriy ravishda **Turso** (bepul,
doimiy, SQLite-mos bulut baza) bilan ishlay oladi: har bir yozuvdan
(buyurtma, profil, mahsulot va h.k.) so'ng ma'lumot darhol bulutga ham
nusxalanadi, shuning uchun Render diski tozalansa ham hech narsa
yo'qolmaydi. Sozlash ixtiyoriy va tez:

1. [turso.tech](https://turso.tech) saytida bepul akkaunt oching (kredit
   karta talab qilinmaydi)
2. Yangi baza (database) yarating
3. Baza sahifasidan **"Database URL"** (`libsql://...` bilan boshlanadi) va
   **"Auth Token"**ni nusxalab oling
4. Render'ning **Environment Variables** bo'limiga qo'shing:
   - `TURSO_DATABASE_URL` = nusxalagan Database URL
   - `TURSO_AUTH_TOKEN` = nusxalagan Auth Token
5. **Save Changes** — Render botni avtomatik qayta ishga tushiradi

Ikkalasini ham bo'sh qoldirsangiz — muammo emas, bot avvalgidek faqat
mahalliy fayl bilan ishlayveradi (lekin yuqoridagi yo'qolish xavfi
qoladi). Bepul reja: 500 million o'qish/oy, 10 million yozish/oy, 5GB joy —
kichik-o'rta do'kon uchun yetarlicha.

✅ **Xavfsizlik to'ri qo'shildi:** endi agar `TURSO_DATABASE_URL`/
`TURSO_AUTH_TOKEN` noto'g'ri bo'lsa (masalan token eskirgan/bekor qilingan
bo'lsa), bot BUTUNLAY ishdan to'xtab qolmaydi — xatoni "Logs"ga aniq yozib,
avtomatik ravishda oddiy mahalliy fayl rejimiga tushib, ishlashda davom
etadi (Turso to'g'rilanguncha). Shunday bo'lsa, "Logs" bo'limida
`Turso bilan ULANIB BO'LMADI` degan qatorni ko'rasiz — bu holatda pastdagi
"Turso xatosi chiqsa" bo'limiga qarang.

Ulanish muvaffaqiyatli bo'lsa, "Logs" bo'limida
`Turso bilan dastlabki sinxronizatsiya muvaffaqiyatli` degan qatorni
ko'rasiz — shundan so'ng bir marta sinov buyurtma berib/mahsulot qo'shib
ko'ring, muammo chiqsa menga ayting.

#### Turso xatosi chiqsa (masalan "invalid JWT token")

Agar Logs'da token/ulanish bilan bog'liq xato ko'rinsa (masalan
`invalid JWT token: role was invalidated after token was issued` yoki
`401 Unauthorized`) — bu odatda token Turso tomonida bekor qilingan yoki
noto'g'ri nusxalangan degani. Turso'ning o'zi tokenlarni faqat siz
(yoki Turso paneli) aniq buyruq bergandagina bekor qiladi — masalan bitta
tokenni ikki marta ustma-ust "yaratish/rotate qilish" natijasida avvalgisi
avtomatik bekor bo'lishi mumkin. Tuzatish:

1. [turso.tech](https://turso.tech) saytida bazangizga kiring
2. Yangi (butunlay FRESH) **Auth Token** yarating — eskisiga tegmang, yangi
   nusxalab oling
3. Render'da `TURSO_AUTH_TOKEN` qiymatini shu yangi token bilan
   ALMASHTIRING (eskisini butunlay o'chirib, yangisini joylashtiring —
   boshida/oxirida bo'sh joy qolmasligiga e'tibor bering)
4. **Save Changes** — qayta deploy bo'lgach, Logs'ni qayta tekshiring

Bu davrda ham (token tuzatilmagunicha) bot mijozlar uchun to'liq ishlayveradi
— faqat ma'lumotlar Turso'ga emas, mahalliy faylga saqlanadi.

#### ✅ Tuzatildi: "savat/buyurtma berish yo'qolib qolishi" (`ValueError: file is not a database`)

Agar avval Logs'da `ValueError: file is not a database` degan xato bilan
birga savatga mahsulot qo'shish yoki "✅ Buyurtma berish" ishlamay qolgan
bo'lsa — sababi topildi va tuzatildi: fondagi davriy Turso sinxronlash
vazifasi (`start_periodic_sync`, har 25 soniyada ishlaydi) mijozning
so'rovi (masalan `/api/cart`) bilan **bir vaqtning o'zida**, bir-biridan
himoyalanmagan holda, bitta bazaga ulanishga tegishi mumkin edi — bu esa
vaqti-vaqti bilan mahalliy baza faylini buzib qo'yardi. Endi bu ikkalasi
hech qachon bir vaqtda ishlamaydi (bir xil qulf — "lock" orqali
navbat bilan ishlaydi). Bu narsa avtomatik tuzatilgan, sizdan hech qanday
qo'shimcha sozlash talab qilinmaydi — shu zip'ni GitHub'ga yuklab, Render
qayta deploy bo'lishini kutsangiz bas.
