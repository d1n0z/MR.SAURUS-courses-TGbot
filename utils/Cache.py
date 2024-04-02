import os
import time
import traceback
from threading import Thread
from typing import Any

from aiogram import Bot
from aiogram.types import BufferedInputFile, Chat

import data.db as db

cache = {"file": {"not_found_404_err": BufferedInputFile.from_file(path="data/media/global/not_found_404_err.png",
                                                                   filename="not found")}, "chat": {}, "invite": {},
         "bot": {}, "confirmPayment": {}, "locale": {},
         "mode": {"test": False, "sber_enabled": True, "sbp_enabled": True, "raiffaisen_enabled": True,
                  "tinkoff_enabled": True, "running": True, }}


def cachedInputFile(path: str, filename: str) -> BufferedInputFile | None:
    if not os.path.exists(path):
        return None if not os.path.exists("data/media/global/not_found_404_err.png") else cache["file"][
            "not_found_404_err"]

    if not (path in cache["file"]):
        try:
            ins: BufferedInputFile | None = BufferedInputFile.from_file(path=path, filename=filename)
        except Exception as e:
            ins = None
            print(f"Cache:cachedInputFile(path={path}, filename={filename}) -> None, {e}")

        if ins is not None:
            cache["file"][path] = ins
        return ins

    return cache["file"][path]


async def cachedChat(bot: Bot, chat: int) -> Chat | None:
    if not (chat in cache["chat"]):
        try:
            ins: Chat | None = await bot.get_chat(chat_id=chat)
        except Exception as e:
            ins = None
            print(f"Cache:cachedChat(chat={chat}) -> None, {e}")

        if ins is not None:
            cache["chat"][chat] = ins
        return ins

    return cache["chat"][chat]


def cachedLocale(key: str) -> db.LocalizedMessage | None:
    try:
        ins: db.LocalizedMessage | None = db.LocalizedMessage.select().where(db.LocalizedMessage.name == key).get()
    except Exception as e:
        traceback.print_exc()
        ins = None
        print(f"Cache:cachedLocale(key={key}) -> None, {e}")
    if not (key in cache["locale"]):
        if ins is not None:
            cache["locale"][ins] = ins
        return ins

    return cache["locale"][ins]


async def cachedInvite(bot: Bot, chat: int) -> Chat | None:
    if not (chat in cache["invite"]):
        try:
            ins: str | None = (await bot.create_chat_invite_link(chat)).invite_link
        except Exception as e:
            ins = None
            print(f"Cache:cachedInvite(chat={chat}) -> None, {e}")

        if ins is not None:
            cache["invite"][chat] = ins
        return ins

    return cache["invite"][chat]


def cachedMode(path: str) -> Any | None:
    if not (path in cache["mode"]):
        return None

    return cache["mode"][path]


def cacheRemove(path: str, raw: str = ""):
    full_path = ""
    group = cache

    for s in path.split("."):
        if not (s in group):
            print(f"Invalid cache path: {path} -> {s}")
            return

        full_path += f"[\"{s}\"]"
        group = group[s]

    exec(f"del cache{full_path}[\"{raw}\"]")


def cacheUpdate(path: str, value: Any):
    full_path = ""
    group = cache

    for s in path.split("."):
        if not (s in group):
            return

        full_path += f"[\"{s}\"]"
        group = group[s]

    exec(f"cache{full_path} = {value}")


def cacheGet(path: str):
    full_path = ""
    group = cache

    for s in path.split("."):
        if not (s in group):
            return

        full_path += f"[\"{s}\"]"
        group = group[s]

    get = ""

    exec(f"get = cache{full_path}")

    return get


def cacheClear():
    cache["file"].clear()
    cache["chat"].clear()
    cache["locale"].clear()
    cache["invite"].clear()


def cacheLoop():
    print("  ... Обработка кеша запущена")

    sets = db.getSettings()
    cacheUpdate("mode.sber_enabled", sets.sber_enabled)
    cacheUpdate("mode.tinkoff_enabled", sets.tinkoff_enabled)
    cacheUpdate("mode.raiffaisen_enabled", sets.raiffaisen_enabled)
    cacheUpdate("mode.sbp_enabled", sets.sbp_enabled)

    while cachedMode("running"):
        for _ in range(60 * 60 * 60):
            if not cachedMode("running"):
                break
            time.sleep(1)

        sum = len(cache["file"]) + len(cache["chat"])

        if sum == 0:
            continue

        cacheClear()
        print(f" Удалено {sum} мусора из кеша!")


def start():
    Thread(target=cacheLoop, args=()).start()
