import os
import asyncio
import logging
import traceback
from html import escape

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, Update, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from supabase import create_client


# =========================================================
# CONFIG
# =========================================================
TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = (os.getenv("RENDER_EXTERNAL_URL") or "").rstrip("/")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").rstrip("/")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

SUPER_ADMIN_ID = 5000535277
CHANNEL_ID = -1002328943187
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
logger = logging.getLogger("autocad-bot")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)


# =========================================================
# TRANSLATIONS
# =========================================================
LANGUAGES = {
    "uz": "🇺🇿 O‘zbekcha",
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
    "tg": "🇹🇯 Тоҷикӣ",
}

T = {
    "uz": {
        "welcome": "👋 AutoCAD Projects Bot'ga xush kelibsiz!\nTilni tanlang:",
        "language_saved": "✅ Til saqlandi.",
        "menu": "🏗 Bosh menyu",
        "search": "🔎 Loyiha qidirish",
        "contact": "📞 Aloqa",
        "top": "🔥 TOP-10 loyihalar",
        "settings": "⚙️ Sozlamalar",
        "choose_category": "📂 Kategoriyani tanlang yoki menyudan foydalaning:",
        "choose_language": "🌐 Tilni tanlang:",
        "search_prompt": "🔎 Qidiriladigan loyiha nomini yozing:",
        "searching": "Qidirilmoqda...",
        "not_found": "😕 Hech qanday loyiha topilmadi.",
        "results": "🔎 Qidiruv natijalari:",
        "top_empty": "Hozircha yuklab olingan loyihalar yo‘q.",
        "top_title": "🔥 ENG KO‘P YUKLAB OLINGAN LOYIHALAR",
        "downloads": "Yuklab olishlar",
        "contact_prompt": "✍️ Adminga yubormoqchi bo‘lgan xabaringizni yozing:",
        "contact_sent": "✅ Xabaringiz adminga yuborildi.",
        "contact_failed": "❌ Xabar yuborilmadi. Keyinroq urinib ko‘ring.",
        "cancelled": "❌ Amal bekor qilindi.",
        "admin_menu": "⚙️ Admin boshqaruv paneli",
        "add_project": "➕ Loyiha qo‘shish",
        "projects": "📁 Loyihalar",
        "admins": "👥 Adminlar",
        "admin_add": "➕ Admin qo‘shish",
        "admin_remove": "➖ Adminni o‘chirish",
        "admin_list": "📋 Adminlar ro‘yxati",
        "enter_title": "📝 Loyiha nomini kiriting:",
        "enter_category": "📂 Kategoriyani tanlang:",
        "enter_description": "📄 Loyiha tavsifini yozing yoki «O‘tkazish»ni bosing:",
        "skip": "⏭ O‘tkazish",
        "send_file": "📎 Endi loyiha faylini hujjat sifatida yuboring:",
        "saved": "✅ Loyiha kanal va bazaga saqlandi!",
        "save_error": "❌ Saqlashda xatolik. Render Logs'ni tekshiring.",
        "invalid_category": "❗ Ro‘yxatdan kategoriya tanlang.",
        "invalid_file": "❗ Faylni Telegram Document sifatida yuboring.",
        "no_projects": "Hozircha loyihalar mavjud emas.",
        "admin_only": "⛔ Bu bo‘lim faqat adminlar uchun.",
        "enter_admin_id": "Yangi adminning Telegram ID raqamini yuboring:",
        "enter_remove_id": "O‘chiriladigan adminning Telegram ID raqamini yuboring:",
        "admin_added": "✅ Admin qo‘shildi.",
        "admin_removed": "✅ Admin o‘chirildi.",
        "admin_exists": "Bu ID adminlar ro‘yxatida allaqachon bor.",
        "admin_missing": "Bunday admin topilmadi.",
        "admin_list_title": "👥 Adminlar ro‘yxati:",
        "bad_id": "❗ Telegram ID faqat raqamlardan iborat bo‘lishi kerak.",
        "super_only": "⛔ Adminlarni faqat asosiy admin boshqaradi.",
        "reply_help": "Javob berish: /reply TELEGRAM_ID xabar",
        "reply_sent": "✅ Javob foydalanuvchiga yuborildi.",
        "reply_failed": "❌ Javob yuborilmadi.",
        "user_message": "📩 Foydalanuvchidan xabar\nID: {id}\nIsm: {name}\n\n{text}",
        "back": "🔙 Bosh menyu",
        "cancel": "❌ Bekor qilish",
        "admin_added_by": "Admin qo‘shildi: {id}",
        "top_line": "{n}. {title} — {count} marta",
    },
    "ru": {
        "welcome": "👋 Добро пожаловать в AutoCAD Projects Bot!\nВыберите язык:",
        "language_saved": "✅ Язык сохранён.",
        "menu": "🏗 Главное меню",
        "search": "🔎 Поиск проектов",
        "contact": "📞 Связаться с администратором",
        "top": "🔥 ТОП-10 проектов",
        "settings": "⚙️ Настройки",
        "choose_category": "📂 Выберите категорию или воспользуйтесь меню:",
        "choose_language": "🌐 Выберите язык:",
        "search_prompt": "🔎 Введите название проекта для поиска:",
        "searching": "Идёт поиск...",
        "not_found": "😕 Проекты не найдены.",
        "results": "🔎 Результаты поиска:",
        "top_empty": "Пока нет скачанных проектов.",
        "top_title": "🔥 ТОП-10 СКАЧИВАЕМЫХ ПРОЕКТОВ",
        "downloads": "Скачиваний",
        "contact_prompt": "✍️ Напишите сообщение администратору:",
        "contact_sent": "✅ Сообщение отправлено администратору.",
        "contact_failed": "❌ Не удалось отправить сообщение. Попробуйте позже.",
        "cancelled": "❌ Действие отменено.",
        "admin_menu": "⚙️ Панель администратора",
        "add_project": "➕ Добавить проект",
        "projects": "📁 Проекты",
        "admins": "👥 Администраторы",
        "admin_add": "➕ Добавить администратора",
        "admin_remove": "➖ Удалить администратора",
        "admin_list": "📋 Список администраторов",
        "enter_title": "📝 Введите название проекта:",
        "enter_category": "📂 Выберите категорию:",
        "enter_description": "📄 Напишите описание или нажмите «Пропустить»:",
        "skip": "⏭ Пропустить",
        "send_file": "📎 Отправьте файл проекта как документ:",
        "saved": "✅ Проект сохранён в канале и базе данных!",
        "save_error": "❌ Ошибка сохранения. Проверьте Render Logs.",
        "invalid_category": "❗ Выберите категорию из списка.",
        "invalid_file": "❗ Отправьте файл как Telegram Document.",
        "no_projects": "Пока проектов нет.",
        "admin_only": "⛔ Этот раздел доступен только администраторам.",
        "enter_admin_id": "Отправьте Telegram ID нового администратора:",
        "enter_remove_id": "Отправьте Telegram ID администратора для удаления:",
        "admin_added": "✅ Администратор добавлен.",
        "admin_removed": "✅ Администратор удалён.",
        "admin_exists": "Этот ID уже есть в списке администраторов.",
        "admin_missing": "Администратор не найден.",
        "admin_list_title": "👥 Список администраторов:",
        "bad_id": "❗ Telegram ID должен содержать только цифры.",
        "super_only": "⛔ Управлять администраторами может только главный администратор.",
        "reply_help": "Ответ: /reply TELEGRAM_ID текст",
        "reply_sent": "✅ Ответ отправлен пользователю.",
        "reply_failed": "❌ Не удалось отправить ответ.",
        "user_message": "📩 Сообщение от пользователя\nID: {id}\nИмя: {name}\n\n{text}",
        "back": "🔙 Главное меню",
        "cancel": "❌ Отмена",
        "admin_added_by": "Добавлен администратор: {id}",
        "top_line": "{n}. {title} — {count} раз",
    },
    "en": {
        "welcome": "👋 Welcome to AutoCAD Projects Bot!\nChoose your language:",
        "language_saved": "✅ Language saved.",
        "menu": "🏗 Main menu",
        "search": "🔎 Search projects",
        "contact": "📞 Contact admin",
        "top": "🔥 Top 10 projects",
        "settings": "⚙️ Settings",
        "choose_category": "📂 Choose a category or use the menu:",
        "choose_language": "🌐 Choose your language:",
        "search_prompt": "🔎 Enter a project name to search:",
        "searching": "Searching...",
        "not_found": "😕 No projects found.",
        "results": "🔎 Search results:",
        "top_empty": "No projects have been downloaded yet.",
        "top_title": "🔥 TOP 10 MOST DOWNLOADED PROJECTS",
        "downloads": "Downloads",
        "contact_prompt": "✍️ Write your message to the administrator:",
        "contact_sent": "✅ Your message has been sent to the administrator.",
        "contact_failed": "❌ Message could not be sent. Please try again later.",
        "cancelled": "❌ Action cancelled.",
        "admin_menu": "⚙️ Admin panel",
        "add_project": "➕ Add project",
        "projects": "📁 Projects",
        "admins": "👥 Admins",
        "admin_add": "➕ Add admin",
        "admin_remove": "➖ Remove admin",
        "admin_list": "📋 Admin list",
        "enter_title": "📝 Enter the project title:",
        "enter_category": "📂 Choose a category:",
        "enter_description": "📄 Enter a description or press Skip:",
        "skip": "⏭ Skip",
        "send_file": "📎 Send the project file as a document:",
        "saved": "✅ Project saved to the channel and database!",
        "save_error": "❌ Save failed. Check Render Logs.",
        "invalid_category": "❗ Choose a category from the list.",
        "invalid_file": "❗ Send the file as a Telegram Document.",
        "no_projects": "There are no projects yet.",
        "admin_only": "⛔ This section is for administrators only.",
        "enter_admin_id": "Send the Telegram ID of the new administrator:",
        "enter_remove_id": "Send the Telegram ID of the administrator to remove:",
        "admin_added": "✅ Administrator added.",
        "admin_removed": "✅ Administrator removed.",
        "admin_exists": "This ID is already an administrator.",
        "admin_missing": "Administrator not found.",
        "admin_list_title": "👥 Administrators:",
        "bad_id": "❗ Telegram ID must contain digits only.",
        "super_only": "⛔ Only the main administrator can manage admins.",
        "reply_help": "Reply format: /reply TELEGRAM_ID message",
        "reply_sent": "✅ Reply sent to the user.",
        "reply_failed": "❌ Could not send the reply.",
        "user_message": "📩 Message from user\nID: {id}\nName: {name}\n\n{text}",
        "back": "🔙 Main menu",
        "cancel": "❌ Cancel",
        "admin_added_by": "Administrator added: {id}",
        "top_line": "{n}. {title} — {count} downloads",
    },
    "tg": {
        "welcome": "👋 Ба AutoCAD Projects Bot хуш омадед!\nЗабонро интихоб кунед:",
        "language_saved": "✅ Забон нигоҳ дошта шуд.",
        "menu": "🏗 Менюи асосӣ",
        "search": "🔎 Ҷустуҷӯи лоиҳа",
        "contact": "📞 Тамос бо маъмур",
        "top": "🔥 ТОП-10 лоиҳа",
        "settings": "⚙️ Танзимот",
        "choose_category": "📂 Категорияро интихоб кунед ё аз меню истифода баред:",
        "choose_language": "🌐 Забонро интихоб кунед:",
        "search_prompt": "🔎 Номи лоиҳаро барои ҷустуҷӯ нависед:",
        "searching": "Ҷустуҷӯ рафта истодааст...",
        "not_found": "😕 Лоиҳа ёфт нашуд.",
        "results": "🔎 Натиҷаи ҷустуҷӯ:",
        "top_empty": "Ҳоло лоиҳаҳои боргиришуда нестанд.",
        "top_title": "🔥 10 ЛОИҲАИ МАШҲУР",
        "downloads": "Боргирӣ",
        "contact_prompt": "✍️ Паёми худро ба маъмур нависед:",
        "contact_sent": "✅ Паём ба маъмур фиристода шуд.",
        "contact_failed": "❌ Паём фиристода нашуд. Баъдтар кӯшиш кунед.",
        "cancelled": "❌ Амал бекор карда шуд.",
        "admin_menu": "⚙️ Панели маъмур",
        "add_project": "➕ Иловаи лоиҳа",
        "projects": "📁 Лоиҳаҳо",
        "admins": "👥 Маъмурон",
        "admin_add": "➕ Иловаи маъмур",
        "admin_remove": "➖ Нест кардани маъмур",
        "admin_list": "📋 Рӯйхати маъмурон",
        "enter_title": "📝 Номи лоиҳаро ворид кунед:",
        "enter_category": "📂 Категорияро интихоб кунед:",
        "enter_description": "📄 Тавсифро нависед ё «Гузаронидан»-ро пахш кунед:",
        "skip": "⏭ Гузаронидан",
        "send_file": "📎 Файли лоиҳаро ҳамчун ҳуҷҷат фиристед:",
        "saved": "✅ Лоиҳа ба канал ва пойгоҳи додаҳо сабт шуд!",
        "save_error": "❌ Хатои сабт. Render Logs-ро санҷед.",
        "invalid_category": "❗ Аз рӯйхат категорияро интихоб кунед.",
        "invalid_file": "❗ Файлро ҳамчун Telegram Document фиристед.",
        "no_projects": "Ҳоло лоиҳа нест.",
        "admin_only": "⛔ Ин бахш танҳо барои маъмурон аст.",
        "enter_admin_id": "Telegram ID-и маъмури навро фиристед:",
        "enter_remove_id": "Telegram ID-и маъмуреро, ки нест мешавад, фиристед:",
        "admin_added": "✅ Маъмур илова шуд.",
        "admin_removed": "✅ Маъмур нест карда шуд.",
        "admin_exists": "Ин ID аллакай маъмур аст.",
        "admin_missing": "Маъмур ёфт нашуд.",
        "admin_list_title": "👥 Рӯйхати маъмурон:",
        "bad_id": "❗ Telegram ID бояд танҳо рақам бошад.",
        "super_only": "⛔ Танҳо маъмури асосӣ метавонад маъмуронро идора кунад.",
        "reply_help": "Ҷавоб: /reply TELEGRAM_ID матн",
        "reply_sent": "✅ Ҷавоб ба корбар фиристода шуд.",
        "reply_failed": "❌ Ҷавоб фиристода нашуд.",
        "user_message": "📩 Паём аз корбар\nID: {id}\nНом: {name}\n\n{text}",
        "back": "🔙 Менюи асосӣ",
        "cancel": "❌ Бекор кардан",
        "admin_added_by": "Маъмур илова шуд: {id}",
        "top_line": "{n}. {title} — {count} бор",
        "language_saved": "✅ Забон нигоҳ дошта шуд.",
    },
}

CATEGORIES = ['🏠 Uy', '🏢 Ofis', '🛋 Interyer dizayn', '🏫 Maktab va bog‘cha', '🛍 Savdo markazi', '🛣 Yo‘l va ko‘prik', '🏗 Boshqa binolar', '☕ Kichik kafelar', '🚏 Aqlli bekatlar', '🚗 Avtomobillar', '⚡ Elektr chizmalari', '🧱 Konstruksiya va fundament', '🪑 Mebel chizmalari', '🌳 Landshaft dizayn', '📐 Tayyor shablonlar', '🎨 Hatch va teksturalar', '🚜 Ferma va chorvachilik loyihalari']

CATEGORY_TRANSLATIONS = {'uz': ['🏠 Uy', '🏢 Ofis', '🛋 Interyer dizayn', '🏫 Maktab va bog‘cha', '🛍 Savdo markazi', '🛣 Yo‘l va ko‘prik', '🏗 Boshqa binolar', '☕ Kichik kafelar', '🚏 Aqlli bekatlar', '🚗 Avtomobillar', '⚡ Elektr chizmalari', '🧱 Konstruksiya va fundament', '🪑 Mebel chizmalari', '🌳 Landshaft dizayn', '📐 Tayyor shablonlar', '🎨 Hatch va teksturalar', '🚜 Ferma va chorvachilik loyihalari'], 'ru': ['🏠 Дом', '🏢 Офис', '🛋 Дизайн интерьера', '🏫 Школа и детский сад', '🛍 Торговый центр', '🛣 Дороги и мосты', '🏗 Другие здания', '☕ Небольшие кафе', '🚏 Умные остановки', '🚗 Автомобили', '⚡ Электрические схемы', '🧱 Конструкции и фундамент', '🪑 Чертежи мебели', '🌳 Ландшафтный дизайн', '📐 Готовые шаблоны', '🎨 Штриховки и текстуры', '🚜 Фермы и животноводство'], 'en': ['🏠 House', '🏢 Office', '🛋 Interior design', '🏫 School and kindergarten', '🛍 Shopping mall', '🛣 Roads and bridges', '🏗 Other buildings', '☕ Small cafes', '🚏 Smart bus stops', '🚗 Vehicles', '⚡ Electrical drawings', '🧱 Structures and foundations', '🪑 Furniture drawings', '🌳 Landscape design', '📐 Ready templates', '🎨 Hatches and textures', '🚜 Farm and livestock projects'], 'tg': ['🏠 Хона', '🏢 Идора', '🛋 Тарҳи дохилӣ', '🏫 Мактаб ва кӯдакистон', '🛍 Маркази савдо', '🛣 Роҳ ва пул', '🏗 Биноҳои дигар', '☕ Қаҳвахонаҳои хурд', '🚏 Истгоҳҳои ҳушманд', '🚗 Автомобилҳо', '⚡ Нақшаҳои барқӣ', '🧱 Сохтор ва таҳкурсӣ', '🪑 Нақшаҳои мебел', '🌳 Тарҳи ландшафт', '📐 Шаблонҳои тайёр', '🎨 Ҳач ва текстураҳо', '🚜 Лоиҳаҳои ферма ва чорводорӣ']}

CATEGORY_TO_CANONICAL = {
    CATEGORY_TRANSLATIONS[lang][i]: CATEGORIES[i]
    for lang in LANGUAGES for i in range(len(CATEGORIES))
}





# =========================================================
# FSM
# =========================================================
class AddProject(StatesGroup):
    title = State()
    category = State()
    description = State()
    file = State()


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
def db_execute(query):
    return query.execute()


async def db(query):
    return await asyncio.to_thread(db_execute, query)


async def get_language(user_id: int) -> str:
    try:
        result = await db(
            supabase.table("bot_users")
            .select("language")
            .eq("telegram_id", user_id)
            .limit(1)
        )
        if result.data:
            lang = result.data[0].get("language", "uz")
            return lang if lang in LANGUAGES else "uz"
    except Exception:
        logger.exception("Tilni olishda xato")
    return "uz"


async def save_user(user_id: int, lang: str):
    try:
        await db(
            supabase.table("bot_users").upsert({
                "telegram_id": user_id,
                "language": lang,
            }, on_conflict="telegram_id")
        )
    except Exception:
        logger.exception("Foydalanuvchini saqlashda xato")


async def is_admin(user_id: int) -> bool:
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
        logger.exception("Admin tekshiruvida xato")
        return False


async def t(user_id: int, key: str, **kwargs) -> str:
    lang = await get_language(user_id)
    value = T[lang].get(key, T["uz"].get(key, key))
    return value.format(**kwargs)


# =========================================================
# INLINE KEYBOARDS
# =========================================================
def language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name, callback_data=f"lang:{code}")]
        for code, name in LANGUAGES.items()
    ])


def main_keyboard(lang: str, admin: bool = False):
    rows = [
        [InlineKeyboardButton(text=T[lang]["search"], callback_data="menu:search"),
         InlineKeyboardButton(text=T[lang]["top"], callback_data="menu:top")],
        [InlineKeyboardButton(text=T[lang]["contact"], callback_data="menu:contact"),
         InlineKeyboardButton(text=T[lang]["settings"], callback_data="menu:settings")],
    ]
    if admin:
        rows += [
            [InlineKeyboardButton(text=T[lang]["add_project"], callback_data="menu:add"),
             InlineKeyboardButton(text=T[lang]["projects"], callback_data="menu:projects")],
            [InlineKeyboardButton(text=T[lang]["admins"], callback_data="menu:admins")],
        ]
    names = CATEGORY_TRANSLATIONS[lang]
    for i in range(0, len(names), 2):
        row = [InlineKeyboardButton(text=names[i], callback_data=f"cat:{i}")]
        if i + 1 < len(names):
            row.append(InlineKeyboardButton(text=names[i + 1], callback_data=f"cat:{i+1}"))
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def category_keyboard(lang: str):
    names = CATEGORY_TRANSLATIONS[lang]
    rows = []
    for i in range(0, len(names), 2):
        row = [InlineKeyboardButton(text=names[i], callback_data=f"addcat:{i}")]
        if i + 1 < len(names):
            row.append(InlineKeyboardButton(text=names[i + 1], callback_data=f"addcat:{i+1}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(text=T[lang]["cancel"], callback_data="flow:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_manage_keyboard(lang: str):
    """Admin tugmalari chat pastida doimiy ReplyKeyboard bo'lib turadi."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=T[lang]["admin_add"])],
            [KeyboardButton(text=T[lang]["admin_remove"])],
            [KeyboardButton(text=T[lang]["admin_list"])],
            [KeyboardButton(text=T[lang]["back"])],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Admin boshqaruvi",
    )


def flow_keyboard(lang: str, skip: bool = False):
    rows = []
    if skip:
        rows.append([InlineKeyboardButton(text=T[lang]["skip"], callback_data="flow:skip")])
    rows.append([InlineKeyboardButton(text=T[lang]["cancel"], callback_data="flow:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def show_main(message: Message):
    lang = await get_language(message.from_user.id)
    admin = await is_admin(message.from_user.id)
    await message.answer(
        T[lang]["admin_menu"] if admin else T[lang]["choose_category"],
        reply_markup=main_keyboard(lang, admin)
    )


# =========================================================
# START AND LANGUAGE
# =========================================================
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await save_user(message.from_user.id, await get_language(message.from_user.id))
    lang = await get_language(message.from_user.id)
    await message.answer(T[lang]["welcome"], reply_markup=language_keyboard())


@dp.callback_query(F.data.startswith("lang:"))
async def choose_language(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split(":", 1)[1]
    if lang not in LANGUAGES:
        await callback.answer("Til topilmadi", show_alert=True)
        return
    await save_user(callback.from_user.id, lang)
    await state.clear()
    admin = await is_admin(callback.from_user.id)
    await callback.answer(T[lang]["language_saved"])
    try:
        await callback.message.edit_text(
            T[lang]["language_saved"] + "\n\n" +
            (T[lang]["admin_menu"] if admin else T[lang]["choose_category"]),
            reply_markup=main_keyboard(lang, admin)
        )
    except Exception:
        await callback.message.answer(
            T[lang]["language_saved"] + "\n\n" +
            (T[lang]["admin_menu"] if admin else T[lang]["choose_category"]),
            reply_markup=main_keyboard(lang, admin)
        )


@dp.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext):
    await state.clear()
    lang = await get_language(message.from_user.id)
    await message.answer(
        T[lang]["cancelled"],
        reply_markup=main_keyboard(lang, await is_admin(message.from_user.id))
    )


@dp.callback_query(F.data.startswith("menu:"))
async def inline_menu_router(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await get_language(user_id)
    action = callback.data.split(":", 1)[1]
    await callback.answer()

    if action == "back":
        await state.clear()
        admin = await is_admin(user_id)
        await callback.message.edit_text(
            T[lang]["admin_menu"] if admin else T[lang]["choose_category"],
            reply_markup=main_keyboard(lang, admin)
        )
    elif action == "settings":
        await callback.message.edit_text(T[lang]["choose_language"], reply_markup=language_keyboard())
    elif action == "search":
        await state.set_state(SearchProject.query)
        await callback.message.edit_text(T[lang]["search_prompt"], reply_markup=flow_keyboard(lang))
    elif action == "contact":
        await state.set_state(ContactAdmin.message)
        await callback.message.edit_text(T[lang]["contact_prompt"], reply_markup=flow_keyboard(lang))
    elif action == "top":
        await show_top(callback.message, lang)
    elif action == "add" and await is_admin(user_id):
        await state.set_state(AddProject.title)
        await callback.message.edit_text(T[lang]["enter_title"], reply_markup=flow_keyboard(lang))
    elif action == "projects" and await is_admin(user_id):
        await show_projects(callback.message, lang)
    elif action == "admins" and await is_admin(user_id):
        if user_id != SUPER_ADMIN_ID:
            await callback.message.answer(T[lang]["super_only"])
        else:
            await callback.message.answer(
                T[lang]["admins"],
                reply_markup=admin_manage_keyboard(lang)
            )


@dp.callback_query(F.data.startswith("cat:"))
async def choose_project_category(callback: CallbackQuery):
    lang = await get_language(callback.from_user.id)
    try:
        index = int(callback.data.split(":", 1)[1])
        category = CATEGORY_TRANSLATIONS[lang][index]
        canonical = CATEGORY_TO_CANONICAL[category]
    except (ValueError, IndexError, KeyError):
        await callback.answer("Kategoriya topilmadi", show_alert=True)
        return
    await callback.answer()
    await send_category_projects(callback.message, canonical, lang)


@dp.message(F.text.in_([T[code][key] for code in T for key in ("admin_add", "admin_remove", "admin_list", "back")]))
async def admin_menu_router(message: Message, state: FSMContext):
    lang = await get_language(message.from_user.id)
    if message.from_user.id != SUPER_ADMIN_ID:
        return

    action_by_text = {
        T[code]["admin_add"]: "add" for code in T
    }
    action_by_text.update({T[code]["admin_remove"]: "remove" for code in T})
    action_by_text.update({T[code]["admin_list"]: "list" for code in T})
    action_by_text.update({T[code]["back"]: "back" for code in T})
    action = action_by_text.get((message.text or "").strip())

    if action == "add":
        await state.set_state(AdminManage.add_id)
        await message.answer(T[lang]["enter_admin_id"], reply_markup=flow_keyboard(lang))
    elif action == "remove":
        await state.set_state(AdminManage.remove_id)
        await message.answer(T[lang]["enter_remove_id"], reply_markup=flow_keyboard(lang))
    elif action == "list":
        await show_admins(message, lang)
    elif action == "back":
        await state.clear()
        await message.answer(
            T[lang]["admin_menu"],
            reply_markup=main_keyboard(lang, await is_admin(message.from_user.id))
        )


@dp.callback_query(F.data == "flow:cancel")
async def cancel_inline_flow(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    lang = await get_language(callback.from_user.id)
    admin = await is_admin(callback.from_user.id)
    await callback.answer(T[lang]["cancelled"])
    await callback.message.edit_text(
        T[lang]["admin_menu"] if admin else T[lang]["choose_category"],
        reply_markup=main_keyboard(lang, admin)
    )


@dp.callback_query(F.data == "flow:skip", AddProject.description)
async def skip_project_description(callback: CallbackQuery, state: FSMContext):
    lang = await get_language(callback.from_user.id)
    await state.update_data(description="")
    await state.set_state(AddProject.file)
    await callback.answer()
    await callback.message.edit_text(T[lang]["send_file"], reply_markup=flow_keyboard(lang))


# =========================================================
# PROJECT UPLOAD FLOW (ADMIN)
# =========================================================
@dp.message(AddProject.title)
async def add_title(message: Message, state: FSMContext):
    lang = await get_language(message.from_user.id)
    if not message.text or len(message.text.strip()) > 200:
        await message.answer(T[lang]["enter_title"], reply_markup=flow_keyboard(lang))
        return
    await state.update_data(title=message.text.strip())
    await state.set_state(AddProject.category)
    await message.answer(T[lang]["enter_category"], reply_markup=category_keyboard(lang))


@dp.callback_query(F.data.startswith("addcat:"), AddProject.category)
async def add_category(callback: CallbackQuery, state: FSMContext):
    lang = await get_language(callback.from_user.id)
    try:
        index = int(callback.data.split(":", 1)[1])
        selected = CATEGORY_TRANSLATIONS[lang][index]
        canonical = CATEGORY_TO_CANONICAL[selected]
    except (ValueError, IndexError, KeyError):
        await callback.answer(T[lang]["invalid_category"], show_alert=True)
        return
    await state.update_data(category=canonical)
    await state.set_state(AddProject.description)
    await callback.answer()
    await callback.message.edit_text(
        T[lang]["enter_description"],
        reply_markup=flow_keyboard(lang, skip=True)
    )


@dp.message(AddProject.description, F.text)
async def add_description(message: Message, state: FSMContext):
    lang = await get_language(message.from_user.id)
    description = "" if message.text == T[lang]["skip"] else message.text.strip()
    if description == T[lang]["cancel"]:
        await state.clear()
        await show_main(message)
        return
    await state.update_data(description=description[:3000])
    await state.set_state(AddProject.file)
    await message.answer(T[lang]["send_file"], reply_markup=flow_keyboard(lang))


@dp.message(AddProject.file, F.document)
async def save_project(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    lang = await get_language(message.from_user.id)
    data = await state.get_data()
    try:
        logger.info("1-QADAM: Telegram kanalga yuborish boshlandi")
        channel_message = await bot.send_document(
            chat_id=CHANNEL_ID,
            document=message.document.file_id,
            caption=(f"📁 {data['title']}\n📂 {data['category']}\n\n"
                     f"{data.get('description', '')}")[:1024]
        )
        channel_file_id = channel_message.document.file_id
        logger.info("2-QADAM: Fayl kanalga yuborildi")
        await db(
            supabase.table("projects").insert({
                "title": data["title"],
                "category": data["category"],
                "description": data.get("description", ""),
                "telegram_file_id": channel_file_id,
                "download_count": 0,
            })
        )
        logger.info("3-QADAM: Supabase saqlash muvaffaqiyatli")
        await message.answer(
            T[lang]["saved"],
            reply_markup=main_keyboard(lang, True)
        )
        await state.clear()
    except Exception:
        logger.exception("Loyihani saqlashda xato")
        await message.answer(T[lang]["save_error"])


@dp.message(AddProject.file)
async def invalid_project_file(message: Message):
    lang = await get_language(message.from_user.id)
    await message.answer(T[lang]["invalid_file"])


# =========================================================
# DOWNLOAD AND SEARCH HELPERS
# =========================================================
async def increment_download(project_id: int):
    try:
        result = await db(
            supabase.table("projects")
            .select("download_count")
            .eq("id", project_id)
            .limit(1)
        )
        current = 0
        if result.data:
            current = int(result.data[0].get("download_count") or 0)
        await db(
            supabase.table("projects")
            .update({"download_count": current + 1})
            .eq("id", project_id)
        )
    except Exception:
        logger.exception("Yuklab olish sonini oshirishda xato")


async def send_project(message: Message, project: dict, lang: str):
    caption = (
        f"📁 {project.get('title', '')}\n"
        f"📂 {project.get('category', '')}\n\n"
        f"{project.get('description') or ''}"
    )[:1024]
    await bot.send_document(
        chat_id=message.chat.id,
        document=project["telegram_file_id"],
        caption=caption
    )
    await increment_download(project["id"])


async def send_category_projects(message: Message, category: str, lang: str):
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
            await message.answer(T[lang]["no_projects"])
            return
        for project in projects:
            await send_project(message, project, lang)
    except Exception:
        logger.exception("Kategoriya loyihalarini yuborishda xato")
        await message.answer("❌ Xatolik yuz berdi. Please try again.")


@dp.message(SearchProject.query)
async def search_projects(message: Message, state: FSMContext):
    lang = await get_language(message.from_user.id)
    if not message.text:
        await message.answer(T[lang]["search_prompt"])
        return
    query_text = message.text.strip()
    if query_text == T[lang]["cancel"]:
        await state.clear()
        await show_main(message)
        return
    try:
        await message.answer(T[lang]["searching"])
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
            await message.answer(T[lang]["not_found"])
            return
        await message.answer(T[lang]["results"])
        for project in projects:
            await send_project(message, project, lang)
    except Exception:
        logger.exception("Loyiha qidirishda xato")
        await state.clear()
        await message.answer("❌ Search error. Please try again.")


async def show_top(message: Message, lang: str):
    try:
        result = await db(
            supabase.table("projects")
            .select("id,title,category,telegram_file_id,description,download_count")
            .order("download_count", desc=True)
            .order("id", desc=True)
            .limit(10)
        )
        projects = result.data or []
        if not projects:
            await message.answer(T[lang]["top_empty"])
            return
        lines = [T[lang]["top_title"], ""]
        for index, project in enumerate(projects, 1):
            lines.append(T[lang]["top_line"].format(
                n=index,
                title=project["title"],
                count=project.get("download_count") or 0
            ))
        await message.answer("\n".join(lines))
        for project in projects:
            await message.answer_document(
                document=project["telegram_file_id"],
                caption=f"📁 {project['title']}"
            )
            await increment_download(project["id"])
    except Exception:
        logger.exception("TOP-10 chiqarishda xato")
        await message.answer("❌ Error loading top projects.")


# =========================================================
# CONTACT
# =========================================================
@dp.message(ContactAdmin.message)
async def contact_admin(message: Message, state: FSMContext):
    lang = await get_language(message.from_user.id)
    if not message.text:
        await message.answer(T[lang]["contact_prompt"])
        return
    if message.text == T[lang]["cancel"]:
        await state.clear()
        await show_main(message)
        return
    user = message.from_user
    text = T["uz"]["user_message"].format(
        id=user.id,
        name=user.full_name,
        text=message.text
    )
    sent = False
    try:
        result = await db(supabase.table("bot_admins").select("telegram_id"))
        admin_ids = {int(row["telegram_id"]) for row in (result.data or [])}
        admin_ids.add(SUPER_ADMIN_ID)
        for admin_id in admin_ids:
            try:
                await bot.send_message(admin_id, text)
                sent = True
            except Exception:
                logger.warning("Admin %s ga xabar yuborilmadi", admin_id)
        await state.clear()
        await message.answer(
            T[lang]["contact_sent"] if sent else T[lang]["contact_failed"],
            reply_markup=main_keyboard(lang, await is_admin(user.id))
        )
    except Exception:
        logger.exception("Aloqa xabarini yuborishda xato")
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
    user_id = int(parts[1])
    try:
        await bot.send_message(user_id, "📨 Admin javobi:\n\n" + parts[2])
        await message.answer(T[lang]["reply_sent"])
    except Exception:
        logger.exception("Foydalanuvchiga javob yuborishda xato")
        await message.answer(T[lang]["reply_failed"])


# =========================================================
# ADMIN MANAGEMENT (SUPER ADMIN ONLY)
# =========================================================
@dp.message(AdminManage.add_id)
async def add_admin_id(message: Message, state: FSMContext):
    lang = await get_language(message.from_user.id)
    if message.from_user.id != SUPER_ADMIN_ID:
        await state.clear()
        await message.answer(T[lang]["super_only"])
        return
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer(T[lang]["bad_id"])
        return
    new_id = int(raw)
    if new_id == SUPER_ADMIN_ID:
        await message.answer(T[lang]["admin_exists"])
        return
    try:
        existing = await db(
            supabase.table("bot_admins").select("telegram_id").eq("telegram_id", new_id)
        )
        if existing.data:
            await message.answer(T[lang]["admin_exists"])
        else:
            await db(supabase.table("bot_admins").insert({"telegram_id": new_id}))
            await message.answer(T[lang]["admin_added"])
        await state.clear()
        await show_main(message)
    except Exception:
        logger.exception("Admin qo'shishda xato")
        await message.answer("❌ Admin qo‘shilmadi. Render Logs'ni tekshiring.")


@dp.message(AdminManage.remove_id)
async def remove_admin_id(message: Message, state: FSMContext):
    lang = await get_language(message.from_user.id)
    if message.from_user.id != SUPER_ADMIN_ID:
        await state.clear()
        await message.answer(T[lang]["super_only"])
        return
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer(T[lang]["bad_id"])
        return
    remove_id = int(raw)
    if remove_id == SUPER_ADMIN_ID:
        await message.answer(T[lang]["super_only"])
        return
    try:
        existing = await db(
            supabase.table("bot_admins").select("telegram_id").eq("telegram_id", remove_id)
        )
        if not existing.data:
            await message.answer(T[lang]["admin_missing"])
        else:
            await db(
                supabase.table("bot_admins")
                .delete()
                .eq("telegram_id", remove_id)
            )
            await message.answer(T[lang]["admin_removed"])
        await state.clear()
        await show_main(message)
    except Exception:
        logger.exception("Admin o'chirishda xato")
        await message.answer("❌ Admin o‘chirilmadi. Render Logs'ni tekshiring.")


async def show_admins(message: Message, lang: str):
    try:
        result = await db(
            supabase.table("bot_admins").select("telegram_id").order("telegram_id")
        )
        ids = sorted({SUPER_ADMIN_ID} | {
            int(row["telegram_id"]) for row in (result.data or [])
        })
        await message.answer(
            T[lang]["admin_list_title"] + "\n" +
            "\n".join(f"• {admin_id}" for admin_id in ids)
        )
    except Exception:
        logger.exception("Adminlar ro'yxatini olishda xato")
        await message.answer("❌ Adminlar ro‘yxatini olishda xato.")


async def show_projects(message: Message, lang: str):
    try:
        result = await db(
            supabase.table("projects")
            .select("id,title,category")
            .order("id", desc=True)
            .limit(30)
        )
        projects = result.data or []
        if not projects:
            await message.answer(T[lang]["no_projects"])
            return
        lines = ["📁 LOYIHALAR RO‘YXATI", ""]
        for p in projects:
            lines.append(f"ID: {p['id']} | {p['title']} | {p['category']}")
        await message.answer("\n".join(lines)[:4000])
    except Exception:
        logger.exception("Loyihalar ro'yxatini olishda xato")
        await message.answer("❌ Loyihalar ro‘yxatini olishda xato.")


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
        logger.exception("Webhook update xatosi")
        raise


async def on_startup(app: web.Application):
    await bot.set_webhook(
        url=f"{BASE_URL}{WEBHOOK_PATH}",
        secret_token=WEBHOOK_SECRET
    )
    logger.info("Webhook muvaffaqiyatli o'rnatildi!")


async def on_shutdown(app: web.Application):
    await bot.session.close()
    logger.info("Bot to'xtatildi")


app = web.Application()
app.router.add_get(
    "/",
    lambda request: web.Response(text="AutoCAD Projects Bot ishlayapti!")
)
app.router.add_post(WEBHOOK_PATH, handle_webhook)
app.on_startup.append(on_startup)
app.on_cleanup.append(on_shutdown)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    web.run_app(app, host="0.0.0.0", port=port)
