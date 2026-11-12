
import os

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton
)

TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("RENDER_EXTERNAL_URL")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

WEBHOOK_PATH = "/telegram-webhook"

if not TOKEN:
    raise ValueError("BOT_TOKEN topilmadi!")

if not BASE_URL:
    raise ValueError("RENDER_EXTERNAL_URL topilmadi!")

if not WEBHOOK_SECRET:
    raise ValueError("WEBHOOK_SECRET topilmadi!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

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


@dp.message(CommandStart())
async def start(message: Message):
    buttons = [
        [KeyboardButton(text=cat) for cat in categories[i:i+2]]
        for i in range(0, len(categories), 2)
    ]

    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )

    await message.answer(
        "Assalomu alaykum!\n"
        "AutoCAD Projects Botga xush kelibsiz!\n\n"
        "Kategoriyani tanlang:",
        reply_markup=keyboard
    )


@dp.message()
async def category_handler(message: Message):
    if message.text in categories:
        await message.answer(
            f"📂 {message.text} kategoriyasi\n\n"
            "Quyidagi loyihalar tez orada joylashtiriladi:\n\n"
            "1. Loyiha №1\n"
            "2. Loyiha №2\n"
            "3. Loyiha №3\n\n"
            "Loyihalar ustida ish olib borilmoqda."
        )


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
