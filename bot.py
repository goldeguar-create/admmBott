# -*- coding: utf-8 -*-
import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from dotenv import load_dotenv

import catalog
from database import create_order, init_db

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

logging.basicConfig(level=logging.INFO)

router = Router()


# ---------------------------------------------------------------------------
# FSM holatlari
# ---------------------------------------------------------------------------
class Order(StatesGroup):
    choosing_brand = State()
    typing_model = State()
    choosing_suggestion = State()
    typing_quantity = State()
    typing_phone = State()
    choosing_delivery = State()
    waiting_address = State()
    waiting_location = State()


# ---------------------------------------------------------------------------
# Klaviaturalar
# ---------------------------------------------------------------------------
def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🛒 Buyurtma berish", callback_data="order_start")]]
    )


def brands_kb() -> InlineKeyboardMarkup:
    rows = []
    row = []
    for b in catalog.BRANDS:
        row.append(InlineKeyboardButton(text=b, callback_data=f"brand:{b}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="📦 Barchasi (hammasi)", callback_data="brand:Barchasi")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def suggestions_kb(items) -> InlineKeyboardMarkup:
    rows = []
    for idx, item in enumerate(items):
        rows.append([InlineKeyboardButton(text=item["name"], callback_data=f"pick:{idx}")])
    rows.append([InlineKeyboardButton(text="🔁 Qaytadan yozish", callback_data="retype")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def after_found_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Shu mahsulotni buyurtma qilish", callback_data="confirm_product")],
            [InlineKeyboardButton(text="🔁 Boshqa model qidirish", callback_data="retype")],
        ]
    )


def delivery_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Joylashuvni yuborish", request_location=True)],
            [KeyboardButton(text="✍️ Manzilni yozib yuboraman")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def phone_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📞 Raqamimni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


# ---------------------------------------------------------------------------
# /start
# ---------------------------------------------------------------------------
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Assalomu alaykum, {message.from_user.full_name}! 👋\n\n"
        "🔩 <b>Toshkent Bearing</b> botiga xush kelibsiz!\n"
        "Bu yerda siz kerakli podshipnik (bearing) modelini topib, buyurtma bera olasiz.\n\n"
        "Boshlash uchun quyidagi tugmani bosing 👇",
        reply_markup=main_menu_kb(),
    )


# ---------------------------------------------------------------------------
# Buyurtma boshlanishi -> brend tanlash
# ---------------------------------------------------------------------------
@router.callback_query(F.data == "order_start")
async def order_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(Order.choosing_brand)
    await callback.message.edit_text(
        "Qaysi turdagi (brenddagi) bearing kerak? Tanlang 👇",
        reply_markup=brands_kb(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("brand:"))
async def brand_chosen(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    brand = callback.data.split(":", 1)[1]
    await state.update_data(brand=brand)
    await state.set_state(Order.typing_model)
    await callback.message.edit_text(
        f"Tanlandi: <b>{brand}</b>\n\n"
        "Endi kerakli podshipnik <b>model raqamini</b> yozib yuboring.\n"
        "Masalan: <code>6205</code> yoki <code>6205 2RS SKF</code>"
    )
    await callback.answer()


@router.callback_query(F.data == "retype")
async def retype(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(Order.typing_model)
    await callback.message.edit_text("Yangi model raqamini yozib yuboring:")
    await callback.answer()


# ---------------------------------------------------------------------------
# Model qidirish
# ---------------------------------------------------------------------------
@router.message(Order.typing_model)
async def model_search(message: Message, state: FSMContext):
    data = await state.get_data()
    brand = data.get("brand")
    query = message.text.strip()

    exact, suggestions = catalog.search(query, brand=brand)

    if exact:
        item = exact[0]
        await state.update_data(product=item)
        await message.answer(catalog.format_item(item), reply_markup=after_found_kb())
        return

    if suggestions:
        await state.update_data(suggestions=suggestions)
        await state.set_state(Order.choosing_suggestion)
        await message.answer(
            "Aniq mos model topilmadi 🔍\n"
            "Balki shulardan biri kerakdir? Tanlang, yoki qaytadan yozing:",
            reply_markup=suggestions_kb(suggestions),
        )
        return

    await message.answer(
        "Kechirasiz, bu model bo'yicha hech narsa topilmadi. 😔\n"
        "Boshqa model raqamini kiritib ko'ring, yoki operatorga to'g'ridan-to'g'ri yozing.",
    )


@router.callback_query(Order.choosing_suggestion, F.data.startswith("pick:"))
async def pick_suggestion(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    suggestions = data.get("suggestions", [])
    idx = int(callback.data.split(":", 1)[1])
    if idx >= len(suggestions):
        await callback.answer("Xatolik, qaytadan urinib ko'ring", show_alert=True)
        return
    item = suggestions[idx]
    await state.update_data(product=item)
    await callback.message.edit_text(catalog.format_item(item))
    await callback.message.answer("Buyurtma qilamizmi?", reply_markup=after_found_kb())
    await callback.answer()


# ---------------------------------------------------------------------------
# Mahsulotni tasdiqlash -> miqdor -> telefon -> yetkazib berish
# ---------------------------------------------------------------------------
@router.callback_query(F.data == "confirm_product")
async def confirm_product(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(Order.typing_quantity)
    await callback.message.edit_text("Nechta dona kerak? (miqdorini raqamda yozing, masalan: 2)")
    await callback.answer()


@router.message(Order.typing_quantity)
async def get_quantity(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit() or int(text) <= 0:
        await message.answer("Iltimos, miqdorni musbat raqamda yozing. Masalan: 1, 2, 5 ...")
        return
    await state.update_data(quantity=int(text))
    await state.set_state(Order.typing_phone)
    await message.answer(
        "Endi telefon raqamingizni yuboring 📞 (tugmani bosing yoki qo'lda yozing):",
        reply_markup=phone_kb(),
    )


@router.message(Order.typing_phone, F.contact)
async def get_phone_contact(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await ask_delivery(message, state)


@router.message(Order.typing_phone)
async def get_phone_text(message: Message, state: FSMContext):
    phone = message.text.strip()
    await state.update_data(phone=phone)
    await ask_delivery(message, state)


async def ask_delivery(message: Message, state: FSMContext):
    await state.set_state(Order.choosing_delivery)
    await message.answer(
        "📦 <b>Yetkazib berish</b>\n\n"
        "Manzilingizni bildiring: kartadan joylashuvingizni yuboring, "
        "yoki manzilni yozib yuboring 👇",
        reply_markup=delivery_kb(),
    )


@router.message(Order.choosing_delivery, F.location)
async def got_location(message: Message, state: FSMContext):
    loc = message.location
    await state.update_data(latitude=loc.latitude, longitude=loc.longitude, address=None)
    await finish_order(message, state)


@router.message(Order.choosing_delivery, F.text == "✍️ Manzilni yozib yuboraman")
async def ask_address_text(message: Message, state: FSMContext):
    await state.set_state(Order.waiting_address)
    await message.answer("Manzilingizni yozing (shahar, tuman, ko'cha va h.k.):", reply_markup=ReplyKeyboardRemove())


@router.message(Order.waiting_address)
async def got_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text.strip(), latitude=None, longitude=None)
    await finish_order(message, state)


@router.message(Order.choosing_delivery)
async def choosing_delivery_fallback(message: Message, state: FSMContext):
    await message.answer(
        "Iltimos, quyidagi tugmalardan birini tanlang 👇",
        reply_markup=delivery_kb(),
    )


# ---------------------------------------------------------------------------
# Buyurtmani yakunlash va adminga yuborish
# ---------------------------------------------------------------------------
async def finish_order(message: Message, state: FSMContext):
    data = await state.get_data()
    product = data.get("product", {})
    quantity = data.get("quantity", 1)
    phone = data.get("phone", "-")
    address = data.get("address")
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    user = message.from_user
    order_id = create_order(
        tg_id=user.id,
        username=user.username,
        full_name=user.full_name,
        model=product.get("name", "-"),
        price=product.get("price", 0),
        quantity=quantity,
        phone=phone,
        address=address,
        latitude=latitude,
        longitude=longitude,
    )

    await state.clear()
    await message.answer(
    "✅ Buyurtmangiz qabul qilindi!\n\n"
    "Tez orada operatorimiz siz bilan bog'lanadi. Rahmat! 🙏",
    reply_markup=ReplyKeyboardRemove(),
)
    await message.answer("Yana biror narsa buyurtma qilmoqchimisiz?", reply_markup=main_menu_kb())

    # --- Adminga xabar ---
    price = product.get("price", 0)
    total = price * quantity
    admin_text = (
        f"🆕 <b>Yangi buyurtma</b>\n"
        f"Buyurtma raqami: <b>#{order_id}</b>\n"
        f"TG ID: <code>{user.id}</code>\n"
        f"Foydalanuvchi: {user.full_name} (@{user.username or '-'})\n"
        f"Model: <b>{product.get('name', '-')}</b>\n"
        f"Narxi (1 dona): {price:,} so'm".replace(",", " ") + "\n"
        f"Miqdori: {quantity} dona\n"
        f"Jami: {total:,} so'm".replace(",", " ") + "\n"
        f"Telefon raqami: {phone}\n"
    )
    if address:
        admin_text += f"Manzil: {address}\n"
    admin_text += "\nJavob yozish uchun: <code>/reply " + str(user.id) + " matningiz</code>"

    bot: Bot = message.bot
    if ADMIN_ID:
        if latitude and longitude:
            await bot.send_location(ADMIN_ID, latitude=latitude, longitude=longitude)
        await bot.send_message(ADMIN_ID, admin_text)


# ---------------------------------------------------------------------------
# Admin uchun /reply komandasi
# ---------------------------------------------------------------------------
@router.message(Command("reply"))
async def admin_reply(message: Message):
    if message.from_user.id != ADMIN_ID:
        return  # faqat admin foydalana oladi

    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("Foydalanish: <code>/reply tg_id matn</code>\nMasalan: /reply 123456789 Salom, buyurtmangiz tayyor!")
        return

    _, tg_id_str, text = parts
    try:
        tg_id = int(tg_id_str)
    except ValueError:
        await message.answer("tg_id raqam bo'lishi kerak.")
        return

    try:
        await message.bot.send_message(tg_id, f"💬 <b>Admin javobi:</b>\n{text}")
        await message.answer("✅ Xabar yuborildi.")
    except Exception as e:
        await message.answer(f"❌ Xabar yuborilmadi: {e}")


# ---------------------------------------------------------------------------
# Boshqa istalgan matn (menyudan tashqari)
# ---------------------------------------------------------------------------
@router.message()
async def fallback(message: Message, state: FSMContext):
    await message.answer(
        "Buyurtma berish uchun quyidagi tugmani bosing 👇",
        reply_markup=main_menu_kb(),
    )


async def main():
    init_db()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN topilmadi! .env faylida BOT_TOKEN ni kiriting.")
    asyncio.run(main())
