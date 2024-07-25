from aiogram.types import *

import utils.Checks as Checks


class MiniMessage:
    message: Message = None
    text: str = None
    media: InputFile = None
    reply_markup: ReplyKeyboardMarkup | InlineKeyboardMarkup = None

    def __init__(self, text: str = None, media: InputFile = None,
                 reply_markup: ReplyKeyboardMarkup | InlineKeyboardMarkup = None):
        self.text = text
        self.media = media
        self.reply_markup = reply_markup

    def __init__(self, message: Message):  # NOQA
        self.message = message
        if Checks.media(message):
            self.text = message.caption

        else:
            self.text = message.html_text

    async def answer(self, message: Message) -> Message:
        if self.media is None:
            return await message.answer(text=self.text, parse_mode="HTML", reply_markup=self.reply_markup)

        return await message.answer_photo(photo=self.media, caption=self.text, parse_mode="HTML",
                                          reply_markup=self.reply_markup)

    async def edit(self, message: Message):
        if not Checks.media(message):
            await message.edit_text(text=self.text, parse_mode="HTML", reply_markup=self.reply_markup)
            return self

        if self.media is not None:
            if message.photo is not None:
                await message.edit_media(media=InputMediaPhoto(media=self.media))

        if self.text is not None:
            await message.edit_caption(caption=self.text, parse_mode="HTML")

        return self
