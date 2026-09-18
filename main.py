import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

API_TOKEN = "8915334520:AAG3BVLL8xOXXoUxgIatriP0WmNF257x3_U"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Множество для хранения ID активных дежурных
active_shifts = set()


def get_main_keyboard(is_on_shift: bool):
    if is_on_shift:
        btn = KeyboardButton(text="🔴 Завершить смену")
    else:
        btn = KeyboardButton(text="🟢 Начать смену")
    return ReplyKeyboardMarkup(keyboard=[[btn]], resize_keyboard=True)


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    is_on = message.from_user.id in active_shifts
    await message.answer(
        "Привет! Нажми кнопку ниже, чтобы начать или завершить смену.",
        reply_markup=get_main_keyboard(is_on),
    )


@dp.message(F.text == "🟢 Начать смену")
async def start_shift(message: types.Message):
    active_shifts.add(message.from_user.id)
    await message.answer(
        "Вы заступили на смену! Все сообщения будут приходить сюда.",
        reply_markup=get_main_keyboard(True),
    )


@dp.message(F.text == "🔴 Завершить смену")
async def end_shift(message: types.Message):
    active_shifts.discard(message.from_user.id)
    await message.answer(
        "Смена завершена. Хорошего отдыха!",
        reply_markup=get_main_keyboard(False),
    )


@dp.message()
async def broadcast_to_shift(message: types.Message):
    user_id = message.from_user.id

    if user_id not in active_shifts:
        await message.answer(
            "Вы не на смене! Нажмите «🟢 Начать смену», чтобы отправлять и получать вызовы."
        )
        return

    sender_name = message.from_user.full_name
    caption_prefix = f"От: {sender_name}\n\n"

    recipients = [uid for uid in active_shifts if uid != user_id]

    if not recipients:
        await message.answer(
            "На смене пока только вы. Сообщение некому пересылать."
        )
        return

    for recipient_id in recipients:
        try:
            if message.text:
                await bot.send_message(
                    chat_id=recipient_id,
                    text=f"От: {sender_name}\n\n{message.text}",
                )
            elif message.photo:
                photo_id = message.photo[-1].file_id
                caption = caption_prefix + (message.caption or "")
                await bot.send_photo(
                    chat_id=recipient_id, photo=photo_id, caption=caption
                )
            elif message.video:
                video_id = message.video.file_id
                caption = caption_prefix + (message.caption or "")
                await bot.send_video(
                    chat_id=recipient_id, video=video_id, caption=caption
                )
            elif message.voice:
                caption = caption_prefix + (message.caption or "")
                await bot.send_voice(
                    chat_id=recipient_id,
                    voice=message.voice.file_id,
                    caption=caption,
                )
        except Exception as e:
            logging.error(f"Ошибка отправки: {e}")

    await message.answer("Сообщение отправлено бригаде на смене.")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
