from aiogram import Bot
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
import data.db as db


async def subscribed(bot: Bot, user: int) -> bool:
    for channel in db.SubscribeChannel.select():
        if not (await subscribed_channel(bot, user, channel.channel)):
            return False

    return True


async def subscribed_channel(bot: Bot, user: int, channel: int) -> bool:
    try:
        if (await bot.get_chat_member(chat_id=channel, user_id=user)).status == "left":
            return False
    except TelegramBadRequest:
        return False
    except TelegramForbiddenError:
        return True

    return True


async def admin(user: db.User | int) -> bool:
    if isinstance(user, db.User):
        usr = user
    else:
        try:
            usr = db.User.get(id == user)
        except:
            return False
    return usr and usr.admin


def media(message: Message) -> bool:
    return (message.photo is not None or message.document is not None or message.audio is not None or
            message.animation is not None or message.sticker is not None or message.video is not None)
