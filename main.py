
import os
import asyncio

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


# =========================
# SOZLAMALAR
# =========================

TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("RENDER_EXTERNAL_URL")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

ADMIN_IDS = [5000535277]
CHANNEL_ID = -1002328943187

WEBHOOK_PATH = "/telegram-webhook"


# =========================
# TEKSHIRISH
# =========================

required_vars = {
    "BOT_TOKEN": TOKEN,
    "RENDER_EXTERNAL_URL": BASE_URL,
    "WEBHOOK_SECRET": WEBHOOK_SECRET,
    "SUPABASE_URL": SUPABASE_URL,
    "SUPABASE_SECRET_KEY": SUPABASE_SECRET_KEY,
}

for name, value in required_vars.items():
    if not value:
        raise ValueError(f"{name} topilmadi!")


# =========================
# BOT VA SUPABASE
# =========================

bot = Bot(token=TOKEN)

dp = Dispatcher(storage=MemoryStorage())

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY
)


# =========================
# KATEGORIYALAR
# =========================

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


def category_keyboard():
    buttons = [
        [KeyboardButton(text=cat) for cat in categories[i:i+2]]
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


# =========================
# ADMIN HOLATLARI
# =========================

class AddProject(StatesGroup):
    waiting_title = State()
    waiting_category = State()
    waiting_description = State()
    waiting_file = State()


# =========================
# START
# =========================

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()

    if message.from_user.id in ADMIN_IDS:
        await message.answer(
            "👋 Assalomu alaykum, admin!\n\n"
            "AutoCAD Projects Bot boshqaruv paneli.",
            reply_markup=admin_keyboard()
        )
    else:
        await message.answer(
            "Assalomu alaykum!\n"
            "AutoCAD Projects Botga xush kelibsiz!\n\n"
            "Kategoriyani tanlang:",
            reply_markup=category_keyboard()
        )


# =========================
# ADMIN PANEL
# =========================

@dp.message(F.text == "🔙 Bosh menyu")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "Kategoriyani tanlang:",
        reply_markup=category_keyboard()
    )


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
            await message.answer("Hozircha loyihalar mavjud emas.")
            return

        text = "📁 Oxirgi loyihalar:\n\n"

        for project in projects:
            text += (
                f"🆔 {project['id']}\n"
                f"📌 {project['title']}\n"
                f"📂 {project['category']}\n\n"
            )

        await message.answer(text)

    except Exception as e:
        print("Supabase xatosi:", e)
        await message.answer("Ma'lumotlarni olishda xatolik!")


# =========================
# LOYIHA QO'SHISH
# =========================

@dp.message(F.text == "➕ Loyiha qo‘shish")
async def add_project(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    await state.clear()
    await state.set_state(AddProject.waiting_title)

    await message.answer("📝 Loyiha nomini kiriting:")


@dp.message(AddProject.waiting_title)
async def get_title(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Iltimos, loyiha nomini matn ko‘rinishida yuboring.")
        return

    await state.update_data(title=message.text.strip())
    await state.set_state(AddProject.waiting_category)

    await message.answer(
        "📂 Loyiha kategoriyasini tanlang:",
        reply_markup=category_keyboard()
    )


@dp.message(AddProject.waiting_category)
async def get_category(message: Message, state: FSMContext):
    if message.text not in categories:
        await message.answer("Iltimos, ro‘yxatdan kategoriya tanlang.")
        return

    await state.update_data(category=message.text)
    await state.set_state(AddProject.waiting_description)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⏭ O‘tkazish")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "📄 Loyiha haqida qisqacha ma'lumot yozing.\n"
        "Yoki o'tkazib yuboring:",
        reply_markup=keyboard
    )


@dp.message(
    AddProject.waiting_description,
    F.text == "⏭ O‘tkazish"
)
async def skip_description(message: Message, state: FSMContext):
    await state.update_data(description="")
    await state.set_state(AddProject.waiting_file)

    await message.answer(
        "📎 Endi loyiha faylini yuboring.\n"
        "DWG, PDF, ZIP va boshqa hujjatlar qabul qilinadi.",
        reply_markup=admin_keyboard()
    )


@dp.message(AddProject.waiting_description)
async def get_description(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Tavsifni matn ko‘rinishida yuboring.")
        return

    await state.update_data(description=message.text.strip())
    await state.set_state(AddProject.waiting_file)

    await message.answer(
        "📎 Endi AutoCAD loyiha faylini yuboring:",
        reply_markup=admin_keyboard()
    )


# =========================
# FAYLNI KANALGA VA SUPABASEGA SAQLASH
# =========================

@dp.message(AddProject.waiting_file, F.document)
async def save_project(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    data = await state.get_data()

    title = data["title"]
    category = data["category"]
    description = data.get("description", "")

    try:
        # Faylni yopiq kanalga joylash
        channel_message = await bot.send_document(
            chat_id=CHANNEL_ID,
            document=message.document.file_id,
            caption=(
                f"📁 {title}\n"
                f"📂 {category}\n\n"
                f"{description}"
            )
        )

        # Kanaldagi fayl ID sini olish
        channel_file_id = channel_message.document.file_id

        # Supabase bazasiga yozish
        project_data = {
            "title": title,
            "category": category,
            "description": description,
            "telegram_file_id": channel_file_id
        }

        await asyncio.to_thread(
            lambda: supabase.table("projects")
            .insert(project_data)
            .execute()
        )

        await message.answer(
            "✅ LOYIHA MUVAFFAQIYATLI SAQLANDI!\n\n"
            f"📁 Nomi: {title}\n"
            f"📂 Kategoriya: {category}\n\n"
            "Fayl kanalga va Supabase bazasiga joylandi.",
            reply_markup=admin_keyboard()
        )

        await state.clear()

    except Exception as e:
        print("Loyiha saqlash xatosi:", repr(e))

        await message.answer(
            "❌ Loyihani saqlashda xatolik yuz berdi.\n"
            "Render Logs bo‘limini tekshiring."
        )


@dp.message(AddProject.waiting_file)
async def invalid_file(message: Message):
    await message.answer(
        "Iltimos, loyiha faylini hujjat (Document) sifatida yuboring."
    )


# =========================
# FOYDALANUVCHI LOYIHALARI
# =========================

@dp.message(F.text.in_(categories))
async def category_handler(message: Message):
    category = message.text

    try:
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
            f"Topilgan loyihalar: {len(projects)}"
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

    except Exception as e:
        print("Loyihalarni olish xatosi:", repr(e))
        await message.answer("❌ Loyihalarni yuklashda xatolik!")


# =========================
# BEKOR QILISH
# =========================

@dp.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "❌ Amal bekor qilindi.",
        reply_markup=(
            admin_keyboard()
            if message.from_user.id in ADMIN_IDS
            else category_keyboard()
        )
    )


# =========================
# WEBHOOK
# =========================

async def handle_webhook(request):
    secret = request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token"
    )

    if secret != WEBHOOK_SECRET:
        raise web.HTTPForbidden()

    data = await request.json()

    update = Update.model_validate(
        data,
        context={"bot": bot}
    )

    await dp.feed_update(bot, update)

    return web.Response(text="OK")


async def on_startup(app):
    await bot.set_webhook(
        url=f"{BASE_URL}{WEBHOOK_PATH}",
        secret_token=WEBHOOK_SECRET
    )

    print("Webhook muvaffaqiyatli o'rnatildi!")


async def on_shutdown(app):
    await bot.session.close()


# =========================
# SERVER
# =========================

app = web.Application()

app.router.add_get(
    "/",
    lambda request: web.Response(text="Bot ishlayapti!")
)

app.router.add_post(
    WEBHOOK_PATH,
    handle_webhook
)

app.on_startup.append(on_startup)
app.on_cleanup.append(on_shutdown)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)
