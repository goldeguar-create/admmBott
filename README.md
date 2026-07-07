# Toshkent Bearing — Telegram bot

## Bot nima qiladi
1. Mijoz `/start` yozadi -> salomlashadi, "🛒 Buyurtma berish" tugmasi chiqadi.
2. Tugma bosilsa -> brend tanlash tugmalari (SKF, KOYO, NSK, C&U, BYZ, VPZ, FAG, HRB, Barchasi).
3. Brend tanlangach -> mijoz model raqamini yozadi (masalan: `6205` yoki `6205 2RS SKF`).
4. Bot katalogdan qidiradi:
   - Aniq/qisman mos kelsa -> nomi va narxini chiqaradi.
   - Topilmasa -> o'xshash modellarni tugmalar shaklida taklif qiladi.
5. Mahsulot tasdiqlansa -> miqdorini so'raydi -> telefon raqamini so'raydi -> yetkazib berish uchun
   joylashuv (karta orqali) yoki manzilni yozma so'raydi.
6. Buyurtma tugagach mijozga tasdiq xabari, sizga (adminga) esa to'liq ma'lumot yuboriladi:
   buyurtma raqami, tg id, ism, model, narx, miqdor, telefon, manzil/joylashuv.
7. Siz mijozga botdan to'g'ridan-to'g'ri javob yozishingiz mumkin:
   ```
   /reply 123456789 Salom, buyurtmangiz tayyor, ertaga yetkazib beramiz!
   ```
   (123456789 o'rniga mijozning tg id raqami, u adminga kelgan xabarda yozilgan bo'ladi)

## O'rnatish

1. Python 3.10+ kerak.
2. Kutubxonalarni o'rnating:
   ```
   pip install -r requirements.txt
   ```
3. `.env.example` faylini `.env` deb nusxa oling va to'ldiring:
   - `BOT_TOKEN` — @BotFather orqali yaratilgan bot tokeni (BotFather'ga `/newbot` yozing).
   - `ADMIN_ID` — sizning shaxsiy Telegram ID raqamingiz (bilish uchun @userinfobot ga yozing).
4. Botni ishga tushiring:
   ```
   python3 bot.py
   ```

Bot doim ishlab turishi uchun (masalan mijozlar tunda ham yozishi mumkin bo'lsa),
uni biror serverga (VPS) joylashtirib, `systemd` yoki `pm2`/`screen`/`tmux` yordamida
doimiy ishlaydigan qilib qo'yish tavsiya etiladi. Bu kompyuterda vaqtincha ishga tushirilgan
bot faqat shu terminal ochiq turgandagina javob beradi.

## Katalogni to'ldirish / tuzatish

Barcha mahsulotlar `catalog.json` faylida saqlanadi:
```json
[
  {"name": "6205 ZZ SKF", "price": 6000},
  ...
]
```
- Narxni o'zgartirish uchun shu faylni tahrirlab, botni qayta ishga tushirsangiz bo'ldi.
- Yangi mahsulot qo'shish uchun shu formatda yangi qator qo'shing.

**Muhim eslatma:** Yuborgan rasmlaringizdagi jadvallardan **1160 dan ortiq** mahsulot
(nomi + narxi) `catalog.json` ga kiritildi. Lekin bitta bo'limda (UCFL/UCHA/UCPA/UCPH/UCT/YET
seriyali mahsulotlar, birinchi rasmning pastki chap ustunida) ekrandagi ochiq menyu narxlarning
bir qismini yopib qo'ygan edi — shu sabab o'sha bo'lim kiritilmadi. Agar xohlasangiz:
- O'sha jadvalning to'liq (yopilmagan) skrinshotini yuboring — men ularni ham qo'shib beraman, YOKI
- Agar bu narxlar Excel/Google Sheets faylida bo'lsa, to'g'ridan-to'g'ri o'sha faylni yuborsangiz,
  men butun katalogni undan **100% aniqlik bilan** avtomatik import qilib beraman (bu eng ishonchli yo'l,
  chunki rasmdan o'qishda kichik xatoliklar bo'lishi mumkin).

## Fayllar tuzilishi
- `bot.py` — asosiy bot kodi
- `catalog.py` — katalogda qidirish logikasi
- `catalog.json` — mahsulotlar (nomi, narxi)
- `database.py` — buyurtmalarni saqlash (SQLite, `bot.db` fayli avtomatik yaratiladi)
- `build_catalog.py` — rasmlardan yig'ilgan ma'lumotdan catalog.json yaratuvchi skript (kerak bo'lsa qayta ishga tushirish uchun)
- `.env.example` — sozlamalar namunasi
