import os
import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, Update, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from supabase import create_client


# =====================================================
# SOZLAMALAR
# =====================================================

TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = (os.getenv("RENDER_EXTERNAL_URL") or "").rstrip("/")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").rstrip("/")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

SUPER_ADMIN_ID = 5000535277
CHANNEL_ID = -1002328943187
WEBHOOK_PATH = "/telegram-webhook"

for key, value in {
    "BOT_TOKEN": TOKEN,
    "RENDER_EXTERNAL_URL": BASE_URL,
    "WEBHOOK_SECRET": WEBHOOK_SECRET,
    "SUPABASE_URL": SUPABASE_URL,
    "SUPABASE_SECRET_KEY": SUPABASE_SECRET_KEY,
}.items():
    if not value:
        raise ValueError(f"{key} Render Environment ichida yo‘q!")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("autocad-bot")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)


# =====================================================
# KATEGORIYALAR
# =====================================================

CATEGORIES = [
    "🏠 Uy",
    "🏢 Ofis",
    "🛋 Interyer dizayn",
    "🏫 Maktab va bog‘cha",
    "🛍 Savdo markazi",
    "🛣 Yo‘l va ko‘prik",
    "🏗 Boshqa binolar",
    "☕ Kichik kafelar",
    "🚏 Aqlli bekatlar",
    "🚗 Avtomobillar",
    "⚡ Elektr chizmalari",
    "🧱 Konstruksiya va fundament",
    "🪑 Mebel chizmalari",
    "🌳 Landshaft dizayn",
    "📐 Tayyor shablonlar",
    "🎨 Hatch va teksturalar",
    "🚜 Ferma va chorvachilik loyihalari",
]


# =====================================================
# FSM HOLATLARI
# =====================================================

class AddProject(StatesGroup):
    title = State()
    category = State()
    description = State()
    file = State()


class DeleteProject(StatesGroup):
    project_id = State()


class AdminManage(StatesGroup):
    add_id = State()
    remove_id = State()


class SearchProject(StatesGroup):
    query = State()


# =====================================================
# DATABASE
# =====================================================

def execute_query(query):
    return query.execute()


async def db(query):
    return await asyncio.to_thread(execute_query, query)


async def is_admin(user_id):
    if user_id == SUPER_ADMIN_ID:
        return True

    try:
        result = await db(
            supabase.table("bot_admins")
            .select("telegram_id")
            .eq("telegram_id", user_id)
            .limit(1)
        )
        return bool(result.data)
    except Exception:
        logger.exception("Admin tekshirish xatosi")
        return False


# =====================================================
# ADMIN KLAVIATURALARI
# =====================================================

def admin_reply_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Loyiha qo‘shish")],
            [KeyboardButton(text="🗑 Loyihani o‘chirish")],
            [KeyboardButton(text="📁 Loyihalar")],
            [KeyboardButton(text="👥 Adminlar")],
        ],
        resize_keyboard=True,
        is_persistent=True
    )


def admin_manage_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Admin qo‘shish")],
            [KeyboardButton(text="➖ Admin chiqarish")],
            [KeyboardButton(text="🔙 Admin paneliga qaytish")],
        ],
        resize_keyboard=True,
        is_persistent=True
    )


def cancel_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="❌ Bekor qilish",
                callback_data="cancel"
            )]
        ]
    )


def category_keyboard():
    rows = []

    for i in range(0, len(CATEGORIES), 2):
        row = [
            InlineKeyboardButton(
                text=CATEGORIES[i],
                callback_data=f"category:{i}"
            )
        ]

        if i + 1 < len(CATEGORIES):
            row.append(
                InlineKeyboardButton(
                    text=CATEGORIES[i + 1],
                    callback_data=f"category:{i+1}"
                )
            )

        rows.append(row)

    rows.append([
        InlineKeyboardButton(
            text="❌ Bekor qilish",
            callback_data="cancel"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def public_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔎 Loyiha qidirish",
                    callback_data="search"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📂 Kategoriyalar",
                    callback_data="categories"
                )
            ],
        ]
    )


# =====================================================
# START
# =====================================================

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()

    if await is_admin(message.from_user.id):
        await message.answer(
            "⚙️ Admin boshqaruv paneli",
            reply_markup=admin_reply_keyboard()
        )
    else:
        await message.answer(
            "👋 AutoCAD Projects botiga xush kelibsiz!",
            reply_markup=public_keyboard()
        )


# =====================================================
# ADMIN ASOSIY TUGMALARI
# =====================================================

@dp.message(F.text == "➕ Loyiha qo‘shish")
async def add_project_start(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    await state.set_state(AddProject.title)
    await message.answer(
        "📝 Loyiha nomini yuboring:",
        reply_markup=cancel_keyboard()
    )


@dp.message(F.text == "🗑 Loyihani o‘chirish")
async def delete_project_start(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    await state.set_state(DeleteProject.project_id)
    await message.answer(
        "🗑 O‘chiriladigan loyihaning ID raqamini yuboring:"
    )


@dp.message(F.text == "📁 Loyihalar")
async def projects_button(message: Message):
    if not await is_admin(message.from_user.id):
        return

    await show_projects(message)


@dp.message(F.text == "👥 Adminlar")
async def admins_button(message: Message):
    if message.from_user.id != SUPER_ADMIN_ID:
        await message.answer("⛔ Bu bo‘lim faqat asosiy admin uchun.")
        return

    await message.answer(
        "👥 Adminlar boshqaruvi:",
        reply_markup=admin_manage_keyboard()
    )


# =====================================================
# ADMINLAR SUBMENYUSI
# =====================================================

@dp.message(F.text == "➕ Admin qo‘shish")
async def add_admin_start(message: Message, state: FSMContext):
    if message.from_user.id != SUPER_ADMIN_ID:
        return

    await state.set_state(AdminManage.add_id)
    await message.answer(
        "➕ Yangi adminning Telegram ID raqamini yuboring:"
    )


@dp.message(F.text == "➖ Admin chiqarish")
async def remove_admin_start(message: Message, state: FSMContext):
    if message.from_user.id != SUPER_ADMIN_ID:
        return

    await state.set_state(AdminManage.remove_id)
    await message.answer(
        "➖ O‘chiriladigan adminning Telegram ID raqamini yuboring:"
    )


@dp.message(F.text == "🔙 Admin paneliga qaytish")
async def back_admin_panel(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    await state.clear()
    await message.answer(
        "⚙️ Admin boshqaruv paneli",
        reply_markup=admin_reply_keyboard()
    )


# =====================================================
# ADMIN QO‘SHISH
# =====================================================

@dp.message(AdminManage.add_id)
async def add_admin_id(message: Message, state: FSMContext):
    if message.from_user.id != SUPER_ADMIN_ID:
        await state.clear()
        return

    raw_id = (message.text or "").strip()

    if not raw_id.isdigit():
        await message.answer("❗ ID faqat raqamlardan iborat bo‘lishi kerak.")
        return

    new_id = int(raw_id)

    if new_id == SUPER_ADMIN_ID:
        await message.answer("Bu foydalanuvchi asosiy admin.")
        return

    try:
        existing = await db(
            supabase.table("bot_admins")
            .select("telegram_id")
            .eq("telegram_id", new_id)
        )

        if existing.data:
            await message.answer("Bu foydalanuvchi allaqachon admin.")
        else:
            await db(
                supabase.table("bot_admins").insert({
                    "telegram_id": new_id
                })
            )
            await message.answer("✅ Admin muvaffaqiyatli qo‘shildi.")

        await state.clear()
        await message.answer(
            "👥 Adminlar boshqaruvi:",
            reply_markup=admin_manage_keyboard()
        )

    except Exception:
        logger.exception("Admin qo‘shish xatosi")
        await message.answer("❌ Admin qo‘shilmadi. Render Logs'ni tekshiring.")


# =====================================================
# ADMINNI O‘CHIRISH
# =====================================================

@dp.message(AdminManage.remove_id)
async def remove_admin_id(message: Message, state: FSMContext):
    if message.from_user.id != SUPER_ADMIN_ID:
        await state.clear()
        return

    raw_id = (message.text or "").strip()

    if not raw_id.isdigit():
        await message.answer("❗ ID faqat raqamlardan iborat bo‘lishi kerak.")
        return

    remove_id = int(raw_id)

    if remove_id == SUPER_ADMIN_ID:
        await message.answer("⛔ Asosiy adminni o‘chirib bo‘lmaydi.")
        return

    try:
        existing = await db(
            supabase.table("bot_admins")
            .select("telegram_id")
            .eq("telegram_id", remove_id)
        )

        if not existing.data:
            await message.answer("❌ Bunday admin topilmadi.")
        else:
            await db(
                supabase.table("bot_admins")
                .delete()
                .eq("telegram_id", remove_id)
            )
            await message.answer("✅ Admin chiqarildi.")

        await state.clear()
        await message.answer(
            "👥 Adminlar boshqaruvi:",
            reply_markup=admin_manage_keyboard()
        )

    except Exception:
        logger.exception("Admin o‘chirish xatosi")
        await message.answer("❌ Adminni o‘chirib bo‘lmadi.")


# =====================================================
# LOYIHA QO‘SHISH
# =====================================================

@dp.message(AddProject.title)
async def add_project_title(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await state.clear()
        return

    if not message.text:
        await message.answer("Loyiha nomini matn ko‘rinishida yuboring.")
        return

    await state.update_data(title=message.text.strip())
    await state.set_state(AddProject.category)

    await message.answer(
        "📂 Kategoriyani tanlang:",
        reply_markup=category_keyboard()
    )


@dp.callback_query(F.data.startswith("category:"), AddProject.category)
async def add_project_category(callback: CallbackQuery, state: FSMContext):
    index = int(callback.data.split(":")[1])

    if index < 0 or index >= len(CATEGORIES):
        await callback.answer("Kategoriya topilmadi.", show_alert=True)
        return

    await state.update_data(category=CATEGORIES[index])
    await state.set_state(AddProject.description)

    await callback.answer()
    await callback.message.answer(
        "📄 Loyiha tavsifini yuboring. Tavsif bo‘lmasa `-` yuboring:"
    )


@dp.message(AddProject.description)
async def add_project_description(message: Message, state: FSMContext):
    description = (message.text or "").strip()

    if description == "-":
        description = ""

    await state.update_data(description=description[:3000])
    await state.set_state(AddProject.file)

    await message.answer(
        "📎 Endi DWG yoki boshqa loyiha faylini hujjat sifatida yuboring:"
    )


@dp.message(AddProject.file, F.document)
async def save_project(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await state.clear()
        return

    data = await state.get_data()

    try:
        channel_message = await bot.send_document(
            chat_id=CHANNEL_ID,
            document=message.document.file_id,
            caption=(
                f"📁 {data['title']}\n"
                f"📂 {data['category']}\n\n"
                f"{data.get('description', '')}"
            )[:1024]
        )

        file_id = channel_message.document.file_id

        await db(
            supabase.table("projects").insert({
                "title": data["title"],
                "category": data["category"],
                "description": data.get("description", ""),
                "telegram_file_id": file_id,
                "download_count": 0
            })
        )

        await state.clear()

        await message.answer(
            "✅ Loyiha muvaffaqiyatli saqlandi!",
            reply_markup=admin_reply_keyboard()
        )

    except Exception:
        logger.exception("Loyiha saqlash xatosi")
        await message.answer("❌ Saqlashda xatolik yuz berdi.")


@dp.message(AddProject.file)
async def invalid_project_file(message: Message):
    await message.answer("❗ Faylni Telegram Document sifatida yuboring.")


# =====================================================
# LOYIHANI O‘CHIRISH
# =====================================================

@dp.message(DeleteProject.project_id)
async def delete_project_by_id(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await state.clear()
        return

    raw_id = (message.text or "").strip()

    if not raw_id.isdigit():
        await message.answer("❗ Loyiha ID raqamini yuboring.")
        return

    project_id = int(raw_id)

    try:
        result = await db(
            supabase.table("projects")
            .select("id,title")
            .eq("id", project_id)
            .limit(1)
        )

        if not result.data:
            await message.answer("❌ Bunday loyiha topilmadi.")
            return

        title = result.data[0]["title"]

        await db(
            supabase.table("projects")
            .delete()
            .eq("id", project_id)
        )

        await state.clear()

        await message.answer(
            f"✅ «{title}» loyihasi o‘chirildi.",
            reply_markup=admin_reply_keyboard()
        )

    except Exception:
        logger.exception("Loyihani o‘chirish xatosi")
        await message.answer("❌ Loyihani o‘chirib bo‘lmadi.")


# =====================================================
# LOYIHALAR RO‘YXATI
# =====================================================

async def show_projects(message: Message):
    try:
        result = await db(
            supabase.table("projects")
            .select("id,title,category")
            .order("id", desc=True)
            .limit(50)
        )

        projects = result.data or []

        if not projects:
            await message.answer("Hozircha loyihalar mavjud emas.")
            return

        lines = ["📁 LOYIHALAR RO‘YXATI", ""]

        for project in projects:
            lines.append(
                f"ID: {project['id']}\n"
                f"📌 {project['title']}\n"
                f"📂 {project['category']}\n"
            )

        await message.answer("\n".join(lines)[:4000])

    except Exception:
        logger.exception("Loyihalar ro‘yxati xatosi")
        await message.answer("❌ Loyihalarni olishda xatolik.")


# =====================================================
# FOYDALANUVCHI KATEGORIYALARI
# =====================================================

@dp.callback_query(F.data == "categories")
async def show_categories(callback: CallbackQuery):
    rows = []

    for i in range(0, len(CATEGORIES), 2):
        row = [
            InlineKeyboardButton(
                text=CATEGORIES[i],
                callback_data=f"publiccat:{i}"
            )
        ]

        if i + 1 < len(CATEGORIES):
            row.append(
                InlineKeyboardButton(
                    text=CATEGORIES[i + 1],
                    callback_data=f"publiccat:{i+1}"
                )
            )

        rows.append(row)

    await callback.message.answer(
        "📂 Kategoriyani tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("publiccat:"))
async def public_category(callback: CallbackQuery):
    index = int(callback.data.split(":")[1])
    category = CATEGORIES[index]

    try:
        result = await db(
            supabase.table("projects")
            .select("*")
            .eq("category", category)
            .order("id", desc=True)
            .limit(20)
        )

        projects = result.data or []

        if not projects:
            await callback.message.answer("Bu kategoriyada loyiha yo‘q.")
        else:
            for project in projects:
                caption = (
                    f"📁 {project['title']}\n"
                    f"📂 {project['category']}\n\n"
                    f"{project.get('description', '')}"
                )

                await callback.message.answer_document(
                    document=project["telegram_file_id"],
                    caption=caption[:1024]
                )

                await db(
                    supabase.table("projects")
                    .update({
                        "download_count":
                            (project.get("download_count") or 0) + 1
                    })
                    .eq("id", project["id"])
                )

    except Exception:
        logger.exception("Kategoriya loyihalari xatosi")
        await callback.message.answer("❌ Xatolik yuz berdi.")

    await callback.answer()


# =====================================================
# LOYIHA QIDIRISH
# =====================================================

@dp.callback_query(F.data == "search")
async def search_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SearchProject.query)
    await callback.message.answer("🔎 Loyiha nomini yozing:")
    await callback.answer()


@dp.message(SearchProject.query)
async def search_projects(message: Message, state: FSMContext):
    query_text = (message.text or "").strip()

    if not query_text:
        await message.answer("Loyiha nomini yozing.")
        return

    try:
        result = await db(
            supabase.table("projects")
            .select("*")
            .ilike("title", f"%{query_text}%")
            .order("id", desc=True)
            .limit(10)
        )

        projects = result.data or []
        await state.clear()

        if not projects:
            await message.answer("😕 Loyiha topilmadi.")
            return

        for project in projects:
            await message.answer_document(
                document=project["telegram_file_id"],
                caption=(
                    f"📁 {project['title']}\n"
                    f"📂 {project['category']}\n\n"
                    f"{project.get('description', '')}"
                )[:1024]
            )

    except Exception:
        logger.exception("Qidiruv xatosi")
        await state.clear()
        await message.answer("❌ Qidiruvda xatolik yuz berdi.")


# =====================================================
# BEKOR QILISH
# =====================================================

@dp.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Bekor qilindi.")

    if await is_admin(callback.from_user.id):
        await callback.message.answer(
            "⚙️ Admin paneli",
            reply_markup=admin_reply_keyboard()
        )
    else:
        await callback.message.answer(
            "🏗 Bosh menyu",
            reply_markup=public_keyboard()
        )


@dp.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext):
    await state.clear()

    if await is_admin(message.from_user.id):
        await message.answer(
            "⚙️ Admin paneli",
            reply_markup=admin_reply_keyboard()
        )
    else:
        await message.answer(
            "🏗 Bosh menyu",
            reply_markup=public_keyboard()
        )


# =====================================================
# WEBHOOK
# =====================================================

async def handle_webhook(request: web.Request):
    secret = request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token"
    )

    if secret != WEBHOOK_SECRET:
        raise web.HTTPForbidden()

    try:
        payload = await request.json()
        update = Update.model_validate(
            payload,
            context={"bot": bot}
        )
        await dp.feed_update(bot, update)
        return web.Response(text="OK")

    except Exception:
        logger.exception("Webhook xatosi")
        raise


async def on_startup(app):
    await bot.set_webhook(
        url=f"{BASE_URL}{WEBHOOK_PATH}",
        secret_token=WEBHOOK_SECRET
    )
    logger.info("Webhook ishga tushdi.")


async def on_shutdown(app):
    await bot.session.close()


app = web.Application()

app.router.add_get(
    "/",
    lambda request: web.Response(
        text="AutoCAD Projects Bot ishlayapti!"
    )
)

app.router.add_post(WEBHOOK_PATH, handle_webhook)

app.on_startup.append(on_startup)
app.on_cleanup.append(on_shutdown)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    web.run_app(app, host="0.0.0.0", port=port)
