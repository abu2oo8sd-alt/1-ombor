
import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton
)

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN topilmadi!")

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


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
