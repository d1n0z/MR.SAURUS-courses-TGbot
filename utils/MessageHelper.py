import traceback

import aiogram
from aiogram.fsm.context import *
from aiogram.types import *

import locales as locale


async def download_photo(bot: aiogram.Bot, message: Message, path: str) -> bool:
    try:
        if message.document is not None:
            if message.document.mime_type.startswith("image/"):
                await bot.download_file((await bot.get_file(message.document.file_id)).file_path, path)
                return True

        if message.photo is not None:
            try:
                await bot.download_file((await bot.get_file(message.photo[1].file_id)).file_path, path)
            except:
                await bot.download_file((await bot.get_file(message.photo[0].file_id)).file_path, path)
            return True
    except:
        print(traceback.format_exc())

    return False


async def state_clear_light(state: FSMContext):
    try:
        (await state.get_data())['edit_message'].delete()
    except:
        pass

    await state.clear()


def bank_display(bank: str) -> str:
    display: str = ''
    bank = bank.lower()

    if bank == "sberbank":
        display = locale.get_button("sber")
    if bank == "tinkoff":
        display = locale.get_button("tinkoff")
    if bank == "raiffeisenbank":
        display = locale.get_button("raifaisen")
    if bank == "sbp":
        display = locale.get_button("sbp")

    return display


def is_menu_used(text: str):
    return text == locale.get_button("buy_course") or text == locale.get_button(
        "personal_cabinet") or text == locale.get_button("cart") or text == locale.get_button(
        "help") or text == locale.get_button("balance_topup") or text == locale.get_button("free_courses")
