
import asyncio
from aiogram import Bot, Router, Dispatcher, F
from aiogram.types import (Message, CallbackQuery,ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import asyncpg

TOKEN = "8329870331:AAFqRwBwrk05Z52s_wr7PGUDamKWQknqs40"
bot = Bot(token=TOKEN)
dp = Dispatcher()

DB_USER = "postgres"
DB_PASSWORD = "1234"
DB_NAME = "taxi"
DB_HOST = "localhost"
DB_PORT = 5432

db = None


# ================= FSM =================
class TaxiOrderState(StatesGroup):
    taxi_turi = State()
    qayerdan = State()
    qayerga = State()
    kilometr = State()   
    telefon = State()
    tasdiqlash = State()



# ================= MENYU =================
def user_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚕 Taksi buyurtma qilish")],
            [KeyboardButton(text="📋 Mening buyurtmalarim")],
            [KeyboardButton(text="📞 Aloqa")]
        ],
        resize_keyboard=True
    )


def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚕 Taksi buyurtma qilish")],
            [KeyboardButton(text="📋 Mening buyurtmalarim")],
            [KeyboardButton(text="📞 Aloqa")],
            [KeyboardButton(text="😎Admin panel")]
        ],
        resize_keyboard=True
    )

def main_menu_keyboard(user_id: int | None = None):
    # return admin menu when the caller provides the owner admin id, otherwise user menu
    if user_id is not None and user_id == owner_admin:
        return admin_menu()
    return user_menu()


# ====== ADMIN CONFIGURATION ======
owner_admin =  8273266193  # o'zingizning Telegram user ID'ingizni kiriting
ADMIN_PASSWORD = "2205"  # admin parol

class AdminStates(StatesGroup):
    password = State()
# ======Admin panel ========
@dp.message(F.text == "😎Admin panel")
async def admin_panel(msg: Message):
    if msg.from_user.id != owner_admin:
        await msg.answer("❌ Siz admin emassiz!")
        return

    await msg.answer(
        "🔧 Admin panelga xush kelibsiz\nQuyidagilardan birini tanlang:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🚕 Admin panelidan taxi buyurtma qilish")],
                [KeyboardButton(text="Operator paneli 🧑‍💻")],
                [KeyboardButton(text="Haydovchi paneli 👨‍💼")],
                [KeyboardButton(text="Foydalanuvchi paneli 👥")]
            ],
            resize_keyboard=True
        )
    )

#===== user handler ========
@dp.message(F.text == "🚕 Taksi buyurtma qilish")
async def taxi_start(msg: Message, state: FSMContext):
    await state.update_data(role="user")

    await msg.answer(
        "🚖 Taksi turini tanlang:",
        reply_markup=taxi_type_keyboard()
    )

    await state.set_state(TaxiOrderState.taxi_turi)

#===== admion hendler =======
@dp.message(F.text == "🚕 Admin panelidan taxi buyurtma qilish")
async def admin_taxi_start(msg: Message, state: FSMContext):
    if msg.from_user.id != owner_admin:
        return

    await state.update_data(role="admin")  # 🔥 MUHIM
    await msg.answer(
        "🚖 Hurmatli admin taksi turini tanlang:",
        reply_markup=taxi_type_keyboard()
    )
    await state.set_state(TaxiOrderState.taxi_turi)


#===== Operator paneli========

@dp.message(F.text == "Operator paneli 🧑‍💻")
async def operator_panel(msg: Message):
    if msg.from_user.id != owner_admin:
        return

    rows = await db.fetch("""
        SELECT id, taxi_turi, qayerdan, qayerga, telefon, holat
        FROM orders
        ORDER BY created_at DESC
        LIMIT 10
    """)

    if not rows:
        await msg.answer("📭 Hozircha buyurtmalar yo'q")
        return

    text = "🧑‍💻 *Yangi buyurtmalar:*\n\n"
    for r in rows:
        text += (
            f"🆔 #{r['id']}\n"
            f"🚖 {r['taxi_turi']}\n"
            f"📍 {r['qayerdan']} ➡ {r['qayerga']}\n"
            f"📞 {r['telefon']}\n"
            f"📌 {r['holat']}\n\n"
        )

    await msg.answer(text, parse_mode="Markdown")


@dp.message(F.text == "Ortga qaytish 🔙")
async def back_to_main_menu(msg: Message):
    # Admin bo'lsa admin menyu, bo'lmasa user menyu chiqaradi
    await msg.answer(
        "Asosiy menyuga qaytdingiz.",
        reply_markup=main_menu_keyboard(msg.from_user.id)
    )
#====== Haydovchi paneli======

@dp.message(F.text == "Haydovchi paneli 👨‍💼")
async def driver_panel(msg: Message):
    if msg.from_user.id != owner_admin:
        return

    await msg.answer(
        "👨‍💼 Haydovchi paneliga xush kelibsiz\nSiz buyurtmalarni kuzatishingiz mumkin.\nHozir sizning holatingiz: Bo'shman\nHozir sizning holatingiz: Bandman.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✅ Bo'shman")],
                [KeyboardButton(text="🚕 Bandman")],
                [KeyboardButton(text="⬅ Orqaga")]
            ],
            resize_keyboard=True
        )
    )


@dp.message(F.text == "✅ Bo'shman")
async def set_free(msg: Message):
    await msg.answer("Siz hozir bo'shsiz. Yangi buyurtmalarningizni kuting.\nOperatorlarimiz siz bilan bog'lanishadi.", reply_markup=main_menu_keyboard())

@dp.message(F.text == "🚕 Bandman")
async def set_busy(msg: Message):
    await msg.answer("Siz hozir bandsiz. Hozirgi buyurtmalaringizni\n amalga oshirganingizdan so'ng.Operatorlarimiz siz bilan bog'lanishadi.", reply_markup=main_menu_keyboard())

@dp.message(F.text == "⬅ Orqaga")
async def back_to_admin(msg: Message):
    await msg.answer(
        "🔧 Admin panelga qaytildi\nQuyidagilardan birini tanlang:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Operator paneli 🧑‍💻")],
                [KeyboardButton(text="Haydovchi paneli 👨‍💼")],
                [KeyboardButton(text="Ortga qaytish 🔙")]
            ],
            resize_keyboard=True
        )
    )

#====== ortga qaytish=======
@dp.message(F.text == "Foydalanuvchi paneli 👥")
async def back_to_main(msg: Message):
    await msg.answer(
        "Foydalanuvchi paneliga qaytildi.",
        reply_markup=main_menu_keyboard()
    )


@dp.message(F.text == "📞 Aloqa")
async def al_oqa(msg: Message):
    await msg.answer("😊 Adminimiz tez orada siz bilan bog'lanadi.\n Kamchiliklar uchun oldindan uzur. 🙌")

@dp.message(F.text == "📋 Mening buyurtmalarim")
async def mening_buyurtmalarim(msg: Message):
    rows = await db.fetch(
        """
        SELECT id, qayerdan, qayerga, telefon, holat
        FROM orders
        WHERE telegram_id = $1
        ORDER BY id DESC
        LIMIT 5
        """,
        msg.from_user.id
    )

    if not rows:
        await msg.answer("📭 Sizda hali buyurtmalar yo'q.")
        return

    text = "📋 *Sizning so'ngi buyurtmalaringiz:*\n\n"

    for r in rows:
        text += (
            f"🆔 Buyurtma #{r['id']}\n"
            f"📍 Qayerdan: {r['qayerdan']}\n"
            f"📍 Qayerga: {r['qayerga']}\n"
            f"📞 Telefon: {r['telefon']}\n"
            f"📌 Holat: {r['holat']}\n\n"
        )

    await msg.answer(text, parse_mode="Markdown")


# ================= LOCATION =================
location_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📍 Joylashuvni yuborish", request_location=True),

        ]
    ],
    resize_keyboard=True
)


# ================= PHONE =================
def phone_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)],
        ],
        resize_keyboard=True
    )


# ================= TASDIQLASH =================
def tasdiqlash_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="tasdiqlash"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="bekor")
            ]
        ]
    )


# ================= TAXI TURLARI =================
TAXI_TYPES = {
    "standart": {
        "name": "🚗 Standart",
        "cars": "Lacetti",
        "price": "Narxi jami: 50 000 so'm",
        "photo": "https://www.ixbt.com/img/n1/news/2024/4/6/4a4a27f468ef5856e02e30a3f4e123b6e7d620a3%20(1)%20copy_large.jpg"
    },
    "biznes": {
        "name": "🚘 Biznes",
        "cars": "Malibu 2",
        "price": "Narxi jami: 100 000 so'm",
        "photo": "https://uzautomotors.com/images/uploads/a35dd4bc6d3786affb92a6a5b7e8f79a.jpg"
    },
    "lux": {
        "name": "👑 Lux",
        "cars": "BMW M5",
        "price": "Narxi jami: 250 000+ so'm",
        "photo": "https://ddztmb1ahc6o7.cloudfront.net/policarobmw/wp-content/uploads/2021/02/05112228/2022-BMW-M5-CS-Driving1-1.jpg"
    }
}


def taxi_type_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚗 Standart", callback_data="taxi_standart")],
            [InlineKeyboardButton(text="🚘 Biznes", callback_data="taxi_biznes")],
            [InlineKeyboardButton(text="👑 Lux", callback_data="taxi_lux")]
        ]
    )


# ================= DATABASE =================
async def connect_db():
    global db
    db = await asyncpg.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        host=DB_HOST,
        port=DB_PORT
    )

    # Users jadvali (Yuborganingizdek)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id BIGINT PRIMARY KEY,
            full_name TEXT,
            username TEXT,
            phone TEXT,
            role TEXT DEFAULT 'user',
            qayerdan TEXT,
            qayerga TEXT
        )
    """)
    
   
    await db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
            taxi_turi TEXT NOT NULL,
            qayerdan TEXT NOT NULL,
            qayerga TEXT NOT NULL,
            telefon TEXT NOT NULL,
            holat TEXT DEFAULT 'Kutilmoqda',
            role VARCHAR(50) DEFAULT 'user'
        )
    """)
@dp.message(CommandStart())
async def start_handler(msg: Message):
    # Foydalanuvchini bazaga qo'shish yoki bor bo'lsa yangilamaslik
    await db.execute(
        """
        INSERT INTO users (telegram_id, full_name, username)
        VALUES ($1, $2, $3)
        ON CONFLICT (telegram_id) DO NOTHING
        """,
        msg.from_user.id,
        msg.from_user.full_name,
        msg.from_user.username
    )

    if msg.from_user.id == owner_admin:
        menu = admin_menu()
    else:
        menu = user_menu()

    await msg.answer(
        "🚕 Taksi buyurtma botiga xush kelibsiz!",
        reply_markup=menu
    )



# ================= TAXI TANLASH =================
@dp.callback_query(TaxiOrderState.taxi_turi, F.data.startswith("taxi_"))
async def taxi_selected(call: CallbackQuery, state: FSMContext):
    key = call.data.replace("taxi_", "")
    taxi = TAXI_TYPES[key]

    await state.update_data(taxi_turi=taxi["name"])

    await call.message.answer_photo(
        photo=taxi["photo"],
        caption=(
            f"{taxi['name']}\n\n"
            f"🚘 Mashinalar: {taxi['cars']}\n"
            f"💰 {taxi['price']}\n\n"
            f"📍 Iltimos, joylashuvingizni yuboring"
        ),
        reply_markup=location_keyboard
    )

    await state.set_state(TaxiOrderState.qayerdan)
    await call.answer()



# ================= QAYERDAN =================
@dp.message(TaxiOrderState.qayerdan, F.location)
async def get_qayerdan(msg: Message, state: FSMContext):
    manzil = f"{msg.location.latitude}, {msg.location.longitude}"
    await state.update_data(qayerdan=manzil)

    await msg.answer("📍 Qayerga borasiz? (manzilni yozing)")
    await state.set_state(TaxiOrderState.qayerga)

@dp.message(TaxiOrderState.qayerga)
async def get_qayerga(msg: Message, state: FSMContext):
    await state.update_data(qayerga=msg.text)





# ================= QAYERGA =================
    await msg.answer(
        "📞 Telefon raqamingizni yuboring:",
        reply_markup=phone_keyboard()
    )
    await state.set_state(TaxiOrderState.telefon)



# ================= TELEFON =================
@dp.message(TaxiOrderState.telefon, F.contact | F.text)
async def get_phone(msg: Message, state: FSMContext):
    telefon = msg.contact.phone_number if msg.contact else msg.text
    await state.update_data(telefon=telefon)

    data = await state.get_data()

    await msg.answer(
        f"📋 Buyurtma ma'lumotlari:\n\n"
        f"🚖 Taksi turi: {data['taxi_turi']}\n"
        f"📍 Qayerdan: {data['qayerdan']}\n"
        f"📍 Qayerga: {data['qayerga']}\n"
        f"📞 Telefon: {data['telefon']}\n\n"
        f"Tasdiqlaysizmi?",
        reply_markup=tasdiqlash_keyboard()
    )

    await state.set_state(TaxiOrderState.tasdiqlash)


# ================= TASDIQLASH =================
# ================= TASDIQLASH HANDLERI =================
@dp.callback_query(TaxiOrderState.tasdiqlash, F.data == "tasdiqlash")
async def tasdiqlash(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = call.from_user.id
    
    # Ma'lumotlarni bazaga yozish
    try:
        await db.execute(
            """
            INSERT INTO orders (telegram_id, taxi_turi, qayerdan, qayerga, telefon, role)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            user_id,
            data.get("taxi_turi"),
            data.get("qayerdan"),
            data.get("qayerga"),
            data.get("telefon"),
            data.get("role", "user")
        )
        
        await call.message.edit_text("✅ Buyurtma muvaffaqiyatli qabul qilindi!")
        
        # Admin yoki User menyusini aniqlash
        menu = main_menu_keyboard(user_id) 
        await call.message.answer("Asosiy menyu:", reply_markup=menu)
        
    except Exception as e:
        await call.message.answer(f"Xatolik yuz berdi: {e}")
    
    await state.clear()
    await call.answer()

# ================= ASOSIY FUNKSIYALARNI TO'G'RILASH =================

def main_menu_keyboard(user_id: int):
    # Bu yerda user_id orqali adminligini tekshiramiz
    if user_id == owner_admin:
        return admin_menu()
    return user_menu()

# Callback handlerlarda state-ni tekshirishni unutmang (masalan, TaxiOrderState.tasdiqlash)



# ================= BEKOR =================
@dp.callback_query(F.data == "bekor")
async def bekor(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("❌ Buyurtma bekor qilindi")
    await call.message.answer(
        "Agar yana taxi buyurtma qilmoqchi bo'lsangiz.\n Asosiy menyudan foydalaning",
        reply_markup=main_menu_keyboard()
    )
    await state.clear()
    await call.answer()


# ================= MAIN =================
async def main():
    await connect_db()
    print("🚕 Bot ishga tushdi")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
