
import os
import asyncio
import traceback
import logging

from aiohttp import web

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton
)

from supabase import create_client


# =====================================
# 1. SOZLAMALAR
# =====================================

TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("RENDER_EXTERNAL_URL")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

ADMIN_IDS = [5000535277]

CHANNEL_ID = -1002328943187

WEBHOOK_PATH = "/telegram-webhook"


# =====================================
# 2. LOGGING
# =====================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# =====================================
# 3. MUHIM SOZLAMALARNI TEKSHIRISH
# =====================================

required_vars = {
    "BOT_TOKEN": TOKEN,
    "RENDER_EXTERNAL_URL": BASE_URL,
    "WEBHOOK_SECRET": WEBHOOK_SECRET,
    "SUPABASE_URL": SUPABASE_URL,
    "SUPABASE_SECRET_KEY": SUPABASE_SECRET_KEY
}

for name, value in required_vars.items():
    if not value:
        raise ValueError(f"{name} Render Environment ichida topilmadi!")


# =====================================
# 4. BOT VA SUPABASE
# =====================================

bot = Bot(token=TOKEN)

dp = Dispatcher(storage=MemoryStorage())

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY
)


# =====================================
# 5. KATEGORIYALAR
# =====================================

categories = [
    "🏠 Uy",
    "🏢 Ofis",
    "🏭 Zavod",
    "🛋 Interyer dizayn",
    "🏫 Maktab va bog‘cha",
    "🛍 Savdo markazi",
    "🛣 Yo‘l va ko‘prik",
    "🏗 Boshqa binolar"
]


# =====================================
# 6. KLAVIATURALAR
# =====================================

def category_keyboard():

    buttons = [
        [
            KeyboardButton(text=cat)
            for cat in categories[i:i + 2]
        ]
        for i in range(0, len(categories), 2)
    ]

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )


def admin_keyboard():

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Loyiha qo‘shish")],
            [KeyboardButton(text="📁 Loyihalar")],
            [KeyboardButton(text="🔙 Bosh menyu")]
        ],
        resize_keyboard=True
    )


def skip_keyboard():

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⏭ O‘tkazish")],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )


# =====================================
# 7. ADMIN HOLATLARI
# =====================================

class AddProject(StatesGroup):

    waiting_title = State()

    waiting_category = State()

    waiting_description = State()

    waiting_file = State()


# =====================================
# 8. START
# =====================================

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):

    await state.clear()

    if message.from_user.id in ADMIN_IDS:

        await message.answer(
            "👋 Assalomu alaykum, admin!\n\n"
            "🏗 AutoCAD Projects Bot\n"
            "Boshqaruv paneliga xush kelibsiz!",
            reply_markup=admin_keyboard()
        )

    else:

        await message.answer(
            "👋 Assalomu alaykum!\n\n"
            "🏗 AutoCAD Projects Botga xush kelibsiz!\n\n"
            "📂 Kerakli kategoriyani tanlang:",
            reply_markup=category_keyboard()
        )


# =====================================
# 9. BOSH MENYU
# =====================================

@dp.message(F.text == "🔙 Bosh menyu")
async def back_to_main(message: Message, state: FSMContext):

    await state.clear()

    if message.from_user.id in ADMIN_IDS:

        await message.answer(
            "⚙️ Admin boshqaruv paneli:",
            reply_markup=admin_keyboard()
        )

    else:

        await message.answer(
            "📂 Kategoriyani tanlang:",
            reply_markup=category_keyboard()
        )


# =====================================
# 10. ADMIN LOYIHALAR RO‘YXATI
# =====================================

@dp.message(F.text == "📁 Loyihalar")
async def admin_projects(message: Message):

    if message.from_user.id not in ADMIN_IDS:
        return

    try:

        result = await asyncio.to_thread(
            lambda: supabase.table("projects")
            .select("id,title,category")
            .order("id", desc=True)
            .limit(30)
            .execute()
        )

        projects = result.data or []

        if not projects:

            await message.answer(
                "📂 Hozircha loyihalar mavjud emas."
            )

            return

        text = "📁 OXIRGI LOYIHALAR:\n\n"

        for project in projects:

            text += (
                f"🆔 ID: {project['id']}\n"
                f"📌 Nomi: {project['title']}\n"
                f"📂 Kategoriya: {project['category']}\n"
                "━━━━━━━━━━━━━━\n"
            )

        await message.answer(text[:4000])

    except Exception:

        logger.exception("Admin loyihalar ro'yxatida xato")

        await message.answer(
            "❌ Loyihalarni olishda xatolik yuz berdi."
        )


# =====================================
# 11. LOYIHA QO‘SHISHNI BOSHLASH
# =====================================

@dp.message(F.text == "➕ Loyiha qo‘shish")
async def add_project(message: Message, state: FSMContext):

    if message.from_user.id not in ADMIN_IDS:
        return

    await state.clear()

    await state.set_state(AddProject.waiting_title)

    await message.answer(
        "📝 Yangi loyiha nomini kiriting:\n\n"
        "Masalan: Zamonaviy ikki qavatli uy"
    )


# =====================================
# 12. LOYIHA NOMI
# =====================================

@dp.message(AddProject.waiting_title)
async def get_title(message: Message, state: FSMContext):

    if not message.text:

        await message.answer(
            "❗ Loyiha nomini matn ko‘rinishida yuboring."
        )

        return

    title = message.text.strip()

    if len(title) > 200:

        await message.answer(
            "❗ Loyiha nomi 200 ta belgidan oshmasin."
        )

        return

    await state.update_data(title=title)

    await state.set_state(AddProject.waiting_category)

    await message.answer(
        "📂 Loyiha kategoriyasini tanlang:",
        reply_markup=category_keyboard()
    )


# =====================================
# 13. LOYIHA KATEGORIYASI
# =====================================

@dp.message(AddProject.waiting_category)
async def get_category(message: Message, state: FSMContext):

    if message.text not in categories:

        await message.answer(
            "❗ Iltimos, ro‘yxatdan kategoriya tanlang.",
            reply_markup=category_keyboard()
        )

        return

    await state.update_data(category=message.text)

    await state.set_state(AddProject.waiting_description)

    await message.answer(
        "📄 Loyiha haqida qisqacha ma'lumot yozing.\n\n"
        "Yoki o'tkazib yuborish tugmasini bosing:",
        reply_markup=skip_keyboard()
    )


# =====================================
# 14. TAVSIFNI O‘TKAZIB YUBORISH
# =====================================

@dp.message(
    AddProject.waiting_description,
    F.text == "⏭ O‘tkazish"
)
async def skip_description(message: Message, state: FSMContext):

    await state.update_data(description="")

    await state.set_state(AddProject.waiting_file)

    await message.answer(
        "📎 Endi loyiha faylini yuboring.\n\n"
        "DWG, PDF, ZIP va boshqa hujjatlar qabul qilinadi.",
        reply_markup=admin_keyboard()
    )


# =====================================
# 15. TAVSIFNI QABUL QILISH
# =====================================

@dp.message(AddProject.waiting_description)
async def get_description(message: Message, state: FSMContext):

    if not message.text:

        await message.answer(
            "❗ Tavsifni matn ko‘rinishida yuboring."
        )

        return

    description = message.text.strip()

    if len(description) > 3000:

        await message.answer(
            "❗ Tavsif juda uzun. 3000 ta belgidan kam yuboring."
        )

        return

    await state.update_data(description=description)

    await state.set_state(AddProject.waiting_file)

    await message.answer(
        "📎 Endi AutoCAD loyiha faylini yuboring:\n\n"
        "Masalan: DWG, PDF yoki ZIP",
        reply_markup=admin_keyboard()
    )


# =====================================
# 16. LOYIHANI KANAL VA SUPABASEGA SAQLASH
# =====================================

@dp.message(AddProject.waiting_file, F.document)
async def save_project(message: Message, state: FSMContext):

    if message.from_user.id not in ADMIN_IDS:
        return

    data = await state.get_data()

    title = data.get("title")
    category = data.get("category")
    description = data.get("description", "")

    if not title or not category:

        await message.answer(
            "❌ Loyiha ma'lumotlari topilmadi. "
            "Qaytadan boshlang: /start"
        )

        await state.clear()

        return

    try:

        # 1-QADAM: Faylni yopiq kanalga yuborish

        logger.info("1-QADAM: Telegram kanalga yuborish boshlandi")

        channel_message = await bot.send_document(
            chat_id=CHANNEL_ID,
            document=message.document.file_id,
            caption=(
                f"📁 {title}\n"
                f"📂 {category}\n\n"
                f"{description}"
            )[:1024]
        )

        logger.info("2-QADAM: Fayl kanalga yuborildi")

        # 2-QADAM: Kanal fayl ID sini olish

        channel_file_id = channel_message.document.file_id

        # 3-QADAM: Supabase ma'lumotlarini tayyorlash

        project_data = {
            "title": title,
            "category": category,
            "description": description,
            "telegram_file_id": channel_file_id
        }

        logger.info("3-QADAM: Supabase saqlash boshlandi")

        # 4-QADAM: Supabase bazasiga yozish

        await asyncio.to_thread(
            lambda: supabase.table("projects")
            .insert(project_data)
            .execute()
        )

        logger.info("4-QADAM: Supabase saqlash muvaffaqiyatli")

        # 5-QADAM: Adminga javob

        await message.answer(
            "✅ LOYIHA MUVAFFAQIYATLI SAQLANDI!\n\n"
            f"📁 Nomi: {title}\n"
            f"📂 Kategoriya: {category}\n\n"
            "☑ Fayl Telegram kanalga joylandi.\n"
            "☑ Ma'lumot Supabase bazasiga saqlandi.",
            reply_markup=admin_keyboard()
        )

        await state.clear()

    except Exception as e:

        logger.error(
            "LOYIHA SAQLASHDA XATO: %r",
            e
        )

        traceback.print_exc()

        await message.answer(
            "❌ Loyihani saqlashda xatolik yuz berdi.\n\n"
            "Render Logs orqali xatoni aniqlaymiz."
        )


# =====================================
# 17. NOTO‘G‘RI FAYL
# =====================================

@dp.message(AddProject.waiting_file)
async def invalid_file(message: Message):

    await message.answer(
        "❗ Iltimos, faylni hujjat (Document) sifatida yuboring.\n\n"
        "DWG, PDF yoki ZIP fayl yuborishingiz mumkin."
    )


# =====================================
# 18. FOYDALANUVCHI LOYIHALARI
# =====================================

@dp.message(F.text.in_(categories))
async def category_handler(message: Message):

    category = message.text

    try:

        await message.answer(
            "🔎 Loyihalar qidirilmoqda..."
        )

        result = await asyncio.to_thread(
            lambda: supabase.table("projects")
            .select("*")
            .eq("category", category)
            .order("id", desc=True)
            .limit(20)
            .execute()
        )

        projects = result.data or []

        if not projects:

            await message.answer(
                f"📂 {category}\n\n"
                "Hozircha bu kategoriyada loyihalar yo‘q."
            )

            return

        await message.answer(
            f"📂 {category}\n\n"
            f"✅ Topilgan loyihalar: {len(projects)} ta"
        )

        for project in projects:

            caption = (
                f"📁 {project['title']}\n"
                f"📂 {project['category']}\n\n"
                f"{project.get('description') or ''}"
            )

            await bot.send_document(
                chat_id=message.chat.id,
                document=project["telegram_file_id"],
                caption=caption[:1024]
            )

    except Exception:

        logger.exception("Foydalanuvchi loyihalarini yuklashda xato")

        await message.answer(
            "❌ Loyihalarni yuklashda xatolik yuz berdi."
        )


# =====================================
# 19. BEKOR QILISH
# =====================================

@dp.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):

    await state.clear()

    if message.from_user.id in ADMIN_IDS:

        keyboard = admin_keyboard()

    else:

        keyboard = category_keyboard()

    await message.answer(
        "❌ Amal bekor qilindi.",
        reply_markup=keyboard
    )


@dp.message(F.text == "❌ Bekor qilish")
async def cancel_button(message: Message, state: FSMContext):

    await state.clear()

    await message.answer(
        "❌ Amal bekor qilindi.",
        reply_markup=admin_keyboard()
    )


# =====================================
# 20. WEBHOOK
# =====================================

async def handle_webhook(request):

    secret = request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token"
    )

    if secret != WEBHOOK_SECRET:

        raise web.HTTPForbidden()

    try:

        data = await request.json()

        update = Update.model_validate(
            data,
            context={"bot": bot}
        )

        await dp.feed_update(bot, update)

        return web.Response(text="OK")

    except Exception:

        logger.exception("Webhook ishlashida xatolik")

        raise


# =====================================
# 21. BOTNI ISHGA TUSHIRISH
# =====================================

async def on_startup(app):

    await bot.set_webhook(
        url=f"{BASE_URL}{WEBHOOK_PATH}",
        secret_token=WEBHOOK_SECRET
    )

    logger.info("Webhook muvaffaqiyatli o'rnatildi!")

    logger.info("Telegram bot ishga tushdi!")


# =====================================
# 22. BOTNI TO‘XTATISH
# =====================================

async def on_shutdown(app):

    await bot.session.close()

    logger.info("Bot to'xtatildi")


# =====================================
# 23. SERVER
# =====================================

app = web.Application()

app.router.add_get(
    "/",
    lambda request: web.Response(
        text="AutoCAD Projects Bot ishlayapti!"
    )
)

app.router.add_post(
    WEBHOOK_PATH,
    handle_webhook
)

app.on_startup.append(on_startup)

app.on_cleanup.append(on_shutdown)


# =====================================
# 24. SERVERNI ISHGA TUSHIRISH
# =====================================

if __name__ == "__main__":

    port = int(os.getenv("PORT", 10000))

    web.run_app(
        app,
        host="0.0.0.0",
        port=port
    )
