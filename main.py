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
    Message, Update, ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove
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
        "favorites": "⭐ Sevimlilar", "request": "📝 Loyiha so‘rash", "formats": "📄 Fayl formatlari",
        "edit_project": "✏️ Loyihani tahrirlash", "delete_project": "🗑 Loyihani o‘chirish",
        "enter_project_id": "Loyiha ID raqamini yuboring:",
        "enter_new_title": "Yangi loyiha nomini yuboring (o‘zgartirmaslik uchun - yozing):",
        "enter_new_description": "Yangi tavsifni yuboring (o‘zgartirmaslik uchun - yozing):",
        "confirm_delete": "Loyihani o‘chirishni tasdiqlaysizmi? HA yoki YO‘Q deb yozing.",
        "request_prompt": "Qanday loyiha kerakligini yozing:",
        "request_saved": "✅ So‘rovingiz adminga yuborildi.",
        "no_favorites": "Sevimli loyihalaringiz hozircha yo‘q.",
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
        "favorites": "⭐ Избранное", "request": "📝 Запросить проект", "formats": "📄 Форматы файлов",
        "edit_project": "✏️ Редактировать проект", "delete_project": "🗑 Удалить проект",
        "enter_project_id": "Отправьте ID проекта:",
        "enter_new_title": "Отправьте новое название (или - чтобы не менять):",
        "enter_new_description": "Отправьте новое описание (или - чтобы не менять):",
        "confirm_delete": "Подтвердить удаление? Напишите ДА или НЕТ.",
        "request_prompt": "Опишите, какой проект вам нужен:",
        "request_saved": "✅ Ваш запрос отправлен администратору.",
        "no_favorites": "В избранном пока нет проектов.",
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
        "favorites": "⭐ Favorites", "request": "📝 Request a project", "formats": "📄 File formats",
        "edit_project": "✏️ Edit project", "delete_project": "🗑 Delete project",
        "enter_project_id": "Send the project ID:",
        "enter_new_title": "Send a new title (or - to keep it):",
        "enter_new_description": "Send a new description (or - to keep it):",
        "confirm_delete": "Confirm deletion? Type YES or NO.",
        "request_prompt": "Describe the project you need:",
        "request_saved": "✅ Your request was sent to the administrator.",
        "no_favorites": "You have no favorite projects yet.",
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
        "favorites": "⭐ Дӯстдоштаҳо", "request": "📝 Дархости лоиҳа", "formats": "📄 Форматҳои файл",
        "edit_project": "✏️ Таҳрири лоиҳа", "delete_project": "🗑 Нест кардани лоиҳа",
        "enter_project_id": "ID-и лоиҳаро фиристед:",
        "enter_new_title": "Номи навро фиристед (ё - барои нигоҳ доштан):",
        "enter_new_description": "Тавсифи навро фиристед (ё - барои нигоҳ доштан):",
        "confirm_delete": "Нест карданро тасдиқ мекунед? ҲА ё НЕ нависед.",
        "request_prompt": "Лоиҳаи лозимаро тавсиф кунед:",
        "request_saved": "✅ Дархости шумо ба маъмур фиристода шуд.",
        "no_favorites": "Ҳоло лоиҳаи дӯстдошта нест.",
        "language_saved": "✅ Забон нигоҳ дошта шуд.",
    },
}

CATEGORIES = [
    "🏠 Uy", "🏢 Ofis", "🏭 Zavod", "🛋 Interyer dizayn",
    "🏫 Maktab va bog‘cha", "🛍 Savdo markazi", "🛣 Yo‘l va ko‘prik",
    "🏗 Boshqa binolar", "☕ Kichik kafelar", "🚏 Aqlli bekatlar",
    "🚗 Avtomobillar", "📦 Buyumlar", "⚡ Elektr chizmalari",
    "🚰 Suv va kanalizatsiya", "🧱 Konstruksiya va fundament",
    "🪑 Mebel chizmalari", "🌳 Landshaft dizayn", "🧩 Tayyor DWG bloklar",
    "📐 Tayyor shablonlar", "🎨 Hatch va teksturalar", "📏 Tayyor detallar",
    "🔤 Shriftlar va chiziq turlari", "🚜 Ferma va chorvachilik loyihalari",
]
CATEGORY_TRANSLATIONS = {
    "uz": CATEGORIES,
    "ru": [
        "🏠 Дом", "🏢 Офис", "🏭 Завод", "🛋 Дизайн интерьера",
        "🏫 Школа и детский сад", "🛍 Торговый центр", "🛣 Дороги и мосты",
        "🏗 Другие здания", "☕ Небольшие кафе", "🚏 Умные остановки",
        "🚗 Автомобили", "📦 Предметы", "⚡ Электрические чертежи",
        "🚰 Водоснабжение и канализация", "🧱 Конструкции и фундамент",
        "🪑 Чертежи мебели", "🌳 Ландшафтный дизайн", "🧩 Готовые DWG-блоки",
        "📐 Готовые шаблоны", "🎨 Штриховки и текстуры", "📏 Готовые детали",
        "🔤 Шрифты и типы линий", "🚜 Фермы и животноводство",
    ],
    "en": [
        "🏠 House", "🏢 Office", "🏭 Factory", "🛋 Interior design",
        "🏫 School and kindergarten", "🛍 Shopping mall", "🛣 Roads and bridges",
        "🏗 Other buildings", "☕ Small cafes", "🚏 Smart bus stops",
        "🚗 Vehicles", "📦 Objects", "⚡ Electrical drawings",
        "🚰 Water and sewerage", "🧱 Structures and foundations",
        "🪑 Furniture drawings", "🌳 Landscape design", "🧩 Ready DWG blocks",
        "📐 Ready templates", "🎨 Hatches and textures", "📏 Ready details",
        "🔤 Fonts and linetypes", "🚜 Farms and livestock projects",
    ],
    "tg": [
        "🏠 Хона", "🏢 Идора", "🏭 Завод", "🛋 Тарҳи дохилӣ",
        "🏫 Мактаб ва кӯдакистон", "🛍 Маркази савдо", "🛣 Роҳ ва пул",
        "🏗 Биноҳои дигар", "☕ Қаҳвахонаҳои хурд", "🚏 Истгоҳҳои оқил",
        "🚗 Автомобилҳо", "📦 Ашё", "⚡ Нақшаҳои барқӣ",
        "🚰 Обтаъминкунӣ ва канализатсия", "🧱 Сохтмон ва таҳкурсӣ",
        "🪑 Нақшаҳои мебел", "🌳 Тарҳи ландшафт", "🧩 Блокҳои тайёри DWG",
        "📐 Шаблонҳои тайёр", "🎨 Ҳетч ва текстураҳо", "📏 Ҷузъиёти тайёр",
        "🔤 Ҳарфҳо ва намудҳои хат", "🚜 Ферма ва чорводорӣ",
    ],
}
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


class ProjectAdmin(StatesGroup):
    edit_id = State()
    edit_title = State()
    edit_category = State()
    edit_description = State()
    delete_id = State()
    delete_confirm = State()


class UserRequest(StatesGroup):
    text = State()


class FormatFilter(StatesGroup):
    value = State()


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
# KEYBOARDS
# =========================================================
def language_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=name)] for name in LANGUAGES.values()],
        resize_keyboard=True
    )


def main_keyboard(lang: str, admin: bool = False):
    rows = [
        [KeyboardButton(text=T[lang]["search"]),
         KeyboardButton(text=T[lang]["top"])],
        [KeyboardButton(text=T[lang]["contact"]),
         KeyboardButton(text=T[lang]["settings"])],
        [KeyboardButton(text=T[lang]["favorites"]),
         KeyboardButton(text=T[lang]["request"])],
        [KeyboardButton(text=T[lang]["formats"])],
    ]
    if admin:
        rows += [
            [KeyboardButton(text=T[lang]["add_project"]),
             KeyboardButton(text=T[lang]["projects"])],
            [KeyboardButton(text=T[lang]["edit_project"]),
             KeyboardButton(text=T[lang]["delete_project"])],
            [KeyboardButton(text=T[lang]["admins"])],
        ]
    rows.append([KeyboardButton(text=T[lang]["back"])])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def category_keyboard(lang: str):
    names = CATEGORY_TRANSLATIONS[lang]
    rows = []
    for i in range(0, len(names), 2):
        row = [KeyboardButton(text=names[i])]
        if i + 1 < len(names):
            row.append(KeyboardButton(text=names[i + 1]))
        rows.append(row)
    rows.append([KeyboardButton(text=T[lang]["back"])])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def admin_manage_keyboard(lang: str):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=T[lang]["admin_add"])],
            [KeyboardButton(text=T[lang]["admin_remove"])],
            [KeyboardButton(text=T[lang]["admin_list"])],
            [KeyboardButton(text=T[lang]["back"])],
        ],
        resize_keyboard=True
    )


def skip_keyboard(lang: str):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=T[lang]["skip"])],
            [KeyboardButton(text=T[lang]["cancel"])],
        ],
        resize_keyboard=True
    )


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


@dp.message(F.text.in_(list(LANGUAGES.values())))
async def choose_language(message: Message, state: FSMContext):
    lang = next(code for code, name in LANGUAGES.items() if name == message.text)
    await save_user(message.from_user.id, lang)
    await state.clear()
    admin = await is_admin(message.from_user.id)
    await message.answer(
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


@dp.message(StateFilter(None), F.text)
async def general_menu_router(message: Message, state: FSMContext):
    # FSM ichidagi matnlarni tegishli handlerlar qabul qiladi.
    if await state.get_state():
        return
    user_id = message.from_user.id
    lang = await get_language(user_id)
    text = message.text

    if text == T[lang]["back"] or text == T[lang]["menu"]:
        await show_main(message)
        return

    if text == T[lang]["settings"]:
        await message.answer(T[lang]["choose_language"], reply_markup=language_keyboard())
        return

    if text == T[lang]["search"]:
        await state.set_state(SearchProject.query)
        await message.answer(T[lang]["search_prompt"])
        return

    if text == T[lang]["contact"]:
        await state.set_state(ContactAdmin.message)
        await message.answer(T[lang]["contact_prompt"])
        return

    if text == T[lang]["top"]:
        await show_top(message, lang)
        return

    if text == T[lang]["add_project"] and await is_admin(user_id):
        await state.set_state(AddProject.title)
        await message.answer(T[lang]["enter_title"])
        return

    if text == T[lang]["projects"] and await is_admin(user_id):
        await show_projects(message, lang)
        return

    if text == T[lang]["admins"] and await is_admin(user_id):
        if user_id != SUPER_ADMIN_ID:
            await message.answer(T[lang]["super_only"])
        else:
            await message.answer(T[lang]["admins"], reply_markup=admin_manage_keyboard(lang))
        return

    if text in [T[lang]["admin_add"], T[lang]["admin_remove"], T[lang]["admin_list"]]:
        if user_id != SUPER_ADMIN_ID:
            await message.answer(T[lang]["super_only"])
            return
        if text == T[lang]["admin_add"]:
            await state.set_state(AdminManage.add_id)
            await message.answer(T[lang]["enter_admin_id"])
        elif text == T[lang]["admin_remove"]:
            await state.set_state(AdminManage.remove_id)
            await message.answer(T[lang]["enter_remove_id"])
        else:
            await show_admins(message, lang)
        return

    if text == T[lang]["favorites"]:
        await show_favorites(message, lang)
        return

    if text == T[lang]["request"]:
        await state.set_state(UserRequest.text)
        await message.answer(T[lang]["request_prompt"])
        return

    if text == T[lang]["formats"]:
        await state.set_state(FormatFilter.value)
        await message.answer("📄 Formatni yozing: DWG, DXF, PDF yoki ZIP")
        return

    if text == T[lang]["edit_project"] and await is_admin(user_id):
        await state.set_state(ProjectAdmin.edit_id)
        await message.answer(T[lang]["enter_project_id"])
        return

    if text == T[lang]["delete_project"] and await is_admin(user_id):
        await state.set_state(ProjectAdmin.delete_id)
        await message.answer(T[lang]["enter_project_id"])
        return

    canonical = CATEGORY_TO_CANONICAL.get(text)
    if canonical:
        await send_category_projects(message, canonical, lang)
        return

    if await is_admin(user_id):
        await message.answer(T[lang]["admin_menu"], reply_markup=main_keyboard(lang, True))
    else:
        await message.answer(T[lang]["choose_category"], reply_markup=main_keyboard(lang))


# =========================================================
# PROJECT UPLOAD FLOW (ADMIN)
# =========================================================
@dp.message(AddProject.title)
async def add_title(message: Message, state: FSMContext):
    lang = await get_language(message.from_user.id)
    if not message.text or len(message.text.strip()) > 200:
        await message.answer(T[lang]["enter_title"])
        return
    await state.update_data(title=message.text.strip())
    await state.set_state(AddProject.category)
    await message.answer(T[lang]["enter_category"], reply_markup=category_keyboard(lang))


@dp.message(AddProject.category)
async def add_category(message: Message, state: FSMContext):
    lang = await get_language(message.from_user.id)
    canonical = CATEGORY_TO_CANONICAL.get(message.text or "")
    if not canonical:
        await message.answer(T[lang]["invalid_category"], reply_markup=category_keyboard(lang))
        return
    await state.update_data(category=canonical)
    await state.set_state(AddProject.description)
    await message.answer(T[lang]["enter_description"], reply_markup=skip_keyboard(lang))


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
    await message.answer(T[lang]["send_file"], reply_markup=ReplyKeyboardRemove())


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
                "file_format": (os.path.splitext(message.document.file_name or "")[1].lstrip(".").upper() or "UNKNOWN"),
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
            .order("id", desc=True)
            .limit(200)
        )
        needle = query_text.casefold()
        projects = [p for p in (result.data or []) if needle in (
            str(p.get("title", "")) + " " + str(p.get("category", "")) + " " +
            str(p.get("description", "")) + " " + str(p.get("file_format", ""))
        ).casefold()][:10]
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
        lines += ["", "Tahrirlash: admin menyusidagi ✏️ tugma", "O‘chirish: admin menyusidagi 🗑 tugma"]
        await message.answer("\n".join(lines)[:4000])
    except Exception:
        logger.exception("Loyihalar ro'yxatini olishda xato")
        await message.answer("❌ Loyihalar ro‘yxatini olishda xato.")


@dp.message(FormatFilter.value)
async def filter_projects_by_format(message: Message, state: FSMContext):
    lang = await get_language(message.from_user.id)
    value = (message.text or "").strip().upper().lstrip(".")
    if value in {"BEKOR", "CANCEL", "ОТМЕНА"}:
        await state.clear(); await show_main(message); return
    if value not in {"DWG", "DXF", "PDF", "ZIP"}:
        await message.answer("Faqat DWG, DXF, PDF yoki ZIP formatini yozing.")
        return
    try:
        result = await db(supabase.table("projects").select("*").eq("file_format", value).order("id", desc=True).limit(20))
        projects = result.data or []
        await state.clear()
        if not projects:
            await message.answer(f"{value} formatida loyiha topilmadi.")
            return
        await message.answer(f"📄 {value} formatidagi loyihalar: {len(projects)} ta")
        for project in projects:
            await send_project(message, project, lang)
    except Exception:
        logger.exception("Format bo'yicha filtrlashda xato")
        await state.clear()
        await message.answer("❌ Format bo‘yicha qidirishda xatolik.")


# =========================================================
# FAVORITES, RATINGS, USER REQUESTS, PROJECT EDIT/DELETE
# =========================================================
async def show_favorites(message: Message, lang: str):
    uid = message.from_user.id
    try:
        fav = await db(supabase.table("project_favorites").select("project_id").eq("telegram_id", uid))
        ids = [int(x["project_id"]) for x in (fav.data or [])]
        if not ids:
            await message.answer(T[lang]["no_favorites"])
            return
        for pid in ids[:30]:
            res = await db(supabase.table("projects").select("*").eq("id", pid).limit(1))
            if res.data:
                await send_project(message, res.data[0], lang)
    except Exception:
        logger.exception("Sevimlilarni ko'rsatishda xato")
        await message.answer("❌ Sevimlilarni olishda xatolik.")


@dp.message(Command("fav"))
async def favorite_command(message: Message):
    lang = await get_language(message.from_user.id)
    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Foydalanish: /fav LOYIHA_ID")
        return
    pid = int(parts[1])
    uid = message.from_user.id
    try:
        existing = await db(supabase.table("project_favorites").select("project_id").eq("telegram_id", uid).eq("project_id", pid))
        if existing.data:
            await db(supabase.table("project_favorites").delete().eq("telegram_id", uid).eq("project_id", pid))
            await message.answer("⭐ Sevimlilardan olib tashlandi.")
        else:
            await db(supabase.table("project_favorites").insert({"telegram_id": uid, "project_id": pid}))
            await message.answer("⭐ Sevimlilarga qo‘shildi.")
    except Exception:
        logger.exception("Sevimliga qo'shishda xato")
        await message.answer("❌ Amal bajarilmadi. Loyiha ID sini tekshiring.")


@dp.message(Command("rate"))
async def rate_command(message: Message):
    parts = (message.text or "").split()
    if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit() or not 1 <= int(parts[2]) <= 5:
        await message.answer("Foydalanish: /rate LOYIHA_ID 1-5\nMasalan: /rate 12 5")
        return
    try:
        await db(supabase.table("project_ratings").upsert({
            "telegram_id": message.from_user.id,
            "project_id": int(parts[1]),
            "rating": int(parts[2]),
        }, on_conflict="telegram_id,project_id"))
        await message.answer("⭐ Bahoyingiz saqlandi. Rahmat!")
    except Exception:
        logger.exception("Reyting saqlashda xato")
        await message.answer("❌ Baho saqlanmadi. Loyiha ID sini tekshiring.")


@dp.message(UserRequest.text)
async def save_user_request(message: Message, state: FSMContext):
    lang = await get_language(message.from_user.id)
    if not message.text or len(message.text.strip()) < 3:
        await message.answer(T[lang]["request_prompt"])
        return
    request_text = message.text.strip()
    try:
        await db(supabase.table("project_requests").insert({
            "telegram_id": message.from_user.id,
            "request_text": request_text[:3000],
            "status": "new",
        }))
        admins = await db(supabase.table("bot_admins").select("telegram_id"))
        admin_ids = {SUPER_ADMIN_ID} | {int(x["telegram_id"]) for x in (admins.data or [])}
        for aid in admin_ids:
            try:
                await bot.send_message(aid, f"📝 Yangi loyiha so‘rovi\nFoydalanuvchi: {message.from_user.id}\n\n{request_text[:3000]}")
            except Exception:
                logger.warning("So'rov admin %s ga yuborilmadi", aid)
        await state.clear()
        await message.answer(T[lang]["request_saved"], reply_markup=main_keyboard(lang, await is_admin(message.from_user.id)))
    except Exception:
        logger.exception("Loyiha so'rovini saqlashda xato")
        await message.answer("❌ So‘rov yuborilmadi. Qayta urinib ko‘ring.")


@dp.message(ProjectAdmin.edit_id)
async def project_edit_get_id(message: Message, state: FSMContext):
    lang = await get_language(message.from_user.id)
    if not await is_admin(message.from_user.id):
        await state.clear(); await message.answer(T[lang]["admin_only"]); return
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer(T[lang]["enter_project_id"]); return
    res = await db(supabase.table("projects").select("id,title,category,description").eq("id", int(raw)).limit(1))
    if not res.data:
        await message.answer("❌ Bunday loyiha topilmadi. ID ni qayta yuboring."); return
    await state.update_data(project_id=int(raw), old_project=res.data[0])
    await state.set_state(ProjectAdmin.edit_title)
    await message.answer(T[lang]["enter_new_title"] + f"\nHozirgi nomi: {res.data[0].get('title','')}")


@dp.message(ProjectAdmin.edit_title)
async def project_edit_title(message: Message, state: FSMContext):
    lang = await get_language(message.from_user.id)
    if not await is_admin(message.from_user.id):
        await state.clear(); await message.answer(T[lang]["admin_only"]); return
    data = await state.get_data()
    title = (message.text or "").strip()
    if not title:
        await message.answer(T[lang]["enter_new_title"]); return
    if title != "-":
        await state.update_data(new_title=title[:200])
    else:
        await state.update_data(new_title=data["old_project"]["title"])
    await state.set_state(ProjectAdmin.edit_category)
    await message.answer(T[lang]["enter_category"], reply_markup=category_keyboard(lang))


@dp.message(ProjectAdmin.edit_category)
async def project_edit_category(message: Message, state: FSMContext):
    lang = await get_language(message.from_user.id)
    canonical = CATEGORY_TO_CANONICAL.get(message.text or "")
    data = await state.get_data()
    if canonical:
        await state.update_data(new_category=canonical)
    elif message.text == "-":
        await state.update_data(new_category=data["old_project"]["category"])
    else:
        await message.answer("Kategoriya tanlang yoki - yuboring.", reply_markup=category_keyboard(lang)); return
    await state.set_state(ProjectAdmin.edit_description)
    await message.answer(T[lang]["enter_new_description"], reply_markup=ReplyKeyboardRemove())


@dp.message(ProjectAdmin.edit_description)
async def project_edit_description(message: Message, state: FSMContext):
    lang = await get_language(message.from_user.id)
    if not await is_admin(message.from_user.id):
        await state.clear(); await message.answer(T[lang]["admin_only"]); return
    data = await state.get_data()
    desc = (message.text or "").strip()
    if desc == "-":
        desc = data["old_project"].get("description") or ""
    try:
        await db(supabase.table("projects").update({
            "title": data["new_title"],
            "category": data["new_category"],
            "description": desc[:3000],
        }).eq("id", data["project_id"]))
        await state.clear()
        await message.answer("✅ Loyiha ma’lumotlari tahrirlandi.", reply_markup=main_keyboard(lang, True))
    except Exception:
        logger.exception("Loyihani tahrirlashda xato")
        await message.answer("❌ Tahrirlashda xatolik. Render Logs'ni tekshiring.")


@dp.message(ProjectAdmin.delete_id)
async def project_delete_get_id(message: Message, state: FSMContext):
    lang = await get_language(message.from_user.id)
    if not await is_admin(message.from_user.id):
        await state.clear(); await message.answer(T[lang]["admin_only"]); return
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer(T[lang]["enter_project_id"]); return
    res = await db(supabase.table("projects").select("id,title").eq("id", int(raw)).limit(1))
    if not res.data:
        await message.answer("❌ Bunday loyiha topilmadi. ID ni qayta yuboring."); return
    await state.update_data(project_id=int(raw), project_title=res.data[0]["title"])
    await state.set_state(ProjectAdmin.delete_confirm)
    await message.answer(f"🗑 {res.data[0]['title']}\n" + T[lang]["confirm_delete"])


@dp.message(ProjectAdmin.delete_confirm)
async def project_delete_confirm(message: Message, state: FSMContext):
    lang = await get_language(message.from_user.id)
    if not await is_admin(message.from_user.id):
        await state.clear(); await message.answer(T[lang]["admin_only"]); return
    answer = (message.text or "").strip().casefold()
    yes = answer in {"ha", "да", "yes", "ҳа"}
    no = answer in {"yo‘q", "yo'q", "нет", "no", "не"}
    if not yes and not no:
        await message.answer(T[lang]["confirm_delete"]); return
    data = await state.get_data()
    try:
        if yes:
            await db(supabase.table("projects").delete().eq("id", data["project_id"]))
            await message.answer(f"✅ {data['project_title']} o‘chirildi.")
        else:
            await message.answer("❎ O‘chirish bekor qilindi.")
        await state.clear()
        await message.answer(T[lang]["admin_menu"], reply_markup=main_keyboard(lang, True))
    except Exception:
        logger.exception("Loyihani o'chirishda xato")
        await message.answer("❌ O‘chirishda xatolik. Render Logs'ni tekshiring.")


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
