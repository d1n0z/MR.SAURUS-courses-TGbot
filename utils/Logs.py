from aiogram import Bot

import data.db as db
import utils.KeyBoards as KeyBoards


async def logStart(bot: Bot, user: db.User, referral: db.User | None):  # start
    print(
        f"@{user.username} ({user.id}) запустил бота/прошел капчу"
        f"{'' if referral is None else f' - реферал @{referral.username} ({referral.id})'}")

    for channel in db.LogChannel.select().where(db.LogChannel.type == "start"):
        try:
            await bot.send_message(
                chat_id=channel.channel,
                text=f"@ {user.username}({user.id}) запустил бота/прошел капчу"
                     f"{'' if referral is None else f' - реферал @{referral.username} ({referral.id})'}",
                parse_mode="HTML", reply_markup=KeyBoards.logsUserManage(user))
        except Exception as e:
            print(
                f"Logs: logStart(user={user.id}, referral={'None' if not referral else referral.id})::{channel.channel}"
                f" -> Error, {e}")


async def logBuy(bot: Bot, user: db.User, course: db.Course, promo: db.PromoCode | None, price: int,
                 discount: int):  # buy
    print(
        f"{user.username} ({user.id}) купил курс {course.name} по цене {price} со скидкой "
        f"{discount}%{'' if promo is None else f' - промо {promo.name} ({promo.discount}%)'}")

    for channel in db.LogChannel.select().where(db.LogChannel.type == "buy"):
        try:
            await bot.send_message(
                chat_id=channel.channel,
                text=f"@{user.username} ({user.id}) купил курс {course.name} по цене {price} со скидкой {discount}%" + (
                    '' if promo is None or promo.type != "discount" else f' - промо {promo.name} ({promo.discount}%)'),
                parse_mode="HTML", reply_markup=KeyBoards.logsUserManage(user))
        except Exception as e:
            print(
                f"Logs:logBuy(user={user.id}, course={course}, promo={promo}, price={price}, discount={discount})::"
                f"{channel.channel} -> Error, {e}")


async def logBalanceTopUp(bot: Bot, user: db.User, amount: int):  # balancetopup
    print(f"{user.username} ({user.id}) пополнил баланс на {amount} рублей")

    for channel in db.LogChannel.select().where(db.LogChannel.type == "balancetopup"):
        try:
            await bot.send_message(chat_id=channel.channel,
                                   text=f"{user.username} ({user.id}) пополнил баланс на {amount} рублей",
                                   parse_mode="HTML", reply_markup=KeyBoards.logsUserManage(user))
        except Exception as e:
            print(f"Logs:logStart(user={user.id}, amount={amount})::{channel.channel} -> Error, {e}")


async def logPromoUsage(bot: Bot, user: db.User, promocode: db.PromoCode):  # promocodeusage
    print(f"{user.username}({user.id}) использовал промо {promocode.name}"
          f"{'' if promocode.max_usages == -1 else f'{promocode.used}/{promocode.max_usages}'}")

    for channel in db.LogChannel.select().where(db.LogChannel.type == "promocodeusage"):
        try:
            text = (f"{user.username}({user.id}) использовал промо {promocode.name}"
                    f"{'' if promocode.max_usages == -1 else f'{promocode.used}/{promocode.max_usages}'}")
            await bot.send_message(chat_id=channel.channel,
                                   text=text,
                                   parse_mode="HTML", reply_markup=KeyBoards.logsUserManage(user))
        except Exception as e:
            print(f"Logs:logPromoUsage(user={user.id}, promocode={promocode})::{channel.channel} -> Error, {e}")


async def logBan(bot: Bot, user: db.User | None, admin: db.User, all: bool = False, using_logs: bool = False):  # ban
    if all:
        print(f"@{admin.username} ({admin.id}) забанил всех")
        for channel in db.LogChannel.select().where(db.LogChannel.type == "ban"):
            try:
                await bot.send_message(chat_id=channel.channel, text=f"@{admin.username} ({admin.id}) забанил всех",
                                       parse_mode="HTML",
                                       reply_markup=KeyBoards.logsUserManage(user, ban=False, balance=False))
            except Exception as e:
                print(
                    f"Logs:logBan(user={user.id}, admin={admin}, using_logs={using_logs})::all::{channel.channel} -> "
                    f"Error, {e}")
        return

    print(f"@ {admin.username}({admin.id}) забанил @{user.username} ({user.id})"
          f"{'' if not using_logs else' (через логи)'}")
    for channel in db.LogChannel.select().where(db.LogChannel.type == "ban"):
        try:
            await bot.send_message(chat_id=channel.channel,
                                   text=f"@ {admin.username}({admin.id}) забанил @{user.username}({user.id})"
                                        f"{'' if not using_logs else ' (через логи)'}\nДействия ниже будут применены "
                                        f"на пользователя: @{user.username} ({user.id})",
                                   parse_mode="HTML", reply_markup=KeyBoards.logsUserManage(user))
        except Exception as e:
            print(
                f"Logs:logBan(user={user.id}, admin={admin}, using_logs={using_logs})::{channel.channel} -> Error, {e}")


async def logUnban(bot: Bot, user: db.User | None, admin: db.User, all: bool = False,
                   using_logs: bool = False):  # unban
    if all:
        print(f"{admin.username} ({admin.id}) разбанил всех")
        for channel in db.LogChannel.select().where(db.LogChannel.type == "unban"):
            try:
                await bot.send_message(chat_id=channel.channel, text=f"@{admin.username} ({admin.id}) разбанил всех",
                                       parse_mode="HTML",
                                       reply_markup=KeyBoards.logsUserManage(user, ban=False, balance=False))
            except Exception as e:
                print(
                    f"Logs:logUnban(user={user.id}, admin={admin}, using_logs={using_logs})::all::{channel.channel} "
                    f"-> Error, {e}")
        return

    print(
        f"@{admin.username}({admin.id}) разбанил @{user.username} ({user.id})"
        f"{'' if not using_logs else ' (через логи)'}")
    for channel in db.LogChannel.select().where(db.LogChannel.type == "ban"):
        try:
            await bot.send_message(
                chat_id=channel.channel,
                text=f"@{admin.username}({admin.id}) разбанил @{user.username} ({user.id})"
                     f"{'' if not using_logs else' (через логи)'}\nДействия ниже будут применены на пользователя: "
                     f"@{user.username} ({user.id})",
                parse_mode="HTML", reply_markup=KeyBoards.logsUserManage(user))
        except Exception as e:
            print(
                f"Logs:logUnban(user={user.id}, admin={admin}, using_logs={using_logs})::{channel.channel} "
                f"-> Error, {e}")
