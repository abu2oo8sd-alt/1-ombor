import os
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, F, BaseMiddleware
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, Update, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
)
from supabase import create_client

# =========================================================
# CONFIG — Render Environment Variables
# =========================================================
TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = (os.getenv("RENDER_EXTERNAL_URL") or "").rstrip("/")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").rstrip("/")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

SUPER_ADMIN_ID = 5000535277
CHANNEL_ID = -1002328943187  # Loyihalar fayllari yuboriladigan kanal
REQUIRED_CHANNEL = "@producto8"  # Majburiy obuna kanali
REQUIRED_CHANNEL_URL = "https://t.me/producto8"
WEBHOOK_PATH = "/telegram-webhook"

required = {
    "BOT_TOKEN": TOKEN,
    "RENDER_EXTERNAL_URL": BASE_URL,
    "WEBHOOK_SECRET": WEBHOOK_SECRET,
    "SUPABASE_URL": SUPABASE_URL,
    "SUPABASE_SECRET_KEY": SUPABASE_SECRET_KEY,
}
for key, value in required.items():
    if not value:
        raise ValueError(f"{key} Render Environment ichida topilmadi!")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("autocad-projects-bot")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)

# =========================================================
# LANGUAGES AND TRANSLATIONS
# =========================================================
LANGUAGES = {
    "uz": "🇺🇿 O‘zbekcha",
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
}

T = {
    "uz": {
        "welcome": "👋 AutoCAD Projects botiga xush kelibsiz!\nTilni tanlang:",
        "sub_title": "🔒 Botdan foydalanish uchun avval kanalimizga a’zo bo‘ling.",
        "sub_join": "📢 Kanalga a’zo bo‘lish",
        "sub_check": "✅ A’zolikni tekshirish",
        "sub_required": "❌ Siz hali kanalga a’zo emassiz. Avval a’zo bo‘ling, so‘ng tekshiring.",
        "sub_ok": "✅ A’zolik tasdiqlandi! Endi botdan foydalanishingiz mumkin.",
        "sub_error": "⚠️ A’zolikni tekshirib bo‘lmadi. Birozdan keyin qayta urinib ko‘ring.",
        "language_saved": "✅ Til saqlandi.",
        "choose_language": "🌐 Tilni tanlang:",
        "choose_category": "📂 Kerakli loyiha kategoriyasini tanlang:",
        "search": "🔎 Loyiha qidirish",
        "contact": "📞 Aloqa",
        "settings": "⚙️ Til sozlamalari",
        "back": "🔙 Bosh menyu",
        "admin_menu": "⚙️ Admin boshqaruv paneli",
        "add_project": "➕ Loyiha qo‘shish",
        "delete_project": "🗑 Loyihani o‘chirish",
        "projects": "📁 Loyihalar",
        "admins": "👥 Adminlar",
        "admin_add": "➕ Admin qo‘shish",
        "admin_remove": "➖ Admin chiqarish",
        "enter_title": "📝 Loyiha nomini yuboring:",
        "enter_category": "📂 Loyiha kategoriyasini tanlang:",
        "enter_description": "📄 Loyiha tavsifini yuboring yoki «O‘tkazish»ni bosing:",
        "skip": "⏭ O‘tkazish",
        "send_file": "📎 Endi loyiha faylini Telegram hujjati (Document) sifatida yuboring:",
        "saved": "✅ Loyiha kanalga va bazaga saqlandi!",
        "save_error": "❌ Saqlashda xatolik yuz berdi. Render Logs'ni tekshiring.",
        "invalid_file": "❗ Iltimos, faylni Document sifatida yuboring.",
        "invalid_category": "❗ Ro‘yxatdan kategoriyani tanlang.",
        "enter_project_id": "🆔 O‘chiriladigan loyiha ID raqamini yuboring:",
        "deleted": "✅ Loyiha o‘chirildi.",
        "project_missing": "❌ Bunday ID bilan loyiha topilmadi.",
        "delete_error": "❌ Loyihani o‘chirishda xatolik yuz berdi.",
        "enter_admin_id": "Yangi adminning Telegram ID raqamini yuboring:",
        "enter_remove_admin_id": "Chiqariladigan adminning Telegram ID raqamini yuboring:",
        "admin_added": "✅ Admin qo‘shildi.",
        "admin_removed": "✅ Admin chiqarildi.",
        "admin_exists": "Bu foydalanuvchi allaqachon admin.",
        "admin_missing": "Bunday admin topilmadi.",
        "bad_id": "❗ ID faqat raqamlardan iborat bo‘lishi kerak.",
        "admin_only": "⛔ Bu bo‘lim faqat adminlar uchun.",
        "super_only": "⛔ Adminlarni faqat asosiy admin boshqarishi mumkin.",
        "no_projects": "Hozircha loyihalar mavjud emas.",
        "projects_title": "📁 Loyihalar ro‘yxati:",
        "search_prompt": "🔎 Qidiriladigan loyiha nomini yozing:",
        "searching": "🔎 Qidirilmoqda...",
        "search_results": "🔎 Qidiruv natijalari:",
        "not_found": "😕 Loyiha topilmadi.",
        "contact_prompt": "✍️ Adminga yubormoqchi bo‘lgan xabaringizni yozing:",
        "contact_sent": "✅ Xabaringiz adminga yuborildi.",
        "contact_failed": "❌ Xabar yuborilmadi. Keyinroq urinib ko‘ring.",
        "cancel": "❌ Bekor qilish",
        "cancelled": "❌ Amal bekor qilindi.",
        "reply_help": "Javob formati: /reply TELEGRAM_ID xabar",
        "reply_sent": "✅ Javob yuborildi.",
        "reply_failed": "❌ Javob yuborilmadi.",
        "user_message": "📩 Foydalanuvchidan xabar\nID: {id}\nIsm: {name}\n\n{text}",
        "error": "❌ Xatolik yuz berdi. Keyinroq urinib ko‘ring.",
    },
    "ru": {
        "welcome": "👋 Добро пожаловать в AutoCAD Projects!\nВыберите язык:",
        "sub_title": "🔒 Чтобы пользоваться ботом, сначала подпишитесь на наш канал.",
        "sub_join": "📢 Подписаться на канал",
        "sub_check": "✅ Проверить подписку",
        "sub_required": "❌ Вы ещё не подписались на канал. Подпишитесь и проверьте снова.",
        "sub_ok": "✅ Подписка подтверждена! Теперь вы можете пользоваться ботом.",
        "sub_error": "⚠️ Не удалось проверить подписку. Попробуйте немного позже.",
        "language_saved": "✅ Язык сохранён.",
        "choose_language": "🌐 Выберите язык:",
        "choose_category": "📂 Выберите категорию проекта:",
        "search": "🔎 Поиск проектов",
        "contact": "📞 Связаться с администратором",
        "settings": "⚙️ Настройки языка",
        "back": "🔙 Главное меню",
        "admin_menu": "⚙️ Панель администратора",
        "add_project": "➕ Добавить проект",
        "delete_project": "🗑 Удалить проект",
        "projects": "📁 Проекты",
        "admins": "👥 Администраторы",
        "admin_add": "➕ Добавить администратора",
        "admin_remove": "➖ Удалить администратора",
        "enter_title": "📝 Отправьте название проекта:",
        "enter_category": "📂 Выберите категорию проекта:",
        "enter_description": "📄 Отправьте описание или нажмите «Пропустить»:",
        "skip": "⏭ Пропустить",
        "send_file": "📎 Теперь отправьте файл проекта как документ Telegram:",
        "saved": "✅ Проект сохранён в канале и базе данных!",
        "save_error": "❌ Ошибка сохранения. Проверьте Render Logs.",
        "invalid_file": "❗ Отправьте файл как документ (Document).",
        "invalid_category": "❗ Выберите категорию из списка.",
        "enter_project_id": "🆔 Отправьте ID проекта для удаления:",
        "deleted": "✅ Проект удалён.",
        "project_missing": "❌ Проект с таким ID не найден.",
        "delete_error": "❌ Ошибка при удалении проекта.",
        "enter_admin_id": "Отправьте Telegram ID нового администратора:",
        "enter_remove_admin_id": "Отправьте Telegram ID администратора для удаления:",
        "admin_added": "✅ Администратор добавлен.",
        "admin_removed": "✅ Администратор удалён.",
        "admin_exists": "Этот пользователь уже является администратором.",
        "admin_missing": "Администратор не найден.",
        "bad_id": "❗ ID должен содержать только цифры.",
        "admin_only": "⛔ Этот раздел доступен только администраторам.",
        "super_only": "⛔ Управлять администраторами может только главный администратор.",
        "no_projects": "Пока проектов нет.",
        "projects_title": "📁 Список проектов:",
        "search_prompt": "🔎 Введите название проекта для поиска:",
        "searching": "🔎 Идёт поиск...",
        "search_results": "🔎 Результаты поиска:",
        "not_found": "😕 Проект не найден.",
        "contact_prompt": "✍️ Напишите сообщение администратору:",
        "contact_sent": "✅ Сообщение отправлено администратору.",
        "contact_failed": "❌ Не удалось отправить сообщение. Попробуйте позже.",
        "cancel": "❌ Отмена",
        "cancelled": "❌ Действие отменено.",
        "reply_help": "Формат ответа: /reply TELEGRAM_ID текст",
        "reply_sent": "✅ Ответ отправлен.",
        "reply_failed": "❌ Не удалось отправить ответ.",
        "user_message": "📩 Сообщение от пользователя\nID: {id}\nИмя: {name}\n\n{text}",
        "error": "❌ Произошла ошибка. Попробуйте позже.",
    },
    "en": {
        "welcome": "👋 Welcome to AutoCAD Projects!\nChoose your language:",
        "sub_title": "🔒 Please subscribe to our channel before using the bot.",
        "sub_join": "📢 Subscribe to the channel",
        "sub_check": "✅ Check subscription",
        "sub_required": "❌ You have not joined the channel yet. Join it and check again.",
        "sub_ok": "✅ Subscription confirmed! You can now use the bot.",
        "sub_error": "⚠️ Could not verify your subscription. Please try again later.",
        "language_saved": "✅ Language saved.",
        "choose_language": "🌐 Choose your language:",
        "choose_category": "📂 Choose a project category:",
        "search": "🔎 Search projects",
        "contact": "📞 Contact admin",
        "settings": "⚙️ Language settings",
        "back": "🔙 Main menu",
        "admin_menu": "⚙️ Admin panel",
        "add_project": "➕ Add project",
        "delete_project": "🗑 Delete project",
        "projects": "📁 Projects",
        "admins": "👥 Administrators",
        "admin_add": "➕ Add administrator",
        "admin_remove": "➖ Remove administrator",
        "enter_title": "📝 Send the project title:",
        "enter_category": "📂 Choose the project category:",
        "enter_description": "📄 Send a description or press Skip:",
        "skip": "⏭ Skip",
        "send_file": "📎 Now send the project file as a Telegram document:",
        "saved": "✅ Project saved to the channel and database!",
        "save_error": "❌ Save error. Check Render Logs.",
        "invalid_file": "❗ Please send the file as a Telegram Document.",
        "invalid_category": "❗ Choose a category from the list.",
        "enter_project_id": "🆔 Send the project ID to delete:",
        "deleted": "✅ Project deleted.",
        "project_missing": "❌ No project found with that ID.",
        "delete_error": "❌ Error while deleting the project.",
        "enter_admin_id": "Send the Telegram ID of the new administrator:",
        "enter_remove_admin_id": "Send the Telegram ID of the administrator to remove:",
        "admin_added": "✅ Administrator added.",
        "admin_removed": "✅ Administrator removed.",
        "admin_exists": "This user is already an administrator.",
        "admin_missing": "Administrator not found.",
        "bad_id": "❗ ID must contain digits only.",
        "admin_only": "⛔ This section is for administrators only.",
        "super_only": "⛔ Only the main administrator can manage administrators.",
        "no_projects": "There are no projects yet.",
        "projects_title": "📁 Project list:",
        "search_prompt": "🔎 Enter a project name to search:",
        "searching": "🔎 Searching...",
        "search_results": "🔎 Search results:",
        "not_found": "😕 Project not found.",
        "contact_prompt": "✍️ Write your message to the administrator:",
        "contact_sent": "✅ Your message has been sent to the administrator.",
        "contact_failed": "❌ Message could not be sent. Please try again later.",
        "cancel": "❌ Cancel",
        "cancelled": "❌ Action cancelled.",
        "reply_help": "Reply format: /reply TELEGRAM_ID message",
        "reply_sent": "✅ Reply sent.",
        "reply_failed": "❌ Could not send the reply.",
        "user_message": "📩 Message from user\nID: {id}\nName: {name}\n\n{text}",
        "error": "❌ An error occurred. Please try again later.",
    },
}

# Categories intentionally exclude: Factory, Objects, Water/sewer,
# Ready DWG blocks, Ready details, Fonts and linetypes.
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

CATEGORY_TRANSLATIONS = {
    "uz": CATEGORIES,
    "ru": [
        "🏠 Дом", "🏢 Офис", "🛋 Дизайн интерьера", "🏫 Школа и детский сад",
        "🛍 Торговый центр", "🛣 Дороги и мосты", "🏗 Другие здания",
        "☕ Небольшие кафе", "🚏 Умные остановки", "🚗 Автомобили",
        "⚡ Электрические схемы", "🧱 Конструкции и фундамент",
        "🪑 Чертежи мебели", "🌳 Ландшафтный дизайн", "📐 Готовые шаблоны",
        "🎨 Штриховки и текстуры", "🚜 Фермы и животноводство",
    ],
    "en": [
        "🏠 House", "🏢 Office", "🛋 Interior design", "🏫 School and kindergarten",
        "🛍 Shopping mall", "🛣 Roads and bridges", "🏗 Other buildings",
        "☕ Small cafes", "🚏 Smart bus stops", "🚗 Vehicles",
        "⚡ Electrical drawings", "🧱 Structures and foundations",
        "🪑 Furniture drawings", "🌳 Landscape design", "📐 Ready templates",
        "🎨 Hatches and textures", "🚜 Farm and livestock projects",
    ],
}
CATEGORY_TO_CANONICAL = {
    CATEGORY_TRANSLATIONS[lang][i]: CATEGORIES[i]
    for lang in LANGUAGES for i in range(len(CATEGORIES))
}

# =========================================================
# FSM STATES
# =========================================================
class AddProject(StatesGroup):
    title = State()
    category = State()
    description = State()
    file = State()

class DeleteProject(StatesGroup):
    project_id = State()

class SearchProject(StatesGroup):
    query = State()

class ContactAdmin(StatesGroup):
    message = State()

class AdminManage(StatesGroup):
    add_id = State()
    remove_id = State()

# =========================================================
# DATABASE HELPERS
# =========================================================
def _execute(query):
    return query.execute()

async def db(query):
    return await asyncio.to_thread(_execute, query)

async def get_language(user_id: int) -> str:
    try:
        result = await db(
            supabase.table("bot_users").select("language")
            .eq("telegram_id", user_id).limit(1)
        )
        if result.data:
            lang = result.data[0].get("language", "uz")
            return lang if lang in LANGUAGES else "uz"
    except Exception:
        logger.exception("Could not read user language")
    return "uz"

async def save_user(user_id: int, lang: str):
    try:
        await db(supabase.table("bot_users").upsert({
            "telegram_id": user_id,
            "language": lang,
        }, on_conflict="telegram_id"))
    except Exception:
        logger.exception("Could not save user language")

async def is_admin(user_id: int) -> bool:
    if user_id == SUPER_ADMIN_ID:
        return True
    try:
        result = await db(
            supabase.table("bot_admins").select("telegram_id")
            .eq("telegram_id", user_id).limit(1)
        )
        return bool(result.data)
    except Exception:
        logger.exception("Admin check failed")
        return False

# =========================================================
# REQUIRED CHANNEL SUBSCRIPTION
# =========================================================
async def is_subscribed(user_id: int) -> bool:
    """Return True only when Telegram confirms the user joined @producto8."""
    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        status = getattr(member.status, "value", member.status)
        if status in ("creator", "administrator", "member"):
            return True
        return status == "restricted" and bool(getattr(member, "is_member", False))
    except Exception:
        logger.exception("Could not verify membership in %s", REQUIRED_CHANNEL)
        raise


def subscription_keyboard(lang: str):
    tr = T.get(lang, T["uz"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=tr["sub_join"], url=REQUIRED_CHANNEL_URL)],
        [InlineKeyboardButton(text=tr["sub_check"], callback_data="check_subscription")],
    ])


async def show_subscription_required(message: Message, lang: str):
    tr = T.get(lang, T["uz"])
    await message.answer(tr["sub_title"], reply_markup=subscription_keyboard(lang))


class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        if not event.from_user:
            return await handler(event, data)

        # /start always reaches its handler so the user sees the subscription prompt.
        if (event.text or "").split(maxsplit=1)[0] == "/start":
            return await handler(event, data)

        # Main and additional admins are allowed to manage the bot without subscribing.
        if await is_admin(event.from_user.id):
            return await handler(event, data)

        lang = await get_language(event.from_user.id)
        try:
            joined = await is_subscribed(event.from_user.id)
        except Exception:
            await event.answer(T[lang]["sub_error"])
            return

        if not joined:
            await show_subscription_required(event, lang)
            return

        return await handler(event, data)


dp.message.middleware(SubscriptionMiddleware())


@dp.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = await get_language(user_id)
    try:
        joined = await is_subscribed(user_id)
    except Exception:
        await callback.answer(T[lang]["sub_error"], show_alert=True)
        return

    if not joined:
        await callback.answer(T[lang]["sub_required"], show_alert=True)
        return

    await callback.answer(T[lang]["sub_ok"])
    await callback.message.answer(
        T[lang]["welcome"],
        reply_markup=language_keyboard(),
    )


# =========================================================
# KEYBOARDS
# =========================================================
def language_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=label)] for label in LANGUAGES.values()],
        resize_keyboard=True,
        is_persistent=True,
    )

def main_keyboard(lang: str, admin: bool = False):
    t = T[lang]
    if admin:
        # Admin panel: exactly four buttons in the bottom keyboard.
        rows = [
            [KeyboardButton(text=t["add_project"])],
            [KeyboardButton(text=t["delete_project"])],
            [KeyboardButton(text=t["projects"])],
            [KeyboardButton(text=t["admins"])],
        ]
    else:
        rows = [
            [KeyboardButton(text=t["search"])],
            [KeyboardButton(text=t["contact"])],
            [KeyboardButton(text=t["settings"])],
        ]
        names = CATEGORY_TRANSLATIONS[lang]
        for i in range(0, len(names), 2):
            row = [KeyboardButton(text=names[i])]
            if i + 1 < len(names):
                row.append(KeyboardButton(text=names[i + 1]))
            rows.append(row)
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, is_persistent=True)

def admin_manage_keyboard(lang: str):
    t = T[lang]
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t["admin_add"])],
            [KeyboardButton(text=t["admin_remove"])],
            [KeyboardButton(text=t["back"])],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )

def category_keyboard(lang: str):
    names = CATEGORY_TRANSLATIONS[lang]
    rows = []
    for i in range(0, len(names), 2):
        row = [KeyboardButton(text=names[i])]
        if i + 1 < len(names):
            row.append(KeyboardButton(text=names[i + 1]))
        rows.append(row)
    rows.append([KeyboardButton(text=T[lang]["cancel"])])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

def flow_keyboard(lang: str, skip: bool = False):
    rows = []
    if skip:
        rows.append([KeyboardButton(text=T[lang]["skip"])])
    rows.append([KeyboardButton(text=T[lang]["cancel"])])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

async def show_main(message: Message):
    user_id = message.from_user.id
    lang = await get_language(user_id)
    admin = await is_admin(user_id)
    prompt = T[lang]["admin_menu"] if admin else T[lang]["choose_category"]
    await message.answer(prompt, reply_markup=main_keyboard(lang, admin))

# =========================================================
# START / LANGUAGE SELECTION
# =========================================================
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    lang = await get_language(message.from_user.id)

    if not await is_admin(message.from_user.id):
        try:
            if not await is_subscribed(message.from_user.id):
                await show_subscription_required(message, lang)
                return
        except Exception:
            await message.answer(T[lang]["sub_error"])
            return

    await save_user(message.from_user.id, lang)
    await message.answer(T[lang]["welcome"], reply_markup=language_keyboard())

@dp.message(F.text.in_(list(LANGUAGES.values())))
async def choose_language(message: Message, state: FSMContext):
    lang = next(code for code, label in LANGUAGES.items() if label == message.text)
    await save_user(message.from_user.id, lang)
    await state.clear()
    admin = await is_admin(message.from_user.id)
    prompt = T[lang]["admin_menu"] if admin else T[lang]["choose_category"]
    await message.answer(
        T[lang]["language_saved"] + "\n\n" + prompt,
        reply_markup=main_keyboard(lang, admin),
    )

@dp.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext):
    await state.clear()
    lang = await get_language(message.from_user.id)
    await message.answer(
        T[lang]["cancelled"],
        reply_markup=main_keyboard(lang, await is_admin(message.from_user.id)),
    )

# =========================================================
# GENERAL MENU ROUTER
# =========================================================
@dp.message(StateFilter(None), F.text)
async def general_menu_router(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_language(user_id)
    text = (message.text or "").strip()
    tr = T[lang]

    if text == tr["back"]:
        await show_main(message)
        return
    if text == tr["settings"]:
        await message.answer(tr["choose_language"], reply_markup=language_keyboard())
        return
    if text == tr["search"]:
        await state.set_state(SearchProject.query)
        await message.answer(tr["search_prompt"], reply_markup=flow_keyboard(lang))
        return
    if text == tr["contact"]:
        await state.set_state(ContactAdmin.message)
        await message.answer(tr["contact_prompt"], reply_markup=flow_keyboard(lang))
        return

    if text == tr["add_project"]:
        if not await is_admin(user_id):
            await message.answer(tr["admin_only"])
            return
        await state.set_state(AddProject.title)
        await message.answer(tr["enter_title"], reply_markup=flow_keyboard(lang))
        return
    if text == tr["delete_project"]:
        if not await is_admin(user_id):
            await message.answer(tr["admin_only"])
            return
        await state.set_state(DeleteProject.project_id)
        await message.answer(tr["enter_project_id"], reply_markup=flow_keyboard(lang))
        return
    if text == tr["projects"]:
        if not await is_admin(user_id):
            await message.answer(tr["admin_only"])
            return
        await show_projects(message, lang)
        return
    if text == tr["admins"]:
        if user_id != SUPER_ADMIN_ID:
            await message.answer(tr["super_only"])
            return
        await message.answer(tr["admins"], reply_markup=admin_manage_keyboard(lang))
        return
    if text in (tr["admin_add"], tr["admin_remove"]):
        if user_id != SUPER_ADMIN_ID:
            await message.answer(tr["super_only"])
            return
        if text == tr["admin_add"]:
            await state.set_state(AdminManage.add_id)
            await message.answer(tr["enter_admin_id"], reply_markup=flow_keyboard(lang))
        else:
            await state.set_state(AdminManage.remove_id)
            await message.answer(tr["enter_remove_admin_id"], reply_markup=flow_keyboard(lang))
        return

    canonical = CATEGORY_TO_CANONICAL.get(text)
    if canonical:
        await send_category_projects(message, canonical, lang)
        return

    await message.answer(
        tr["admin_menu"] if await is_admin(user_id) else tr["choose_category"],
        reply_markup=main_keyboard(lang, await is_admin(user_id)),
    )

# =========================================================
# ADD PROJECT FLOW
# =========================================================
@dp.message(AddProject.title)
async def add_project_title(message: Message, state: FSMContext):
    lang = await get_language(message.from_user.id)
    if message.text == T[lang]["cancel"]:
        await state.clear()
        await show_main(message)
        return
    title = (message.text or "").strip()
    if not title or len(title) > 200:
        await message.answer(T[lang]["enter_title"])
        return
    await state.update_data(title=title)
    await state.set_state(AddProject.category)
    await message.answer(T[lang]["enter_category"], reply_markup=category_keyboard(lang))

@dp.message(AddProject.category)
async def add_project_category(message: Message, state: FSMContext):
    lang = await get_language(message.from_user.id)
    if message.text == T[lang]["cancel"]:
        await state.clear()
        await show_main(message)
        return
    category = CATEGORY_TO_CANONICAL.get((message.text or "").strip())
    if not category:
        await message.answer(T[lang]["invalid_category"], reply_markup=category_keyboard(lang))
        return
    await state.update_data(category=category)
    await state.set_state(AddProject.description)
    await message.answer(T[lang]["enter_description"], reply_markup=flow_keyboard(lang, skip=True))

@dp.message(AddProject.description, F.text)
async def add_project_description(message: Message, state: FSMContext):
    lang = await get_language(message.from_user.id)
    text = (message.text or "").strip()
    if text == T[lang]["cancel"]:
        await state.clear()
        await show_main(message)
        return
    description = "" if text == T[lang]["skip"] else text[:3000]
    await state.update_data(description=description)
    await state.set_state(AddProject.file)
    await message.answer(T[lang]["send_file"], reply_markup=ReplyKeyboardRemove())

@dp.message(AddProject.file, F.document)
async def add_project_file(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_language(user_id)
    if not await is_admin(user_id):
        await state.clear()
        await message.answer(T[lang]["admin_only"])
        return
    data = await state.get_data()
    try:
        caption = (
            f"📁 {data['title']}\n📂 {data['category']}\n\n"
            f"{data.get('description', '')}"
        )[:1024]
        channel_message = await bot.send_document(
            chat_id=CHANNEL_ID,
            document=message.document.file_id,
            caption=caption,
        )
        saved_file_id = channel_message.document.file_id
        await db(supabase.table("projects").insert({
            "title": data["title"],
            "category": data["category"],
            "description": data.get("description", ""),
            "telegram_file_id": saved_file_id,
            "download_count": 0,
        }))
        await state.clear()
        await message.answer(T[lang]["saved"], reply_markup=main_keyboard(lang, True))
    except Exception:
        logger.exception("Project upload failed")
        await message.answer(T[lang]["save_error"])

@dp.message(AddProject.file)
async def add_project_invalid_file(message: Message):
    lang = await get_language(message.from_user.id)
    if message.text == T[lang]["cancel"]:
        await message.answer(T[lang]["cancelled"], reply_markup=main_keyboard(lang, True))
        return
    await message.answer(T[lang]["invalid_file"])

# =========================================================
# DELETE PROJECT FLOW
# =========================================================
@dp.message(DeleteProject.project_id)
async def delete_project_by_id(message: Message, state: FSMContext):
    lang = await get_language(message.from_user.id)
    raw = (message.text or "").strip()
    if raw == T[lang]["cancel"]:
        await state.clear()
        await show_main(message)
        return
    if not raw.isdigit():
        await message.answer(T[lang]["bad_id"])
        return
    try:
        existing = await db(
            supabase.table("projects").select("id")
            .eq("id", int(raw)).limit(1)
        )
        if not existing.data:
            await message.answer(T[lang]["project_missing"])
            return
        await db(supabase.table("projects").delete().eq("id", int(raw)))
        await state.clear()
        await message.answer(T[lang]["deleted"], reply_markup=main_keyboard(lang, True))
    except Exception:
        logger.exception("Project delete failed")
        await message.answer(T[lang]["delete_error"])

# =========================================================
# PROJECT DISPLAY / SEARCH
# =========================================================
async def increment_download(project_id: int):
    try:
        result = await db(
            supabase.table("projects").select("download_count")
            .eq("id", project_id).limit(1)
        )
        count = int(result.data[0].get("download_count") or 0) if result.data else 0
        await db(supabase.table("projects").update({
            "download_count": count + 1
        }).eq("id", project_id))
    except Exception:
        logger.exception("Download counter update failed")

async def send_project(message: Message, project: dict):
    caption = (
        f"📁 {project.get('title', '')}\n"
        f"📂 {project.get('category', '')}\n\n"
        f"{project.get('description') or ''}"
    )[:1024]
    await message.answer_document(
        document=project["telegram_file_id"],
        caption=caption,
    )
    await increment_download(int(project["id"]))

async def send_category_projects(message: Message, category: str, lang: str):
    try:
        result = await db(
            supabase.table("projects").select("*")
            .eq("category", category).order("id", desc=True).limit(20)
        )
        projects = result.data or []
        if not projects:
            await message.answer(T[lang]["no_projects"])
            return
        for project in projects:
            await send_project(message, project)
    except Exception:
        logger.exception("Category project listing failed")
        await message.answer(T[lang]["error"])

@dp.message(SearchProject.query)
async def search_projects(message: Message, state: FSMContext):
    lang = await get_language(message.from_user.id)
    query = (message.text or "").strip()
    if query == T[lang]["cancel"]:
        await state.clear()
        await show_main(message)
        return
    if not query:
        await message.answer(T[lang]["search_prompt"])
        return
    try:
        await message.answer(T[lang]["searching"])
        result = await db(
            supabase.table("projects").select("*")
            .ilike("title", f"%{query}%")
            .order("id", desc=True).limit(10)
        )
        projects = result.data or []
        await state.clear()
        if not projects:
            await message.answer(T[lang]["not_found"], reply_markup=main_keyboard(lang, await is_admin(message.from_user.id)))
            return
        await message.answer(T[lang]["search_results"])
        for project in projects:
            await send_project(message, project)
        await message.answer(T[lang]["back"], reply_markup=main_keyboard(lang, await is_admin(message.from_user.id)))
    except Exception:
        logger.exception("Project search failed")
        await state.clear()
        await message.answer(T[lang]["error"])

async def show_projects(message: Message, lang: str):
    try:
        result = await db(
            supabase.table("projects").select("id,title,category")
            .order("id", desc=True).limit(50)
        )
        projects = result.data or []
        if not projects:
            await message.answer(T[lang]["no_projects"])
            return
        lines = [T[lang]["projects_title"], ""]
        for project in projects:
            lines.append(f"ID: {project['id']} | {project['title']} | {project['category']}")
        await message.answer("\n".join(lines)[:4000])
    except Exception:
        logger.exception("Project list failed")
        await message.answer(T[lang]["error"])

# =========================================================
# CONTACT ADMIN
# =========================================================
@dp.message(ContactAdmin.message)
async def contact_admin(message: Message, state: FSMContext):
    lang = await get_language(message.from_user.id)
    if not message.text:
        await message.answer(T[lang]["contact_prompt"])
        return
    if message.text.strip() == T[lang]["cancel"]:
        await state.clear()
        await show_main(message)
        return
    user = message.from_user
    body = T[lang]["user_message"].format(
        id=user.id, name=user.full_name, text=message.text
    )
    try:
        result = await db(supabase.table("bot_admins").select("telegram_id"))
        admin_ids = {int(row["telegram_id"]) for row in (result.data or [])}
        admin_ids.add(SUPER_ADMIN_ID)
        delivered = False
        for admin_id in admin_ids:
            try:
                await bot.send_message(admin_id, body)
                delivered = True
            except Exception:
                logger.warning("Could not deliver message to admin %s", admin_id)
        await state.clear()
        await message.answer(
            T[lang]["contact_sent"] if delivered else T[lang]["contact_failed"],
            reply_markup=main_keyboard(lang, await is_admin(user.id)),
        )
    except Exception:
        logger.exception("Contact admin failed")
        await message.answer(T[lang]["contact_failed"])

@dp.message(Command("reply"))
async def reply_to_user(message: Message):
    lang = await get_language(message.from_user.id)
    if not await is_admin(message.from_user.id):
        await message.answer(T[lang]["admin_only"])
        return
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3 or not parts[1].isdigit():
        await message.answer(T[lang]["reply_help"])
        return
    try:
        await bot.send_message(int(parts[1]), "📨 Admin javobi:\n\n" + parts[2])
        await message.answer(T[lang]["reply_sent"])
    except Exception:
        logger.exception("Reply to user failed")
        await message.answer(T[lang]["reply_failed"])

# =========================================================
# ADMIN MANAGEMENT — MAIN ADMIN ONLY
# =========================================================
@dp.message(AdminManage.add_id)
async def add_admin(message: Message, state: FSMContext):
    lang = await get_language(message.from_user.id)
    if message.from_user.id != SUPER_ADMIN_ID:
        await state.clear()
        await message.answer(T[lang]["super_only"])
        return
    raw = (message.text or "").strip()
    if raw == T[lang]["cancel"]:
        await state.clear()
        await show_main(message)
        return
    if not raw.isdigit():
        await message.answer(T[lang]["bad_id"])
        return
    new_id = int(raw)
    if new_id == SUPER_ADMIN_ID:
        await message.answer(T[lang]["admin_exists"])
        return
    try:
        existing = await db(
            supabase.table("bot_admins").select("telegram_id")
            .eq("telegram_id", new_id).limit(1)
        )
        if existing.data:
            await message.answer(T[lang]["admin_exists"])
        else:
            await db(supabase.table("bot_admins").insert({"telegram_id": new_id}))
            await message.answer(T[lang]["admin_added"])
        await state.clear()
        await message.answer(T[lang]["admin_menu"], reply_markup=main_keyboard(lang, True))
    except Exception:
        logger.exception("Add admin failed")
        await message.answer(T[lang]["error"])

@dp.message(AdminManage.remove_id)
async def remove_admin(message: Message, state: FSMContext):
    lang = await get_language(message.from_user.id)
    if message.from_user.id != SUPER_ADMIN_ID:
        await state.clear()
        await message.answer(T[lang]["super_only"])
        return
    raw = (message.text or "").strip()
    if raw == T[lang]["cancel"]:
        await state.clear()
        await show_main(message)
        return
    if not raw.isdigit():
        await message.answer(T[lang]["bad_id"])
        return
    target_id = int(raw)
    if target_id == SUPER_ADMIN_ID:
        await message.answer(T[lang]["super_only"])
        return
    try:
        existing = await db(
            supabase.table("bot_admins").select("telegram_id")
            .eq("telegram_id", target_id).limit(1)
        )
        if not existing.data:
            await message.answer(T[lang]["admin_missing"])
        else:
            await db(supabase.table("bot_admins").delete().eq("telegram_id", target_id))
            await message.answer(T[lang]["admin_removed"])
        await state.clear()
        await message.answer(T[lang]["admin_menu"], reply_markup=main_keyboard(lang, True))
    except Exception:
        logger.exception("Remove admin failed")
        await message.answer(T[lang]["error"])

# =========================================================
# WEBHOOK / SERVER
# =========================================================
async def handle_webhook(request: web.Request):
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret != WEBHOOK_SECRET:
        raise web.HTTPForbidden()
    try:
        payload = await request.json()
        update = Update.model_validate(payload, context={"bot": bot})
        await dp.feed_update(bot, update)
        return web.Response(text="OK")
    except Exception:
        logger.exception("Webhook update error")
        raise

async def on_startup(app: web.Application):
    await bot.set_webhook(
        url=f"{BASE_URL}{WEBHOOK_PATH}",
        secret_token=WEBHOOK_SECRET,
    )
    logger.info("Telegram webhook configured")

async def on_shutdown(app: web.Application):
    await bot.session.close()
    logger.info("Bot stopped")

app = web.Application()
app.router.add_get("/", lambda request: web.Response(text="AutoCAD Projects Bot is running"))
app.router.add_post(WEBHOOK_PATH, handle_webhook)
app.on_startup.append(on_startup)
app.on_cleanup.append(on_shutdown)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    web.run_app(app, host="0.0.0.0", port=port)
