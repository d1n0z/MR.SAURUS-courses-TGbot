import asyncio
import logging
import os
import sys
import traceback
from datetime import datetime, timedelta

import aiogram
from aiogram.enums import *
from aiogram.exceptions import *
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import *
from sympy import *

import config
import data.db as db
import locales as locale
import utils.Cache as Cache
import utils.CaptchaGenerator as CaptchaGenerator
import utils.Checks as Checks
import utils.Cleaner as Cleaner
import utils.EXCEL as EXCEL
import utils.KeyBoards as KeyBoards
import utils.Logs as Logs
import utils.Math as Math
import utils.MessageHelper as MessageHelper
import utils.States as States
from botutils import recursiveParentIDS
from utils.Scheduler import Scheduler
from utils.payment.PaymentSystemAPI import PaymentSystem
from utils.payment.AaioAPI import Aaio
from utils.payment.AnypayAPI import Anypay


def setupPayment() -> PaymentSystem | None:
    paymentID = db.getSettings().bank

    print("  ... Инициализация платежной системы #" + str(paymentID))

    # if paymentID == 0:  # paylama
    #     return PayLama(config.PAYLAMA.API_KEY)
    # elif paymentID == 1:  # payok
    #     return Payok(config.PAYOK.API_ID, config.PAYOK.API_KEY, config.PAYOK.SITE_ID, config.PAYOK.SECRET_KEY)
    if paymentID == 2:  # anypay
        return Anypay(config.ANYPAY.SECRET_KEY, config.ANYPAY.API_ID, config.ANYPAY.API_KEY, config.ANYPAY.MERCHANT_ID)
    # elif paymentID == 4:  # aaio
    else:
        return Aaio(config.AAIO.SECRET_KEY, config.AAIO.API_KEY, config.AAIO.MERCHANT_ID)
    # elif paymentID == 3:  # drop
    #     return Drop()
    # else:
    #     print("  ... Не удалось инициализировать платежную систему!")
    #     return None


global paymentapi
# noinspection PyRedeclaration
paymentapi = setupPayment()
anypay = Anypay(config.ANYPAY.SECRET_KEY, config.ANYPAY.API_ID, config.ANYPAY.API_KEY, config.ANYPAY.MERCHANT_ID)
aaio = Aaio(config.AAIO.SECRET_KEY, config.AAIO.API_KEY, config.AAIO.MERCHANT_ID)

logging.basicConfig(level=logging.INFO)

bot = aiogram.Bot(token=config.TOKEN)
storage = MemoryStorage()
dp = aiogram.Dispatcher(storage=storage)
scheduler = Scheduler()


# noinspection PyShadowingNames,PyComparisonWithNone
@dp.message(CommandStart())
async def start(message: Message, command: CommandObject, state: FSMContext):
    global paymentapi
    userId = message.chat.id

    try:
        user = db.User.get(db.User.id == userId)
    except:
        user = None

    if user is None:
        try:
            referral = int(command.args)
        except:
            referral = 0

        user = db.User.create(
            id=userId,
            username="Неизвестный" if message.from_user.username is None else message.from_user.username,
            captcha=CaptchaGenerator.generateCaptcha(), from_referral=referral)
        # CaptchaGenerator.saveCaptcha(user.captcha, user.id)

    if Cache.cachedMode("test"):
        await Logs.logStart(bot, user, None if user.from_referral == 0 else db.User.select().where(
            db.User.id == user.from_referral).get())

    if user.banned:
        await message.answer(locale.get_message("banned_user"), parse_mode="HTML")
        return

    if user.blocked_bot:
        user.blocked_bot = False
        user.save()

    if not (await Checks.subscribed(bot, user.id)):
        await message.answer(locale.get_message("subscribe"), parse_mode="HTML",
                             reply_markup=(await KeyBoards.subscribe(bot)))
        return

    if user.captcha is not None:
        await message.answer_photo(caption=locale.get_message("captcha"), parse_mode="HTML",
                                   photo=Cache.cachedInputFile(path=f"data/captcha/{user.captcha.lower()}.jpg",
                                                               filename="𤩒𤨗𤩀𤨻𤩌𤩨𤨠𤨣𤩌𤩨𤨠𤨤𤩌𤩞𤩌𤩨.jpg"))
        return

    if (await state.get_state()) != None:
        await state.set_state()

    if command.args != None:
        if command.args.startswith("course_"):
            try:
                course_id = int(command.args.split("course_")[1])
                course = db.Course.select().where(db.Course.id == course_id).get()

                if course == None:
                    raise Exception("course is None")

                category: db.CourseCategory = db.CourseCategory.select().where(
                    db.CourseCategory.id == course.category).get()

                if not (await Cache.cachedChat(bot, course.channel)):
                    await callback.answer(locale.get_message("course_unavailable"), show_alert=True)
                    return

                data = await state.get_data()

                await state.update_data(course=course, discount=data["discount"] if "discount" in data else 0,
                                        course_category=category)
                promocode: int = 0 if not "promocode" in data else data["promocode"].discount
                price = Math.calculateDiscountDisplay(course.price, promocode, course.discount, category.discount,
                                                      db.getSettings().discount)

                m = Cache.cachedInputFile("data/media/global/courses.png", "loose again.mp4")

                if course.media is not None:
                    m = Cache.cachedInputFile(f"{course.media}", "𤩒𤨗𤩀𤨻𤩌𤩨𤨠𤨣𤩌𤩨𤨠𤨤𤩌𤩞𤩌𤩨.png")

                await message.answer_photo(photo=m, caption=locale.get_message("course_select", name=course.name,
                                                                               description=course.description,
                                                                               price=price),
                                           parse_mode="HTML",
                                           reply_markup=KeyBoards.courseInfoInline(category.id, course.id, user))

                return
            except:
                print(traceback.format_exc())
                pass

        if command.args.startswith("category_"):
            try:
                # noinspection PyTypeChecker
                category = int(command.args.split("category_")[1])
                course_category: db.CourseCategory = db.CourseCategory.select().where(
                    db.CourseCategory.id == category).get()

                if course_category == None:
                    raise Exception("category is None")

                await state.update_data(course_category=course_category)
                state_data = await state.get_data()

                if "course" in state_data and state_data["course"] != None:
                    await state.update_data(state=None)

                m = Cache.cachedInputFile("data/media/global/courses.png", "loose again.mp4")
                if course_category.media is not None:
                    m = Cache.cachedInputFile(
                        "data/media/global/courses.png" if course_category.media is None else course_category.media,
                        "loose again.mp4")

                await message.answer_photo(
                    photo=m, caption=None if not course_category.description else course_category.description,
                    parse_mode="HTML", reply_markup=KeyBoards.coursesInline(course_category.parent,
                                                                            course_category.id, user))

                return
            except:
                print(traceback.format_exc())
                pass

    await message.answer(text=locale.get_message("welcome",
                                                 user=user.username),
                         parse_mode="HTML",
                         reply_markup=KeyBoards.welcomeReply((await Checks.admin(user))))


# noinspection PyComparisonWithNone,PyTypeChecker,PyUnboundLocalVariable,PyUnresolvedReferences,PyShadowingNames
@dp.callback_query(lambda c: c.data)
async def callback(callback: CallbackQuery, state: FSMContext):
    global paymentapi, anypay
    id = callback.from_user.id

    try:
        user: db.User | None = db.User.get(db.User.id == id)
    except:
        user = None

    if user is None:
        return

    if user.banned:
        return

    if callback.data == "check_subscribe":
        if not (await Checks.subscribed(bot, id)):
            await callback.answer(text=locale.get_message("subscribe2"), parse_mode="HTML", show_alert=True)
            return

        await callback.message.edit_text(text=locale.get_message("welcome",
                                                                 user=user.username),
                                         parse_mode="HTML",
                                         reply_markup=KeyBoards.welcomeInline())

        await callback.message.answer(locale.get_message("thx"), parse_mode="HTML",
                                      reply_markup=KeyBoards.welcomeReply((await Checks.admin(user))))
        return

    if not (await Checks.subscribed(bot, id)):
        return

    if callback.data == "ok":
        await callback.answer("Больше эта кнопка ничего не делает.")
        return

    if callback.data == 'switch_payment':
        curr = db.getSettings().bank
        bank = 1 if curr == 2 else 2
        db.Settings.update(bank=bank).execute()
        bank = 'aaio' if curr == 2 else 'anypay'
        await callback.message.edit_caption(caption='✅ ' + bank + ' был установлен как основная платежка')
        paymentapi = setupPayment()
        return

    if callback.data.startswith("drop_check_"):
        action = callback.data.split("drop_check_")[1].split("_")[0]
        uid = callback.data.split("_")[3]
        try:
            info = paymentapi.payments[uid]
        except:
            await callback.message.edit_caption(caption=str(callback.message.caption) +
                                                        f"\nВремя подтверждения вышло.\nРешение принято в: "
                                                        f"{datetime.now().strftime('%d.%m.%Y %H:%M')}")
            await callback.answer("Время на ответ уже вышло.")
            return

        if user.admin or user.id == info.user.id:
            if action == "accept":
                await bot.send_message(info['user'].id,
                                       locale.get_message("drop_check_translation_ok", amount=info['amount']),
                                       parse_mode="HTML")

                info['user'].balance += info['amount']
                db.BalanceHistory.create(customer=info['user'], amount=info['amount'])
                await Logs.logBalanceTopUp(bot, info['user'], info['amount'])

                try:
                    referral_user: db.User = db.User.select().where(db.User.id == info['user'].from_referral).get()

                    if referral_user is not None:
                        referral_user.balance += info['amount'] * 0.20
                        referral_user.save()
                except:
                    pass

                info['user'].save()

                await callback.message.edit_caption(caption=str(
                    callback.message.caption) + f"\nРешение принято в {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                                                    reply_markup=KeyBoards.dropCheckAcceptorInline(uid, True))
                return

            if action == "deny":
                await bot.send_message(info['user'].id,
                                       locale.get_message("drop_check_translation_fail", amount=info['amount'],
                                                          uid=uid), parse_mode="HTML")
                await callback.message.edit_caption(caption=str(
                    callback.message.caption) + f"\nРешение принято в {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                                                    reply_markup=KeyBoards.dropCheckAcceptorInline(uid, False))
                return

    if user.admin and callback.data.startswith("logs_"):
        if callback.data.startswith("logs_ban_"):
            id = int(callback.data.split("logs_ban_")[1])

            target = db.User.select().where(db.User.id == id).get()
            target.banned = True
            target.save()
            await Logs.logBan(bot, target, user, using_logs=True)

            await callback.message.edit_text(callback.message.html_text, parse_mode="HTML",
                                             reply_markup=KeyBoards.logsUserManage(target))
            return

        if callback.data.startswith("logs_unban_"):
            id = int(callback.data.split("logs_unban_")[1])

            target = db.User.select().where(db.User.id == id).get()
            target.banned = False
            target.save()
            await Logs.logUnban(bot, target, user, using_logs=True)

            await callback.message.edit_text(callback.message.html_text, parse_mode="HTML",
                                             reply_markup=KeyBoards.logsUserManage(target))
            return

        if callback.data.startswith("logs_balance_"):
            id = int(callback.data.split("logs_balance_")[1].split("_")[0])
            balance = int(callback.data.split(f"logs_balance_{id}_")[1])

            target = db.User.select().where(db.User.id == id).get()
            target.balance = balance
            target.save()

            await callback.message.edit_text(callback.message.html_text, parse_mode="HTML",
                                             reply_markup=KeyBoards.logsUserManage(target))
            return

        return

    curr_state = await state.get_state()

    if curr_state is None:
        try:
            state_data = (await state.get_data())
            edit_message = state_data['edit_message']
        except:
            pass

        if callback.data == "settings_drops_create_end":
            data = (await state.get_data())
            db.Drop.create(name=data['drop_name'], userid=data['drop_user'], channel=data['drop_channel'],
                           sberbank=data['drop_sber'], tinkoff=data['drop_tinkoff'],
                           raiffeisenbank=data['drop_raiffeisenbank'], sbp=data['drop_sbp'])
            await callback.message.edit_text("Выбираем дропа для удаления или создаем нового:", parse_mode="HTML",
                                             reply_markup=KeyBoards.settingsDropsSelectorInline())
            return

        if callback.data == "paid_courses_category_create_end":
            parent_category: db.CourseCategory | None = None if not "category_current" in state_data else state_data[
                "category_current"]
            id = Math.current_milli_time() + len(db.CourseCategory.select()) + 1
            category_media = state_data["category_media"]
            category: db.CourseCategory = db.CourseCategory.create(
                id=id, name=state_data["category_name"],
                media=None if not category_media else f"data/media/category/{id}.png",
                description=state_data["category_description"], parent=parent_category,)
                # discount=state_data["category_discount"],

            if category_media is not None:
                os.rename(category_media, category.media)

            await state.clear()
            if 'rto' in state_data:
                category: int = int(state_data['rto'])
                course_category: db.CourseCategory = db.CourseCategory.select().where(
                    db.CourseCategory.id == category).get()
                await state.update_data(course_category=course_category)

                await edit_message.answer_photo(
                    photo=Cache.cachedInputFile("data/media/global/courses.png" if course_category.media is None else
                                                course_category.media,"loose again.mp4"),
                    caption=None if not course_category.description else
                    course_category.description, parse_mode="HTML",
                    reply_markup=KeyBoards.coursesInline(course_category.parent, course_category.id, user))
                return
            await edit_message.edit_text(
                f"Новая категория создана! Вот её подробности:\n\nНазвание: {category.name}\nОписание: "
                f"{'нету' if not category.description else category.description}\nКатегория: "
                f"{'Глобальная' if parent_category is None else parent_category.name}"
                # f"\nСкидка: {category.discount}%"
                , parse_mode="HTML",
                reply_markup=KeyBoards.cancelInlinePaidCoursesCategoryCreateEnd(category, "paid_courses"))
            return

    if curr_state is not None:
        if callback.data == "cancel":
            if Checks.media(callback.message):
                await callback.message.edit_caption(caption=locale.get_message("cancel"), parse_mode="HTML")
            else:
                await callback.message.edit_text(locale.get_message("cancel"), parse_mode="HTML")
            await state.set_state()
            return

        if user.admin and callback.data == "admin":
            await callback.message.delete()
            await callback.message.answer("Открываю админ-панель 🎩🎩🎩", parse_mode="HTML",
                                          reply_markup=KeyBoards.adminMenuReply())
            return

        state_data = (await state.get_data())

        try:
            edit_message = state_data['edit_message']
        except:
            pass

        if curr_state == States.SettingsBot.payment and callback.data.startswith("settings_bot_payment_"):
            action = state_data["action"]
            value = 0
            type = callback.data.split("settings_bot_payment_")[1]

            if type == "paylama":
                value = 0
            elif type == "payok":
                value = 1
            elif type == "anypay":
                value = 2
            elif type == "drop":
                value = 3

            paymentapi = setupPayment()

            exec(f"import data.db as db\nset = db.getSettings()\nset.{action} = {value}\nset.save()")

            await edit_message.edit_text("Выбираем категорию бота:", reply_markup=KeyBoards.settingsBotSelectorInline())
            await state.clear()
            return

        if curr_state == States.CategoryCreate.description or curr_state == States.CategoryCreate.media:
            if callback.data.startswith("paid_courses_category_create_skip_"):
                to = callback.data.split("paid_courses_category_create_skip_")[1]

                if to == "description":
                    if 'rto' in state_data:
                        await state.update_data(category_description=None, rto=state_data['rto'])
                    else:
                        await state.update_data(category_description=None)
                    await state.set_state(States.CategoryCreate.media)
                    await edit_message.edit_text("Отправьте медию для новой категории:",
                                                 reply_markup=KeyBoards.skipInline(
                                                     "paid_courses_category_create_skip_media"))
                    return

                if to == "media":
                    # save_path = f"data/media/temp/{Math.current_milli_time()*Math.randInt(2, 999)}.png"
                    # shutil.copy("data/media/global/courses.png", save_path)
                    # await state.update_data(category_media=save_path)
                    await state.update_data(category_media=None)
                    await state.update_data(category_media=None)
                    await state.set_state()
                    await edit_message.edit_text(
                        "Завершить создание категории?",
                        reply_markup=KeyBoards.customInline("Завершить","paid_courses_category_create_end"))
                    return

        if (curr_state == States.DropCreate.sber or curr_state == States.DropCreate.tinkoff or
                curr_state == States.DropCreate.raiffeisenbank or curr_state == States.DropCreate.sbp):
            if callback.data.startswith("settings_drops_create_"):
                bank = callback.data.split("settings_drops_create_")[1]

                if bank == "tinkoff":
                    await state.update_data(drop_sber=None)
                    await state.set_state(States.DropCreate.tinkoff)
                    await callback.message.edit_text("Введи реквизиты для оплаты по тинькоффу:",
                                                     reply_markup=KeyBoards.skipInline(
                                                         "settings_drops_create_raiffeisenbank"))
                    return

                if bank == "raiffeisenbank":
                    await state.update_data(drop_tinkoff=None)
                    await state.set_state(States.DropCreate.raiffeisenbank)
                    await callback.message.edit_text("Введи реквизиты для оплаты по райфайзену:",
                                                     reply_markup=KeyBoards.skipInline("settings_drops_create_sbp"))
                    return

                if bank == "sbp":
                    await state.update_data(drop_raiffeisenbank=None)
                    await state.set_state(States.DropCreate.sbp)
                    await callback.message.edit_text("Введи реквизиты для оплаты по сбп:",
                                                     reply_markup=KeyBoards.skipInline("settings_drops_create_sbp2"))
                    return

                if bank == "sbp2":
                    await edit_message.edit_text("Завершить создание дропа?",
                                                 reply_markup=KeyBoards.customInline("Завершить",
                                                                                     "settings_drops_create_end"))
                    await state.set_state()
                    return

        if curr_state == States.BalanceTopUp.waiting_payment.state:
            if callback.data != "translation_check":
                return

            # if paymentapi.type() == "drop":
            #     await callback.message.edit_caption(caption=locale.get_message("drop_check_translation"),
            #                                         parse_mode="HTML", reply_markup=KeyBoards.cancelInline())
            #     await state.set_state(States.BalanceTopUp.waiting_check)
            #     return

            data = await state.get_data()

            if not paymentapi.confirmPayment(data["id"]):
                await callback.answer(
                    locale.get_message("pay_error"),
                    show_alert=True)
                return

            await state.clear()
            amount: int = int(data["amount"])

            db.BalanceHistory.create(customer=user, amount=amount)
            user.balance += amount
            try:
                referral_user: db.User = db.User.select().where(db.User.id == user.from_referral).get()

                if referral_user is not None:
                    referral_user.balance += amount * 0.20
                    referral_user.save()
            except:
                pass
            await Logs.logBalanceTopUp(bot, user, amount)
            user.save()

            await callback.message.edit_caption(caption=locale.get_message("pay_success", amount=amount),
                                                parse_mode="HTML",
                                                reply_markup=KeyBoards.profileInline())
            return

        if curr_state == States.BalanceTopUp.bank.state:
            if not callback.data.startswith("bank_"):
                return

            amount = state_data['amount']
            bank: str = callback.data.split("bank_")[1]
            bank_display: str = MessageHelper.bank_display(bank)

            payment = paymentapi.createPaymentCard(user, amount, bank)

            print(payment)
            if not bool(payment["success"]):
                await edit_message.edit_caption(caption=locale.get_message("sorry_error"), parse_mode="HTML")
                await state.clear()
                return

            await state.set_state(States.BalanceTopUp.waiting_payment)
            await state.update_data(id=payment["id"],
                                    amount=amount,
                                    bank=bank)

            if "card" in payment:
                await edit_message.edit_caption(caption=
                                                locale.get_message("oplata_created_card", bank_display=bank_display,
                                                                   card=payment['card'],
                                                                   amount=payment['amount'], id=payment['id']),
                                                parse_mode="HTML", reply_markup=KeyBoards.translationInline())
            else:
                await edit_message.edit_caption(caption=
                                                locale.get_message("oplata_created_form", bank_display=bank_display,
                                                                   url=payment['url'],
                                                                   amount=payment['amount'], id=payment['id']),
                                                parse_mode="HTML", reply_markup=KeyBoards.translationInline())
            return

        if curr_state == States.FreeCourseAction.action.state:
            data = await state.get_data()

            if data["action"] == "edit":
                if callback.data == "free_courses_edit_save":
                    course: db.FreeCourses = data["course"]

                    course.name = data["course_name"]
                    course.url = data["course_url"]

                    course.save()
                    await state.clear()
                    await callback.message.edit_text("Кнопка сохранена ✅", parse_mode="HTML",
                                                     reply_markup=KeyBoards.backToAdminPanelInline())
                    return

                if callback.data == "free_courses_edit_name":
                    await state.set_state(States.FreeCourseAction.name)
                    await callback.message.edit_text(
                        "Введите название кнопки: (оно будет отображаться так-же и у пользователя)", parse_mode="HTML",
                        reply_markup=KeyBoards.cancelInline())
                    return

                if callback.data == "free_courses_edit_url":
                    await state.set_state(States.FreeCourseAction.url)
                    await callback.message.edit_text("Введите ссылку для кнопки:", parse_mode="HTML",
                                                     reply_markup=KeyBoards.cancelInline())
                    return

                return
            return

        if curr_state == States.FreeCourseAction.select_button.state:
            if callback.data.startswith("free_courses_delete_"):
                id: int = int(callback.data.split("free_courses_delete_")[1])
                db.FreeCourses.delete_by_id(id)

                await callback.message.edit_text("Выберите удаляемую кнопку:", parse_mode="HTML",
                                                 reply_markup=KeyBoards.freeCoursesListSelectorInline("delete"))
                return

            if callback.data.startswith("free_courses_edit_"):
                id: int = int(callback.data.split("free_courses_edit_")[1])
                course: db.FreeCourses = db.FreeCourses.select().where(db.FreeCourses.id == id).get()
                await state.set_state(States.FreeCourseAction.action)
                await state.update_data(course=course,
                                        course_name=course.name,
                                        course_url=course.url)
                await callback.message.edit_text("Выберите категорию изменения кнопки:", parse_mode="HTML",
                                                 reply_markup=KeyBoards.editFreeCoursesSelectActionsSelectorInline())
                return

            await state.clear()
            return

        if curr_state == States.Mailing.confirm.state and callback.data == "mailing_confirm":
            state_data = await state.get_data()
            message: Message = state_data["message"]
            await state.clear()
            await callback.message.edit_text("Отправляю ваше сообщение пользователям по фильтру.")

            mail_users = db.User.select().where((db.User.blocked_bot == False) & (db.User.admin == False))
            mail_filters = state_data["mail_filters"]

            if mail_filters == "customer":
                mail_users = mail_users.where((db.User.purchases > 0) | (db.User.balance > 0))
            if mail_filters == "non_customer":
                mail_users = mail_users.where((db.User.purchases == 0) & (db.User.balance == 0))
            if mail_filters == "banned":
                mail_users = mail_users.where(db.User.banned)

            sent = 0
            bot_blocked = 0

            for mail_user in mail_users:
                try:
                    await message.copy_to(chat_id=mail_user.id, parse_mode="HTML")
                    sent += 1
                except TelegramForbiddenError as e:
                    if not e.message.__contains__("blocked by the user"):
                        pass
                    bot_blocked += 1
                    mail_user.blocked_bot = True
                    mail_user.save()

            await callback.message.edit_text("Отправка сообщения завершена! 🥳\n"
                                             f"\n Успешно отправлено: {sent}"
                                             f"\n Заблокировало бота: {bot_blocked}"
                                             f"\n\nПользователи заблокировшие бота были сохранены в базу!",
                                             parse_mode="HTML", reply_markup=KeyBoards.backToAdminPanelInline())
            return

        if curr_state == States.CourseSelection.bank.state:
            if not callback.data.startswith("bank_"):
                return

            data = await state.get_data()

            bank: str = callback.data.split("bank_")[1]
            bank_display: str = MessageHelper.bank_display(bank)
            amount: int = data["price"]

            payment = paymentapi.createPaymentCard(user, amount, bank)

            if not bool(payment["success"]) or (not "card" in payment and not "form" in payment):
                await callback.message.edit_caption(caption=locale.get_message("pay_error2"), parse_mode="HTML",
                                                    reply_markup=KeyBoards.backwardsToParentCourseCategory(
                                                        data["course_category"].id))
                await state.clear()
                return

            await state.set_state(States.CourseSelection.waiting_payment)
            await state.update_data(id=payment["id"],
                                    amount=amount,
                                    bank=bank)
            if "card" in payment:
                await callback.message.edit_caption(
                    caption=locale.get_message("oplata_created_card", bank_display=bank_display, card=payment['card'],
                                               amount=payment['amount'], id=payment['id']),
                    parse_mode="HTML", reply_markup=KeyBoards.translationInline())
            else:
                await callback.message.edit_caption(
                    caption=locale.get_message("oplata_created_form", bank_display=bank_display, card=payment['url'],
                                               amount=payment['amount'], id=payment['id']),
                    parse_mode="HTML", reply_markup=KeyBoards.translationInline())
            return

        if curr_state == States.PromoCodeCreate.type.state:
            if not callback.data.startswith("promocode_type_"):
                return

            type = callback.data.split("promocode_type_")[1]
            await state.update_data(promocode_type=type)
            await state.set_state(States.PromoCodeCreate.value)

            if type == "discount":
                await callback.message.edit_text("Введите процент скидки на товар:", parse_mode="HTML")
            elif type == "channel":
                await callback.message.edit_text("Перешлите сообщение/айди канала:", parse_mode="HTML")
            elif type == "balance":
                await callback.message.edit_text("Выберите сумму, которая будет начислена на баланс:",
                                                 parse_mode="HTML")

            return

        if curr_state == States.Cart.waiting_payment.state:
            if callback.data != "translation_check":
                return

            # if paymentapi.type() == "drop":
            #     await callback.message.edit_caption(locale.get_message("drop_check_translation"),
            #                                         KeyBoards.cancelInline())
            #     await state.set_state(States.Cart.waiting_check)
            #     return

            data = await state.get_data()

            if not paymentapi.confirmPayment(data["id"]):
                await callback.answer(locale.get_message("pay_notsend"), show_alert=True)
                return

            await state.clear()
            amount: int = int(data["amount"])

            db.BalanceHistory.create(customer=user, amount=amount)
            user.balance += amount
            user.save()
            await callback.message.edit_caption(locale.get_message("accept_buy_cart", amount=amount), parse_mode="HTML",
                                                reply_markup=KeyBoards.cartConfirmBuy())
            return

        if curr_state == States.CourseSelection.waiting_payment.state:
            if callback.data != "translation_check":
                return

            data = await state.get_data()

            if not paymentapi.confirmPayment(data["id"]):
                await callback.answer(locale.get_message("pay_notsend"), show_alert=True)
                return

            await state.set_state()
            amount: int = int(data["amount"])
            course: db.Course = data["course"]

            db.BalanceHistory.create(customer=user, amount=amount)
            user.balance += amount
            user.save()

            await callback.message.edit_caption(
                caption=locale.get_message("course_buy_confirm", name=course.name, description=course.description,
                                           price=course.price), parse_mode="HTML",
                reply_markup=KeyBoards.courseConfirmBuy(data["course_category"].id))
            return

        await MessageHelper.state_clear_light(state)

    if callback.data == "course_category":
        await state.clear()
        await callback.message.edit_media(
            media=InputMediaPhoto(media=Cache.cachedInputFile("data/media/global/courses.png", "loose again.mp4")))
        await callback.message.edit_caption(caption=locale.get_message("paid_courses"), parse_mode="HTML",
                                            reply_markup=KeyBoards.coursesInline(user=user))
        return

    if callback.data.startswith("course_category_"):
        category: int = int(callback.data.split("course_category_")[1])
        course_category: db.CourseCategory = db.CourseCategory.select().where(db.CourseCategory.id == category).get()
        await state.update_data(course_category=course_category)
        state_data = await state.get_data()
        if "course" in state_data and state_data["course"] != None:
            await state.update_data(state=None)

        await callback.message.edit_media(media=InputMediaPhoto(media=Cache.cachedInputFile(
            "data/media/global/courses.png" if course_category.media is None else course_category.media,
            "loose again.mp4")))

        await callback.message.edit_caption(
            caption=None if not course_category.description else course_category.description, parse_mode="HTML",
            reply_markup=KeyBoards.coursesInline(course_category.parent, course_category.id, user))
        return

    if callback.data.startswith("course_share_"):
        share_id = callback.data.split("course_share_")[1]
        url = f"https://t.me/{(await bot.get_me()).username}?start=course_{share_id}"

        await callback.message.answer(f"Вот прямая ссылка на товар: 👇\n Ссылкой: {url}\n Кодом: <code>{url}</code>",
                                      parse_mode="HTML")
        await callback.answer("Ссылка отправлена")
        return

    if callback.data.startswith("category_share_"):
        share_id = callback.data.split("category_share_")[1]
        url = f"https://t.me/{(await bot.get_me()).username}?start=category_{share_id}"

        await callback.message.answer(
            f"Вот прямая ссылка на категорию: 👇\n Ссылкой: {url}\n Кодом: <code>{url}</code>", parse_mode="HTML")
        await callback.answer("Ссылка отправлена")
        return

    if callback.data.startswith("course_select_"):
        course: db.Course = db.Course.select().where(
            db.Course.id == int(callback.data.split("course_select_")[1])).get()
        category: db.CourseCategory = db.CourseCategory.select().where(db.CourseCategory.id == course.category).get()

        if not (await Cache.cachedChat(bot, course.channel)):
            await callback.answer(locale.get_message("course_unavailable"), show_alert=True)
            return

        data = await state.get_data()

        await state.update_data(course=course, discount=data["discount"] if "discount" in data else 0)
        promocode: int = 0 if not "promocode" in data else data["promocode"].discount
        price = Math.calculateDiscountDisplay(course.price, promocode, course.discount, category.discount,
                                              db.getSettings().discount)

        if course.media is not None:
            m = Cache.cachedInputFile(f"{course.media}", "𤩒𤨗𤩀𤨻𤩌𤩨𤨠𤨣𤩌𤩨𤨠𤨤𤩌𤩞𤩌𤩨.png")

            if m is not None:
                await callback.message.edit_media(media=InputMediaPhoto(media=m))

        await callback.message.edit_caption(
            caption=locale.get_message("course_select", name=course.name, description=course.description, price=price),
            parse_mode="HTML", reply_markup=KeyBoards.courseInfoInline(data["course_category"].id, course.id, user))
        return

    if callback.data == "cart_buy_confirm":
        data = await state.get_data()

        if "cart_storage" not in data:
            await callback.message.delete()
            return

        courses: list = data["cart_storage"]
        price: int = 0

        for course in courses:
            if len(db.Purchase.select().where(
                    (db.Purchase.customer == user) & (db.Purchase.course == course))) != 0 or (
                    await Checks.subscribed_channel(bot, user.id, course.channel)):
                courses.remove(course)

            price += Math.calculateDiscount(course.price, course.discount,
                                            0 if not "promocode" in data else data["promocode"].discount,
                                            db.getSettings().discount)

        if len(courses) == 0:
            await callback.message.delete()
            return

        await state.update_data(price=price)
        await callback.message.edit_media(
            media=InputMediaPhoto(media=Cache.cachedInputFile("data/media/global/payment.png", "fuck you")))
        if price > user.balance:
            await callback.answer(locale.get_message("not_enough_balance"), show_alert=True)
            await state.set_state(States.CourseSelection.bank)
            data = paymentapi.createPaymentCard(user, (price - user.balance) + 1)
            await callback.message.edit_caption(caption=f'✔ Нажмите на кнопку ниже для оплаты', parse_mode="HTML",
                                                reply_markup=KeyBoards.selectBankInline(data['url']))
            return

        for course in courses:
            db.Purchase.create(customer=user, course=course.id, price=price, discount=0)
            await Logs.logBuy(bot, user, course, None if not "promocode" in data else data["promocode"], price,
                              0)

        user.balance -= price
        try:
            referral_user: db.User | None = db.User.select().where(db.User.id == user.from_referral).get()
        except:
            referral_user: None = None

        if referral_user != None:
            referral_user.balance += price * 0.05
            referral_user.save()

        user.save()

        urls = ""

        for course in courses:
            urls += "\n" + (await bot.create_chat_invite_link(course.channel, member_limit=1)).invite_link

        await state.clear()
        await callback.message.edit_media(media=InputMediaPhoto(
            media=Cache.cachedInputFile("data/media/global/purchased.png", "barabara bererebere")))
        await callback.message.edit_caption(caption=locale.get_message("invites_send", urls=urls), parse_mode="HTML")
        return

    if callback.data == "course_buy_confirm":
        data = await state.get_data()

        if "course" not in data:
            await callback.message.delete()
            return

        course: db.Course = data["course"]
        price: int = data["price"]
        discount: int = data["discount"]

        if len(db.Purchase.select().where((db.Purchase.customer == user) & (db.Purchase.course == course))) != 0 or (
                await Checks.subscribed_channel(bot, user.id, course.channel)):
            print("buy_sub: ", await Checks.subscribed_channel(bot, user.id, course.channel))
            await callback.answer(locale.get_message("course_already_bought"), show_alert=True)
            return

        if price > user.balance:
            await callback.answer(locale.get_message("not_enough_balance"), show_alert=True)
            await state.set_state(States.CourseSelection.bank)
            await callback.message.edit_media(
                media=InputMediaPhoto(media=Cache.cachedInputFile("data/media/global/payment.png", "fuck you")))
            data = paymentapi.createPaymentCard(user, (price - user.balance) + 1)
            await callback.message.edit_caption(caption=f'✔ Нажмите на кнопку ниже для оплаты', parse_mode="HTML",
                                                reply_markup=KeyBoards.selectBankInline(data['url']))
            return

        db.Purchase.create(customer=user, course=course.id, price=price, discount=discount)
        user.balance -= price
        try:
            referral_user: db.User | None = db.User.select().where(db.User.id == user.from_referral).get()
        except:
            referral_user: None = None

        if referral_user != None:
            referral_user.balance += price * 0.05
            referral_user.save()

        user.save()

        await Logs.logBuy(bot, user, course, None if not "promocode" in data else data["promocode"], price, discount)

        await callback.message.edit_media(media=InputMediaPhoto(
            media=Cache.cachedInputFile("data/media/global/purchased.png", "barabara bererebere")))
        await callback.message.edit_caption(
            caption=locale.get_message("course_bought", name=course.name, description=course.description,
                                       price=course.price,
                                       urls=(await bot.create_chat_invite_link(course.channel,
                                                                               member_limit=1)).invite_link),
            parse_mode="HTML", reply_markup=KeyBoards.cancelInline(
                "buy_course"))  # KeyBoards.backwardsToParentCourseCategory(data["course_category"].id))
        return

    if callback.data == "course_buy":
        data = await state.get_data()

        if "course" not in data:
            await callback.message.delete()
            return

        course: db.Course = data["course"]
        category: db.CourseCategory = db.CourseCategory.select().where(db.CourseCategory.id == course.category).get()
        promocode: db.PromoCode | None = None if not "promocode" in data else data["promocode"]
        price = Math.calculateDiscount(course.price, course.discount, 0 if not promocode else promocode.discount,
                                       category.discount, db.getSettings().discount)

        data["price"] = price
        await state.update_data(price=price)

        if len(db.Purchase.select().where((db.Purchase.customer == user) & (db.Purchase.course == course))) != 0 or (
                await Checks.subscribed_channel(bot, user.id, course.channel)):
            await callback.answer(locale.get_message("course_already_bought"), show_alert=True)
            return

        await callback.message.edit_media(
            media=InputMediaPhoto(media=Cache.cachedInputFile("data/media/global/payment.png", "fuck you")))
        if price > user.balance:
            await callback.answer(locale.get_message("not_enough_balance"), show_alert=True)
            await state.set_state(States.CourseSelection.bank)
            data = paymentapi.createPaymentCard(user, (price - user.balance) + 1)
            await callback.message.edit_caption(caption=f'✔ Нажмите на кнопку ниже для оплаты', parse_mode="HTML",
                                                reply_markup=KeyBoards.selectBankInline(data['url']))
            return

        await callback.message.edit_caption(
            caption=locale.get_message("course_buy_confirm", name=course.name, description=course.description,
                                       price=course.price), parse_mode="HTML",
            reply_markup=KeyBoards.courseConfirmBuy(data["course_category"].id))
        return

    if callback.data == "course_promocode":
        await state.set_state(States.CourseSelection.promocode)
        await state.update_data(edit_message=callback.message)
        await callback.message.edit_caption(caption=locale.get_message("send_promo"), parse_mode="HTML")
        return

    if callback.data == "course_cart":
        data = await state.get_data()

        if "cart_storage" not in data or "course" not in data:
            data["cart_storage"] = []

        course: db.Course = data["course"]

        if len(db.Purchase.select().where((db.Purchase.customer == user) & (db.Purchase.course == course))) != 0 or (
                await Checks.subscribed_channel(bot, user.id, course.channel)):
            await callback.answer(locale.get_message("course_already_bought"), show_alert=True)
            return

        if data["course"] in data["cart_storage"]:
            data["cart_storage"].remove(course)
            await callback.answer(locale.get_message("del_cart"), show_alert=True)
        else:
            data["cart_storage"].append(course)
            await callback.answer(locale.get_message("add_cart"), show_alert=True)

        await state.update_data(cart_storage=data["cart_storage"])
        return

    if callback.data == "cart_promocode":
        await state.set_state(States.Profile.promocode)
        await state.update_data(edit_message=callback.message)
        await callback.message.edit_caption(caption=locale.get_message("send_promo"), parse_mode="HTML")
        return

    if callback.data == "cart_remove":
        state_data = await state.get_data()

        if "cart_storage" not in state_data or len(state_data["cart_storage"]) == 0:
            await callback.message.edit_caption(caption=locale.get_message("cart_empty"))
            return
        await callback.message.edit_caption(caption="Выберите курс для удаления из корзины:", parse_mode="HTML",
                                            reply_markup=KeyBoards.cartRemoveCourse(state_data["cart_storage"]))
        return

    if callback.data.startswith("cart_remove_"):
        state_data = await state.get_data()

        if "cart_storage" not in state_data:
            await callback.message.edit_caption(caption=locale.get_message("cart_empty"), parse_mode="HTML")
            return

        id = int(callback.data.split("cart_remove_")[1])

        for course in state_data["cart_storage"]:
            if course.id != id:
                continue

            state_data["cart_storage"].remove(course)
            break

        if len(state_data["cart_storage"]) == 0:
            await callback.message.edit_caption(caption=locale.get_message("cart_empty"), parse_mode="HTML")
            return
        await callback.message.edit_caption(caption=locale.get_message("select_the_course_to_delete_from_the_trash"),
                                            parse_mode="HTML",
                                            reply_markup=KeyBoards.cartRemoveCourse(state_data["cart_storage"]))
        return

    if callback.data == "cart_pay":
        await callback.message.edit_caption(caption="Подтверждение оплаты корзины", parse_mode="HTML",
                                            reply_markup=KeyBoards.cartConfirmBuy())
        return

    if callback.data == "cancel":
        await callback.message.delete()
        return

    if callback.data == "history_balance":
        if user.purchases == 0 and user.balance == 0:
            await callback.message.edit_caption(caption=locale.get_message("not_replenishment"), parse_mode="HTML",
                                                reply_markup=KeyBoards.backToProfileInline())
            return

        purchases = locale.get_message("pay_history")
        for action in db.BalanceHistory.select().where(
                (db.BalanceHistory.customer == user) & (db.BalanceHistory.amount > 0)):
            purchases += f"\n{action.date.strftime('%Y-%m-%d %H:%M')} +{action.amount} рублей"

        await callback.message.edit_caption(caption=
                                            locale.get_message("pay_error_history") if purchases == locale.get_message(
                                                "pay_history") else purchases,
                                            parse_mode="HTML", reply_markup=KeyBoards.backToProfileInline())
        return

    if callback.data == "buy_course":
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=Cache.cachedInputFile("data/media/global/courses.png", "loose again.mp4"),
            caption=locale.get_message("paid_courses"), parse_mode="HTML",
            reply_markup=KeyBoards.coursesInline(user=user))
        return

    if callback.data == "history_purchases":
        if user.purchases == 0:
            await callback.message.edit_caption(caption=locale.get_message("not_buy"), parse_mode="HTML",
                                                reply_markup=KeyBoards.backToProfileInline())
            return

        purchases = locale.get_message("buy_history")
        for purchase in db.Purchase.select().where(db.Purchase.customer == user):
            try:
                purchases += (f"\n{purchase.date.strftime('%Y-%m-%d %H:%M')} "
                              f"{purchase.course.name} {purchase.price} рублей "
                              f"{f'(на {purchase.discount}% дешевле)' if purchase.discount != 0 else ''}")
            except:
                print(traceback.format_exc())
        await callback.message.edit_caption(caption=purchases, parse_mode="HTML",
                                            reply_markup=KeyBoards.backToProfileInline())
        return

    if callback.data == "profile":
        await callback.message.edit_caption(caption=locale.get_message("id+balik", id=user.id, amount=user.balance,
                                                                       registered=user.registered.strftime(
                                                                           '%Y-%m-%d %H:%M')),
                                            parse_mode="HTML", reply_markup=KeyBoards.profileInline())
        return

    if callback.data == "balance_topup":
        await state.set_state(States.BalanceTopUp.amount)
        await callback.message.edit_media(
            media=InputMediaPhoto(media=Cache.cachedInputFile("data/media/global/balance_topup.png", "xd")))
        edit_message = await callback.message.edit_caption(caption=locale.get_message("pay_create"), parse_mode="HTML")
        await state.update_data(edit_message=edit_message)
        return

    if callback.data == "referral_system":
        await callback.message.edit_caption(
            caption=locale.get_message("referal_system", bot=(await bot.get_me()).username, id=user.id,
                                       amount=user.referrals),
            parse_mode="HTML", reply_markup=KeyBoards.backToProfileInline())
        return

    if callback.data == "promocode_activation":
        await state.set_state(States.Profile.promocode)
        await state.update_data(edit_message=callback.message)
        await callback.message.edit_caption(caption=locale.get_message("send_promo"), parse_mode="HTML")
        return

    if not user.admin:
        return

    if callback.data == "admin":
        await callback.message.delete()
        await callback.message.answer("Открываю админ-панель 🎩🎩🎩", parse_mode="HTML",
                                      reply_markup=KeyBoards.adminMenuReply())
        return

    if callback.data == "settings_bot":
        await callback.message.edit_text("Выбираем категорию бота:", reply_markup=KeyBoards.settingsBotSelectorInline())
        return

    if callback.data.startswith("settings_bot_"):
        action: str = callback.data.split("settings_bot_")[1]

        if action == "minimum_topup":
            edit_message = await callback.message.edit_text(
                f"Текущее значение: {db.getSettings().minimum_topup}\nВведите новую минимальную сумму пополнения:",
                reply_markup=KeyBoards.cancelInline("settings_bot"))
            await state.set_state(States.SettingsBot.intValue)
            await state.update_data(action=action, edit_message=edit_message)
            return

        if action == "maximum_topup":
            edit_message = await callback.message.edit_text(
                f"Текущее значение: {db.getSettings().maximum_topup}\nВведите новую максимальную сумму пополнения:",
                reply_markup=KeyBoards.cancelInline("settings_bot"))
            await state.set_state(States.SettingsBot.intValue)
            await state.update_data(action=action, edit_message=edit_message)
            return

        if action == "discount":
            edit_message = await callback.message.edit_text(
                f"Текущее значение: {db.getSettings().discount}%\nВведите новую глобальную скидку:",
                reply_markup=KeyBoards.cancelInline("settings_bot"))
            await state.set_state(States.SettingsBot.intValue)
            await state.update_data(action=action, edit_message=edit_message)
            return

        if action == "payment":
            edit_message = await callback.message.edit_text(
                f"Текущее значение: {db.getSettings().payment + 1}\nВыберите новую платежку:",
                reply_markup=KeyBoards.settingsBotPaymentSelectionInline())

            await state.set_state(States.SettingsBot.payment)
            await state.update_data(action=action, edit_message=edit_message)
            return

        if action == "test":
            Cache.cacheUpdate("mode.test", not Cache.cachedMode("test"))
            await callback.message.edit_text("Выбираем категорию бота:",
                                             reply_markup=KeyBoards.settingsBotSelectorInline())
            return

# if action.startswith("bank_"):
#     action = action.split("bank_")[1]  # .split("_enabled")[0]
#
#     exec(f'Cache.cacheUpdate("mode.{action}", not Cache.cachedMode("{action}"))')
#     exec(
#         f"import data.db as db\nset = db.getSettings()\nset.{action} = Cache.cachedMode(\"{action}\")\nset.save()")
#
#     await callback.message.edit_text("Выбираем категорию бота:",
#                                      reply_markup=KeyBoards.settingsBotSelectorInline())
#     return

        if action == "subscribe":
            await callback.message.edit_text("Выбираем канал для удаления или создаем новый:",
                                             reply_markup=KeyBoards.settingsBotSettingsSubscribeChannelSelectorInline())
            return

        if action == "subscribe_create":
            edit_message = await callback.message.edit_text("Введи название для канала с подпиской:")

            await state.update_data(edit_message=edit_message)
            await state.set_state(States.SubscribeChannelCreate.name)
            return

        if action.startswith("subscribe_delete_"):
            id = action.split("subscribe_delete_")[1]
            db.SubscribeChannel.select().where(db.SubscribeChannel.id == id).get().delete_instance()

            await callback.message.edit_text("Выбираем канал для удаления или создаем новый:",
                                             reply_markup=KeyBoards.settingsBotSettingsSubscribeChannelSelectorInline())
            return

    if callback.data == "settings_logs":
        await callback.message.edit_text("Выбираем категорию логов:",
                                         reply_markup=KeyBoards.settingsLogsSelectorInline())
        return

    if callback.data == "settings_logs_create":
        edit_message = await callback.message.edit_text("Введи название для канала с логами:")
        await state.update_data(edit_message=edit_message)
        await state.set_state(States.LogsCreate.name)
        return

    if callback.data.startswith("settings_logs_delete_"):
        id = callback.data.split("settings_logs_delete_")[1]
        db.LogChannel.select().where(db.LogChannel.id == id).get().delete_instance()
        state_data = await state.get_data()
        await callback.message.edit_text("Выбираем канал для удаления или создаем новый:",
                                         reply_markup=KeyBoards.settingsLogsChannelSelectorInline(
                                             state_data["logs_category"]))
        return

    if callback.data.startswith("settings_logs_"):
        logs_category = callback.data.split("settings_logs_")[1]
        await state.update_data(logs_category=logs_category)
        await callback.message.edit_text("Выбираем канал для удаления или создаем новый:",
                                         reply_markup=KeyBoards.settingsLogsChannelSelectorInline(logs_category))
        return

    if callback.data == "settings_messages":
        await callback.message.edit_text("Выбираем сообщение для настройки:", parse_mode="HTML",
                                         reply_markup=KeyBoards.settingsLocaleSelectorInline("messages"))
        return

    if callback.data.startswith("settings_messages_"):
        msg_id: str = (callback.data.split("settings_messages_")[1].
                       replace("_edit", "").replace("_reset", ""))
        await state.update_data(msg_id=msg_id,
                                category="messages",
                                edit_message=callback.message)
        if callback.data.endswith("edit"):
            await state.set_state(States.EditBotMessage.waiting_value)
            await callback.message.edit_text("Введите новый текст:", parse_mode="HTML",
                                             reply_markup=KeyBoards.cancelInline())
            return

        if callback.data.endswith("reset"):
            if not Cache.cachedLocale("msg-" + msg_id):
                await callback.answer(f"Невозможно сбросить теста для \"{msg_id}\", потому что он не найден.")
                return
            locale.set_message(msg_id, Cache.cachedLocale("msg-" + msg_id).default)
            try:
                await callback.message.edit_text(f"Сброшенный текст для \"{msg_id}\":\n{locale.get_message(msg_id)}",
                                                 parse_mode="HTML",
                                                 reply_markup=KeyBoards.settingsLocaleEditInline("messages", msg_id))
            except:
                await callback.answer("Упс, ошибочка. Кажется это сообщение уже сброшенно.")
            return

        await callback.message.edit_text(f"Текущий текст для \"{msg_id}\":\n{locale.get_message(msg_id)}",
                                         parse_mode="HTML",
                                         reply_markup=KeyBoards.settingsLocaleEditInline("messages", msg_id))
        return

    if callback.data == "settings_drops":
        await callback.message.edit_text("Выбираем дропа для удаления или создаем нового:", parse_mode="HTML",
                                         reply_markup=KeyBoards.settingsDropsSelectorInline())
        return

    if callback.data.startswith("settings_drops_delete_"):
        db.Drop.select().where(
            db.Drop.userid == callback.data.split("settings_drops_delete_")[1]).get().delete_instance()
        await callback.message.edit_text("Выбираем дропа для удаления или создаем нового:", parse_mode="HTML",
                                         reply_markup=KeyBoards.settingsDropsSelectorInline())
        return

    if callback.data == "settings_drops_create":
        edit_message = await callback.message.edit_text("Введите отображаемое название для дропа:", parse_mode="HTML")
        await state.update_data(edit_message=edit_message, drop_name=None, drop_channel=-1, drop_user=-1,
                                drop_sber=None, drop_tinkoff=None, drop_raiffeisenbank=None, drop_sbp=None)
        await state.set_state(States.DropCreate.name)
        return

    if callback.data == "settings_media":
        await callback.message.edit_text("Выбираем медию для настройки:", parse_mode="HTML",
                                         reply_markup=KeyBoards.settingsMediaSelectorInline())
        return

    if (callback.data.startswith("settings_media_") or
            (callback.data.startswith("edit_category_set_photo_paid_") and
             callback.data.split("edit_category_set_photo_paid_")[1] == '-1')):
        try:
            edit_message = await callback.message.edit_text("Отправьте новую медию:", parse_mode="HTML",
                                                            reply_markup=KeyBoards.cancelInline("settings_media"))
        except:
            edit_message = await callback.message.answer("Отправьте новую медию:", parse_mode="HTML",
                                                            reply_markup=KeyBoards.cancelInline("settings_media"))
        await state.set_state(States.SettingsMedia.media)
        if callback.data.startswith("edit_category_set_photo_paid_"):
            await state.update_data(action='courses', edit_message=edit_message, cat=-1)
        else:
            await state.update_data(action=callback.data.split("settings_media_")[1], edit_message=edit_message, cat=1)
        return

    if callback.data.startswith("promocode_delete"):
        if callback.data == "promocode_delete":
            await callback.message.edit_text("Выбираем промокод для удаления:", parse_mode="HTML",
                                             reply_markup=KeyBoards.promoCodeSelectorInline("delete"))
            return

        id: int = int(callback.data.split("promocode_delete_")[1])
        promo: db.PromoCode = db.PromoCode.select().where(db.PromoCode.id == id).get()

        promo.delete_instance()

        await callback.message.edit_text("Выбираем промокод для удаления:", parse_mode="HTML",
                                         reply_markup=KeyBoards.promoCodeSelectorInline("delete"))
        return

    if callback.data == "promocode_create":
        await state.set_state(States.PromoCodeCreate.name)
        await state.update_data(edit_message=callback.message)
        await callback.message.edit_text("Выбираем названия для промокода:", parse_mode="HTML",
                                         reply_markup=KeyBoards.cancelInline())
        return

    if callback.data.startswith("promocode_edit"):
        if callback.data == "promocode_edit":
            await callback.message.edit_text("Выбираем промокод для изменения:", parse_mode="HTML",
                                             reply_markup=KeyBoards.promoCodeSelectorInline("edit"))
            return

        if callback.data.startswith("promocode_edit_") and simplify(
                callback.data.split("promocode_edit_")[1]).is_integer:
            id: int = int(callback.data.split("promocode_edit_")[1])
            promocode: db.PromoCode = db.PromoCode.select().where(db.PromoCode.id == id).get()
            await state.update_data(promocode=promocode)
            await callback.message.edit_text(
                f"Название: {promocode.name}\nКод: <code>{promocode.code}</code>\nИспользований: {promocode.used}/"
                f"{promocode.max_usages}\nВключен: {'да' if promocode.enabled else 'нет'}\n" + str(
                    f"Канал: #<code>{promocode.channel}</code>" if promocode.type == "channel" else
                    f"Скидка: {promocode.discount}%" if promocode.type == "discount" else
                    f"Баланс: {promocode.amount}"),
                parse_mode="HTML", reply_markup=KeyBoards.editPromoCodeSelectActionsSelectorInline(promocode))
            return

        data = await state.get_data()

        if "promocode" not in data:
            await state.clear()
            await callback.message.delete()
            return

        promocode: db.PromoCode = data["promocode"]

        if callback.data == "promocode_edit_generatecode":
            promocode.code = CaptchaGenerator.randomText()
            await callback.message.edit_text(
                f"Название: {promocode.name}\nКод: <code>{promocode.code}</code>\nИспользований: "
                f"{promocode.used}/{promocode.max_usages}\nВключен: {'да' if promocode.enabled else 'нет'}\n" + str(
                    f"Канал: #<code>{promocode.channel}</code>" if promocode.type == "channel" else
                    f"Скидка: {promocode.discount}%" if promocode.type == "discount" else
                    f"Баланс: {promocode.amount}"
                ),
                parse_mode="HTML", reply_markup=KeyBoards.editPromoCodeSelectActionsSelectorInline(promocode))
            return

        # if callback.data == "promocode_edit_type":
        if callback.data == "promocode_edit_toggle":
            promocode.enabled = not promocode.enabled

            await callback.message.edit_text(
                f"Название: {promocode.name}\nКод: <code>{promocode.code}</code>\nИспользований: "
                f"{promocode.used}/{promocode.max_usages}\nВключен: {'да' if promocode.enabled else 'нет'}\n" + str(
                    f"Канал: #<code>{promocode.channel}</code>" if promocode.type == "channel" else
                    f"Скидка: {promocode.discount}%" if promocode.type == "discount" else
                    f"Баланс: {promocode.amount}"
                ),
                parse_mode="HTML", reply_markup=KeyBoards.editPromoCodeSelectActionsSelectorInline(promocode))
            return

        if callback.data == "promocode_edit_maxuses":
            await state.update_data(edit_message=callback.message)
            await state.set_state(States.PromoCodeEdit.maxUsages)
            await callback.message.edit_text("Максимальное количество использований промо: (-1 = бесконечно)",
                                             parse_mode="HTML", reply_markup=KeyBoards.cancelInline())
            return

        if callback.data == "promocode_edit_value":
            await state.update_data(edit_message=callback.message)
            await state.set_state(States.PromoCodeEdit.value)
            if promocode.type == "channel":
                await callback.message.edit_text("Перешли сообщение/Отправь айди канала", parse_mode="HTML",
                                                 reply_markup=KeyBoards.cancelInline())
                return
            if promocode.type == "balance":
                await callback.message.edit_text("Какую сумму добавить к балансу", parse_mode="HTML",
                                                 reply_markup=KeyBoards.cancelInline())
                return
            if promocode.type == "discount":
                await callback.message.edit_text("Новая скидка:", parse_mode="HTML",
                                                 reply_markup=KeyBoards.cancelInline())
                return
            return

        if callback.data == "promocode_edit_save":
            promocode.save()
            await callback.message.edit_text("Сохранено!\nВыбираем промокод для изменения:", parse_mode="HTML",
                                             reply_markup=KeyBoards.promoCodeSelectorInline("edit"))
            return

        await MessageHelper.state_clear_light(state)
        # return

    if (callback.data.startswith("paid_courses") or
            ((callback.data.startswith("edit_courses_") or callback.data.startswith("edit_category_") or
              callback.data.startswith('edit_course_')) and callback.data.count('_paid') > 0)):

        if callback.data.startswith('edit_courses_category_costs_paid_'):
            try:
                edit_message = await callback.message.edit_text("Введи новую цену для всех товаров в категории:")
            except:
                edit_message = await callback.message.answer("Введи новую цену для всех товаров в категории:")
            await state.set_state(States.CourseEdit.price)
            await state.update_data(category=callback.data.split('edit_courses_category_costs_paid_')[1],
                                    edit_message=edit_message)
            return

        if callback.data == "paid_courses":
            await callback.message.edit_text("Выбираем настройку:", parse_mode="HTML",
                                             reply_markup=KeyBoards.managePaidCoursesTypeSelectorInline())
            return

        if callback.data == "paid_courses_category":
            await state.clear()
            await callback.message.edit_text("Выбери действие для настройки категорий курсов:", parse_mode="HTML",
                                             reply_markup=KeyBoards.managePaidCoursesSelectorInline("category"))
            return

        if callback.data == "paid_courses_category_delete":
            await state.update_data(category_action="delete")
            await callback.message.edit_text("Выбери категорию для удаления:", parse_mode="HTML",
                                             reply_markup=KeyBoards.paidCoursesSelectorInline("category", "delete"))
            return

        if callback.data.startswith("edit_courses_category_discount_paid_"):
            category = callback.data.split('edit_courses_category_discount_paid_')[1]
            try:
                edit_message = await callback.message.edit_text("Введи новую цену для всех товаров в категории:")
            except:
                edit_message = await callback.message.answer("Введи новую скидку для всех товаров в категории:")
            await state.set_state(States.CategoryEdit.discount)
            await state.update_data(category=category, edit_message=edit_message)
            return

        state_data = await state.get_data()

        if callback.data.startswith("paid_courses_category_select_category_") and "category_action" in state_data and \
                state_data["category_action"] == "delete":
            category = int(callback.data.split("paid_courses_category_select_category_")[1])
            new = db.CourseCategory.select().where(db.CourseCategory.id == category).get()
            old = None if new == None or new.parent == None else db.CourseCategory.select().where(
                db.CourseCategory.id == new.parent).get()

            await state.update_data(category_parent=old, category_current=new)
            await callback.message.edit_text("Выбери категорию для удаления:", parse_mode="HTML",
                                             reply_markup=KeyBoards.paidCoursesSelectorInline("category", "delete", old,
                                                                                              new))
            return

        if (callback.data == "paid_courses_category_delete_finish" or
                callback.data.startswith('edit_courses_delete_category_paid_')):
            new = None
            if callback.data.startswith('edit_courses_delete_category_paid_'):
                cat_curr = db.CourseCategory
                cat_curr = cat_curr.select().where(
                    cat_curr.id == callback.data.split('edit_courses_delete_category_paid_')[1])[0]
                await state.update_data(category_current=cat_curr)
                state_data = await state.get_data()

            if "category_current" in state_data:
                new = state_data["category_current"]
                found = [new]
                courses = []
                while len(found) > 0:
                    for f in found:
                        f.delete_instance()

                        for c in db.Course.select().where(db.Course.category == f):
                            courses.append(c)

                        for sub in db.CourseCategory.select().where(db.CourseCategory.parent == f.id):
                            found.append(sub)

                        for c in courses:
                            c.delete_instance()
                            courses.remove(c)

                        found.remove(f)

                new = None if new is None or new.parent is None else db.CourseCategory.select().where(
                    db.CourseCategory.id == new.parent).get()

            parent = None if new is None or new.parent is None else db.CourseCategory.select().where(
                db.CourseCategory.id == new.parent).get()
            await state.update_data(category_parent=parent, category_current=new)
            try:
                await callback.message.edit_text(
                    "Вы успешно удалили категорию.\nВыбери категорию для удаления:",
                    parse_mode="HTML",
                    reply_markup=KeyBoards.paidCoursesSelectorInline("category","delete", parent, new)
                )
            except:
                await state.update_data(
                    edit_message=await callback.message.answer(
                        "Вы успешно удалили категорию.\nВыбери категорию для удаления:",
                        parse_mode="HTML",
                        reply_markup=KeyBoards.paidCoursesSelectorInline("category","delete", parent, new)
                    )
                )
            return

        if callback.data == "paid_courses_category_edit":
            await state.update_data(category_action="edit")
            await callback.message.edit_text("Выбери категорию для изменения:", parse_mode="HTML",
                                             reply_markup=KeyBoards.paidCoursesSelectorInline("category", "edit"))
            return

        if callback.data.startswith("paid_courses_category_select_category_") and "category_action" in state_data and \
                state_data["category_action"] == "edit":
            category = int(callback.data.split("paid_courses_category_select_category_")[1])
            new = db.CourseCategory.select().where(db.CourseCategory.id == category).get()
            old = None if new == None or new.parent == None else db.CourseCategory.select().where(
                db.CourseCategory.id == new.parent).get()

            await state.update_data(category_parent=old, category_current=new)
            await callback.message.edit_text("Выбери категорию для изменения:", parse_mode="HTML",
                                             reply_markup=KeyBoards.paidCoursesSelectorInline("category", "edit", old,
                                                                                              new))
            return

        if callback.data == "paid_courses_category_edit_finish":
            new = None
            edit = None

            if "category_current" in state_data:
                edit = state_data["category_current"]
                new = None if edit is None or edit.parent is None else db.CourseCategory.select().where(
                    db.CourseCategory.id == edit.parent).get()

            # parent = None if new is None or new.parent is None else db.CourseCategory.select().where(
            #     db.CourseCategory.id == new.parent).get()

            edit_message = await callback.message.edit_text(
                f"Название: {edit.name}\nОписание: {edit.description}\n"
                f"Категория: {'Глобальная' if new is None else new.name}"
                # f"\nСкидка: {category.discount}%"
                "\nВыбери действие для изменения:"
                , parse_mode="HTML",
                reply_markup=KeyBoards.editPaidCategorySelectActionsSelectorInline(edit))

            await state.update_data(course_category=edit, category=edit, category_edit=edit,
                                    category_parent=new, edit_message=edit_message)

            return

        if callback.data == "paid_courses_category_create":
            await state.update_data(category_action="create")
            await callback.message.edit_text("Выберите категорию, в которой создать категорию:", parse_mode="HTML",
                                             reply_markup=KeyBoards.paidCoursesSelectorInline("category", "create",
                                                                                              allow_select_global=True))
            return

        if callback.data == "paid_courses_category_edit":
            await state.update_data(category_action="edit")
            await callback.message.edit_text("Выбери категорию для изменения:", parse_mode="HTML",
                                             reply_markup=KeyBoards.paidCoursesSelectorInline("category", "edit"))
            return

        if callback.data.startswith("paid_courses_category_select_category_") and "category_action" in state_data and \
                state_data["category_action"] == "create":
            category = int(callback.data.split("paid_courses_category_select_category_")[1])
            new = db.CourseCategory.select().where(db.CourseCategory.id == category).get()
            old = None if new == None or new.parent == None else db.CourseCategory.select().where(
                db.CourseCategory.id == new.parent).get()

            await state.update_data(category_parent=old, category_current=new)
            await callback.message.edit_text("Выберите категорию, в которой создать категорию:", parse_mode="HTML",
                                             reply_markup=KeyBoards.paidCoursesSelectorInline("category", "create", old,
                                                                                              new,
                                                                                              allow_select_global=True))
            return

        if (callback.data == "paid_courses_category_create_finish" or
                callback.data.startswith("edit_courses_add_category_paid_")):
            if callback.data.startswith("edit_courses_add_category_paid_"):
                category = int(callback.data.split('edit_courses_add_category_paid_')[1])
                if category >= 0:
                    new = db.CourseCategory.select().where(db.CourseCategory.id == category).get()
                    old = None if new == None or new.parent == None else db.CourseCategory.select().where(
                        db.CourseCategory.id == new.parent).get()

                    await state.update_data(category_action="create", category_parent=old, category_current=new,
                                            rto=category)
                    state_data = await state.get_data()
            current = None if not "category_current" in state_data else state_data["category_current"]

            try:
                edit_message = await callback.message.edit_text("Введи название категории:", parse_mode="HTML")
            except:
                edit_message = await callback.message.answer("Введи название категории:", parse_mode="HTML")
            await state.update_data(category_current=current, edit_message=edit_message)
            await state.set_state(States.CategoryCreate.name)
            return

        if callback.data == "paid_courses_course":
            await state.clear()
            await callback.message.edit_text("Выбери действие для настройки платных курсов:", parse_mode="HTML",
                                             reply_markup=KeyBoards.managePaidCoursesSelectorInline("course"))
            return

        if callback.data == "paid_courses_course_create" or callback.data == "edit_courses_add_product_paid":
            await state.update_data(course_action="create")
            try:
                await callback.message.edit_text("Выбери новую категорию для курса:",
                                             reply_markup=KeyBoards.paidCoursesSelectorInline(
                                                 "category",
                                                 "create_course",
                                                 select_only_empty_categories=True))
            except:
                await callback.message.answer("Выбери новую категорию для курса:",
                                             reply_markup=KeyBoards.paidCoursesSelectorInline(
                                                 "category",
                                                 "create_course",
                                                 select_only_empty_categories=True))
            return

        if (callback.data.startswith("paid_courses_category_select_category_") and
                "course_action" in state_data and state_data["course_action"] == "create"):
            category = int(callback.data.split("paid_courses_category_select_category_")[1])
            new = db.CourseCategory.select().where(db.CourseCategory.id == category).get()
            old = None if new == None or new.parent == None else db.CourseCategory.select().where(
                db.CourseCategory.id == new.parent).get()

            await state.update_data(category_parent=old, category_current=new)
            await callback.message.edit_text("Выбери категорию для нового курса:", parse_mode="HTML",
                                             reply_markup=KeyBoards.paidCoursesSelectorInline(
                                                 "category", "create_course", old, new,
                                                 select_only_empty_categories=True))
            return

        if (callback.data == "paid_courses_category_create_course_finish" or
                callback.data.startswith("edit_courses_add_product_paid_")):
            if callback.data.startswith("edit_courses_add_product_paid_"):
                category = int(callback.data.split('edit_courses_add_product_paid_')[1])
                new = db.CourseCategory.select().where(db.CourseCategory.id == category).get()
                old = None if new == None or new.parent == None else db.CourseCategory.select().where(
                    db.CourseCategory.id == new.parent).get()

                await state.update_data(course_action="create", category_parent=old, category_current=new)
                state_data = await state.get_data()
                await state.update_data(rto=category)
            try:
                edit_message = await callback.message.edit_text("Введи название для нового курса:")
            except:
                edit_message = await callback.message.answer("Введи название для нового курса:")
            await state.update_data(course_category=state_data["category_current"], edit_message=edit_message)
            await state.set_state(States.CourseCreate.name)
            return

        if callback.data == "paid_courses_course_delete":
            await state.update_data(course_action="delete")
            await callback.message.edit_text("Выбери курс в категории для удаления:", parse_mode="HTML",
                                             reply_markup=KeyBoards.paidCoursesSelectorInline("course", "delete"))
            return

        if callback.data.startswith("paid_courses_course_select_category_") and "course_action" in state_data and \
                state_data["course_action"] == "delete":
            category = int(callback.data.split("paid_courses_course_select_category_")[1])
            new = db.CourseCategory.select().where(db.CourseCategory.id == category).get()
            old = None if new == None or new.parent == None else db.CourseCategory.select().where(
                db.CourseCategory.id == new.parent).get()

            await state.update_data(category_parent=old, category_current=new)
            await callback.message.edit_text("Выбери курс в категории для удаления:", parse_mode="HTML",
                                             reply_markup=KeyBoards.paidCoursesSelectorInline("course", "delete", old,
                                                                                              new))
            return

        if callback.data.startswith("paid_courses_course_delete_course_") and "course_action" in state_data and \
                state_data["course_action"] == "delete":
            course = int(callback.data.split("paid_courses_course_delete_course_")[1])
            delete: db.Course = db.Course.select().where(db.Course.id == course).get()

            delete.delete_instance()

            await callback.message.edit_text("Выбери курс в категории для удаления:", parse_mode="HTML",
                                             reply_markup=KeyBoards.paidCoursesSelectorInline("course", "delete",
                                                                                              state_data[
                                                                                                  "category_parent"],
                                                                                              state_data[
                                                                                                  "category_current"]))
            return

        if callback.data == "paid_courses_course_edit" or callback.data == "edit_courses_set_desc_paid":
            await state.update_data(course_action="edit")
            try:
                await callback.message.edit_text("Выбери курс в категории для изменения:", parse_mode="HTML",
                                                 reply_markup=KeyBoards.paidCoursesSelectorInline("course",
                                                                                                  "edit"))
            except:
                await callback.message.answer("Выбери курс в категории для изменения:", parse_mode="HTML",
                                                 reply_markup=KeyBoards.paidCoursesSelectorInline("course", "edit"))

            return

        if callback.data.startswith("paid_courses_course_select_category_") and "course_action" in state_data and \
                state_data["course_action"] == "edit":
            category = int(callback.data.split("paid_courses_course_select_category_")[1])
            new = db.CourseCategory.select().where(db.CourseCategory.id == category).get()
            old = None if new == None or new.parent == None else db.CourseCategory.select().where(
                db.CourseCategory.id == new.parent).get()

            await state.update_data(category_parent=old, category_current=new)
            await callback.message.edit_text("Выбери курс в категории для изменения:", parse_mode="HTML",
                                             reply_markup=KeyBoards.paidCoursesSelectorInline("course", "edit", old,
                                                                                              new))
            return

        if callback.data.startswith("paid_courses_course_edit_course_") and "course_action" in state_data and \
                state_data["course_action"] == "edit":
            course = int(callback.data.split("paid_courses_course_edit_course_")[1])
            edit: db.Course = db.Course.select().where(db.Course.id == course).get()
            category: db.CourseCategory = db.CourseCategory.select().where(db.CourseCategory.id == edit.category).get()

            edit_message = await callback.message.edit_text(
                f"Название: {edit.name}\nОписание: {edit.description}\n"
                f"Категория: {category.name}\nКанал: {edit.channel}"
                f"\nСкидка: {edit.discount}%\nВыбери действие для изменения:", parse_mode="HTML",
                reply_markup=KeyBoards.editPaidCourseSelectActionsSelectorInline())
            await state.update_data(edit_message=edit_message, course=edit, category=category)
            return

        if callback.data.startswith('edit_category_set_photo_paid_'):
            new = callback.data.split('edit_category_set_photo_paid_')[1]
            if new != '-1':
                new = db.CourseCategory.select().where(db.CourseCategory.id == new).get()
                old = None if new == None or new.parent == None else db.CourseCategory.select().where(
                    db.CourseCategory.id == new.parent).get()
                await state.update_data(category_parent=old, category_action="edit", category=new,
                                        edit_message=callback.message)
                state_data = await state.get_data()

        if callback.data.startswith('edit_category_set_desc_paid_'):
            new = callback.data.split('edit_category_set_desc_paid_')[1]
            if int(new) != -1:
                new = db.CourseCategory.select().where(db.CourseCategory.id == new).get()
                old = None if new == None or new.parent == None else db.CourseCategory.select().where(
                    db.CourseCategory.id == new.parent).get()
                await state.update_data(category_parent=old, category_action="edit", category=new,
                                        edit_message=callback.message)
                state_data = await state.get_data()

        if ("category_action" in state_data and state_data["category_action"] == "edit" and
                "category" in state_data and "category_parent" in state_data):
            category: db.CourseCategory = state_data["category"]
            category_parent: db.CourseCategory = state_data["category_parent"]

            if callback.data == "paid_courses_category_save":
                await state.update_data(course=None, category=None)
                await callback.message.edit_text("Выбери категорию в категории для изменения:", parse_mode="HTML",
                                                 reply_markup=KeyBoards.paidCoursesSelectorInline(
                                                     "category", "edit",
                                                     None if category_parent is None else category_parent.id,
                                                     category.id))
                return

            if callback.data == "paid_courses_category_edit_name":
                await state.set_state(States.CategoryEdit.name)
                await callback.message.edit_text("Введи новое название для категории:")
                return

            if (callback.data == "paid_courses_category_edit_description" or
                    callback.data.startswith("edit_category_set_desc_paid_")):
                await state.set_state(States.CategoryEdit.description)
                try:
                    await callback.message.edit_text("Введи новое описание для категории:")
                except:
                    await callback.message.answer("Введи новое описание для категории:")
                return

            if (callback.data == "paid_courses_category_edit_media" or
                    callback.data.startswith('edit_category_set_photo_paid_')):
                await state.set_state(States.CategoryEdit.media)
                try:
                    await callback.message.edit_text("Отправь новую медию для категории:")
                except:
                    await callback.message.answer("Отправь новую медию для категории:")
                return

            if callback.data == "paid_courses_category_edit_toggle":
                category: db.CourseCategory = state_data["category"]
                parent_category: db.CourseCategory = state_data["category_parent"]

                category.enabled = not category.enabled

                await edit_message.edit_text(
                    f"Название: {category.name}\nОписание: {category.description}\n"
                    f"Категория: {'Глобальная' if parent_category is None else parent_category.name}"
                    # f"\nСкидка: {category.discount}%"
                    "\nВыбери действие для изменения:"
                    , parse_mode="HTML",
                    reply_markup=KeyBoards.editPaidCategorySelectActionsSelectorInline(category))
                return
            return

        if callback.data.startswith("edit_course_set_photo_paid_"):
            course: int | str = callback.data.split('edit_course_set_photo_paid_')[1]
            await state.update_data(course_action='edit', course=course)
            state_data = await state.get_data()

        if callback.data.startswith("edit_course_set_cost_paid_"):
            course: int | str = callback.data.split('edit_course_set_cost_paid_')[1]
            await state.update_data(course_action='edit', course=course)
            state_data = await state.get_data()

        if callback.data.startswith("edit_course_set_channel_paid_"):
            course: int | str = callback.data.split('edit_course_set_channel_paid_')[1]
            await state.update_data(course_action='edit', course=course)
            state_data = await state.get_data()

        if callback.data.startswith("edit_course_set_desc_paid_"):
            course: int | str = callback.data.split('edit_course_set_desc_paid_')[1]
            await state.update_data(course_action='edit', course=course)
            state_data = await state.get_data()

        if callback.data.startswith("edit_course_product_discount_paid_"):
            course: int | str = callback.data.split('edit_course_product_discount_paid_')[1]
            await state.update_data(course_action='edit', course=course)
            state_data = await state.get_data()

        if ("course_action" in state_data and state_data["course_action"] == "edit" and "course" in state_data and
                ("category" in state_data or callback.data.startswith('edit_course_'))):
            course: db.Course = state_data["course"]

            if callback.data == "paid_courses_save":
                course.save()
                await state.update_data(course=None, category=None)
                await callback.message.edit_text("Выбери курс в категории для изменения:", parse_mode="HTML",
                                                 reply_markup=KeyBoards.paidCoursesSelectorInline(
                                                     "course", "edit", state_data["category_parent"],
                                                     state_data["category_current"]))
                return

            if callback.data == "paid_courses_edit_name":
                await state.set_state(States.CourseEdit.name)
                await callback.message.edit_text("Введи новое название для курса:")
                return

            if (callback.data == "paid_courses_edit_description" or
                    callback.data.startswith('edit_course_set_desc_paid_')):
                await state.set_state(States.CourseEdit.description)
                try:
                    edit_message = await callback.message.edit_text("Введи новое описание для курса:")
                except:
                    edit_message = await callback.message.answer("Введи новое описание для курса:")
                await state.update_data(edit_message=edit_message)
                return

            if callback.data == "paid_courses_edit_category":
                try:
                    await callback.message.edit_text("Выбери новую категорию для курса:",
                                                     reply_markup=KeyBoards.paidCoursesSelectorInline(
                                                         "category", "edit_course",
                                                         select_only_empty_categories=True))
                except:
                    await callback.message.answer("Выбери новую категорию для курса:",
                                                     reply_markup=KeyBoards.paidCoursesSelectorInline(
                                                         "category", "edit_course",
                                                         select_only_empty_categories=True))
                return

            if callback.data.startswith(
                    "paid_courses_category_select_category_") and not "category_action" in state_data:
                category = int(callback.data.split("paid_courses_category_select_category_")[1])
                new = db.CourseCategory.select().where(db.CourseCategory.id == category).get()
                old = None if new == None or new.parent == None else db.CourseCategory.select().where(
                    db.CourseCategory.id == new.parent).get()

                await state.update_data(category_parent=old, category_current=new)
                await callback.message.edit_text("Выбери новую категорию для курса:", parse_mode="HTML",
                                                 reply_markup=KeyBoards.paidCoursesSelectorInline(
                                                     "category", "edit_course", old, new,
                                                     select_only_empty_categories=True))
                return

            if callback.data == "paid_courses_category_edit_course_finish":
                course.category = state_data["category_current"]
                category = state_data["category_current"]
                await callback.message.edit_text(
                    f"Название: {course.name}\nОписание: {course.description}\n"
                    f"Категория: {category.name}\nКанал: {course.channel}"
                    f"\nСкидка: {course.discount}%\nВыбери действие для изменения:", parse_mode="HTML",
                    reply_markup=KeyBoards.editPaidCourseSelectActionsSelectorInline())
                return

            if (callback.data == "paid_courses_edit_channel" or
                    callback.data.startswith('edit_course_set_channel_paid_')):
                await state.set_state(States.CourseEdit.channel)
                try:
                    edit_message = await callback.message.edit_text("Перешлите сообщение/айди с канала:")
                except:
                    edit_message = await callback.message.answer("Перешлите сообщение/айди с канала:")
                await state.update_data(edit_message=edit_message)
                return

            if (callback.data == "paid_courses_edit_discount" or
                    callback.data.startswith('edit_course_product_discount_paid_')):
                await state.set_state(States.CourseEdit.discount)
                try:
                    edit_message = await callback.message.edit_text("Введите новую скидку в процетах:\nНапример: 15%")
                except:
                    edit_message = await callback.message.answer("Введите новую скидку в процетах:\nНапример: 15%")
                await state.update_data(edit_message=edit_message)
                return

            if callback.data == "paid_courses_edit_media" or callback.data.startswith('edit_course_set_photo_paid_'):
                await state.set_state(States.CourseEdit.media)
                try:
                    edit_message = await callback.message.edit_text("Отправьте новую медию:")
                except:
                    edit_message = await callback.message.answer("Отправьте новую медию:")
                await state.update_data(edit_message=edit_message)
                return

            if callback.data.startswith('edit_course_set_cost_paid_'):
                await state.set_state(States.CourseEdit.price_single)
                try:
                    edit_message = await callback.message.edit_text("Отправьте новую цену:")
                except:
                    edit_message = await callback.message.answer("Отправьте новую цену:")
                await state.update_data(edit_message=edit_message)
                return

        await MessageHelper.state_clear_light(state)

    if callback.data == "settings":
        await callback.message.edit_text("Выбери категорию настройки:", parse_mode="HTML",
                                         reply_markup=KeyBoards.settingsSelectorInline())
        return

    if callback.data == "settings_buttons":
        await callback.message.edit_text("Выбираем кнопку для настройки:", parse_mode="HTML",
                                         reply_markup=KeyBoards.settingsLocaleSelectorInline("buttons"))
        return

    if callback.data.startswith("settings_buttons_"):
        msg_id: str = callback.data.split("settings_buttons_")[1].replace("_edit", "").replace("_reset", "")

        await state.update_data(msg_id=msg_id,
                                category="buttons",
                                edit_message=callback.message)
        if callback.data.endswith("edit"):
            await state.set_state(States.EditBotMessage.waiting_value)
            await callback.message.edit_text("Введите новый текст:", parse_mode="HTML",
                                             reply_markup=KeyBoards.cancelInline())
            return
        if callback.data.endswith("reset"):
            if not Cache.cachedLocale("btn-" + msg_id):
                await callback.answer(f"Невозможно сбросить теста для \"{msg_id}\", потому что он не найден.")
                return
            locale.set_message(msg_id, Cache.cachedLocale("btn-" + msg_id).default)
            try:
                await callback.message.edit_text(f"Сброшенный текст для \"{msg_id}\":", parse_mode="HTML",
                                                 reply_markup=KeyBoards.settingsLocaleEditInline("buttons", msg_id,
                                                                                                 locale.get_button(
                                                                                                     msg_id)))
            except:
                await callback.answer("Упс, ошибочка. Кажется это сообщение уже сброшенно.")
            return

        await callback.message.edit_text(f"Текущий текст для \"{msg_id}\":", parse_mode="HTML",
                                         reply_markup=KeyBoards.settingsLocaleEditInline("buttons", msg_id,
                                                                                         locale.get_button(msg_id)))
        return

    if callback.data == "managebans":
        await callback.message.edit_text("Выбираем действие:", parse_mode="HTML",
                                         reply_markup=KeyBoards.manageBansSelectorInline())
        return

    if callback.data == "ban":
        await callback.message.edit_text("Выбираем действие для бана! 🌚", parse_mode="HTML",
                                         reply_markup=KeyBoards.banSelectorInline())
        return

    if callback.data == "ban_all":
        await callback.message.edit_text("Вы точно хотите <b>ЗАБАНИТЬ ВСЕХ</b>?", parse_mode="HTML",
                                         reply_markup=KeyBoards.confirm_ban_all())
        return

    if callback.data == "ban_all_confirm":
        await callback.message.edit_text("Блокировка всех пользователей в процессе, подождите.")
        banned = 0
        already_banned = 0

        for user in db.User.select().where(db.User.admin == False):
            if user.banned:
                already_banned += 1
                continue

            user.banned = True
            user.save()

            banned += 1
        await Logs.logBan(bot, None, user, True)

        await callback.message.edit_text(f"Все пользователи забанены:"
                                         f"\n Было в бане: {already_banned}"
                                         f"\n Новые в бане: {banned}"
                                         f"\n Всего: {banned + already_banned}", parse_mode="HTML",
                                         reply_markup=KeyBoards.backToAdminPanelInline())
        return

    if callback.data == "ban_user":
        await state.set_state(States.manageBanMember.selectUser)
        edit_message = await callback.message.edit_text("Укажите айди/ссылку/тег пользователя:", parse_mode="HTML",
                                                        reply_markup=KeyBoards.cancelInline("ban"))
        await state.update_data(action="ban",
                                edit_message=edit_message)
        return

    if callback.data == "ban_users":
        await state.set_state(States.manageBanMember.selectUser)
        edit_message = await callback.message.edit_text("Укажите айди/ссылку/тег пользователя:", parse_mode="HTML",
                                                        reply_markup=KeyBoards.cancelInline("ban"))
        await state.update_data(action="ban_users",
                                edit_message=edit_message)
        return

    if callback.data == "unban":
        await callback.message.edit_text("Выбираем действие для разбана! 🌞", parse_mode="HTML",
                                         reply_markup=KeyBoards.unbanSelectorInline())
        return

    if callback.data == "unban_all":
        await callback.message.edit_text("Вы точно хотите <b>РАЗБАНИТЬ ВСЕХ</b>?", parse_mode="HTML",
                                         reply_markup=KeyBoards.confirm_unbanban_all())
        return

    if callback.data == "unban_all_confirm":
        await callback.message.edit_text("Разблокировка всех пользователей в процессе, подождите.")
        unbanned = 0
        already_unbanned = 0

        for user in db.User.select().where(db.User.admin == False):
            if not user.banned:
                already_unbanned += 1
                continue

            user.banned = False
            user.save()

            unbanned += 1
        await Logs.logUnban(bot, None, user, True)

        await callback.message.edit_text(f"Все пользователи разблокированны:"
                                         f"\n Было в бане: {unbanned}"
                                         f"\n Уже разбанены: {already_unbanned}"
                                         f"\n Всего: {unbanned + already_unbanned}", parse_mode="HTML",
                                         reply_markup=KeyBoards.backToAdminPanelInline())
        return

    if callback.data == "unban_user":
        await state.set_state(States.manageBanMember.selectUser)
        edit_message = await callback.message.edit_text("Укажите айди/ссылку/тег пользователя:", parse_mode="HTML",
                                                        reply_markup=KeyBoards.cancelInline("unban"))
        await state.update_data(action="unban",
                                edit_message=edit_message)
        return

    if callback.data == "unban_users":
        await state.set_state(States.manageBanMember.selectUser)
        edit_message = await callback.message.edit_text("Укажите айди/ссылку/тег пользователя:", parse_mode="HTML",
                                                        reply_markup=KeyBoards.cancelInline("unban"))
        await state.update_data(action="unban_users",
                                edit_message=edit_message)
        return

    if callback.data.startswith("mailing_"):
        await state.update_data(mail_filters=callback.data.split("mailing_")[1],
                                edit_message=callback.message)
        await state.set_state(States.Mailing.message)
        await callback.message.edit_text("Введите/Перешлите сообщение для рассылки: ", parse_mode="HTML",
                                         reply_markup=KeyBoards.cancelInline())
        return

    if callback.data == "export_users":
        await callback.message.edit_text("Секунду, генерирую и отправляю CSV документ!", parse_mode="HTML",
                                         reply_markup=KeyBoards.backToAdminPanelInline())
        export_file: str = EXCEL.export_users(f"users_{user.id}_{datetime.now().strftime('%f')}")
        await callback.message.delete()
        await callback.message.answer_document(caption="CSV Экспорт пользователей готов!", parse_mode="HTML",
                                               document=BufferedInputFile.from_file(path=export_file),
                                               reply_markup=KeyBoards.backToAdminPanelInline())
        os.remove(export_file)
        return

    if callback.data == "export_balance_history":
        await callback.message.edit_text("Секунду, генерирую и отправляю CSV документ!", parse_mode="HTML",
                                         reply_markup=KeyBoards.backToAdminPanelInline())
        export_file: str = EXCEL.export_balance_history(f"balance_{user.id}_{datetime.now().strftime('%f')}")
        await callback.message.delete()
        await callback.message.answer_document(caption="CSV Экспорт истории балансов готов!", parse_mode="HTML",
                                               document=BufferedInputFile.from_file(path=export_file),
                                               reply_markup=KeyBoards.backToAdminPanelInline())
        os.remove(export_file)
        return

    if callback.data == "export_purchases_history":
        await callback.message.edit_text("Секунду, генерирую и отправляю CSV документ!", parse_mode="HTML",
                                         reply_markup=KeyBoards.backToAdminPanelInline())
        export_file: str = EXCEL.export_purchases_history(f"purchases_{user.id}_{datetime.now().strftime('%f')}")
        await callback.message.delete()
        await callback.message.answer_document(caption="CSV Экспорт истории покупок готов!", parse_mode="HTML",
                                               document=BufferedInputFile.from_file(path=export_file),
                                               reply_markup=KeyBoards.backToAdminPanelInline())
        os.remove(export_file)
        return

    if callback.data == "export_promocode":
        await callback.message.edit_text("Секунду, генерирую и отправляю CSV документ!", parse_mode="HTML",
                                         reply_markup=KeyBoards.backToAdminPanelInline())
        export_file: str = EXCEL.export_promocode(f"promocode_{user.id}_{datetime.now().strftime('%f')}")
        await callback.message.delete()
        await callback.message.answer_document(caption="CSV Экспорт промо-кодов готов!", parse_mode="HTML",
                                               document=BufferedInputFile.from_file(path=export_file),
                                               reply_markup=KeyBoards.backToAdminPanelInline())
        os.remove(export_file)
        return

    if callback.data == "free_courses":
        await callback.message.edit_text("Выбираем действие для бесплатных курсов:", parse_mode="HTML",
                                         reply_markup=KeyBoards.freeCoursesActionsSelectorInline())
        return

    if callback.data == "free_courses_create":
        await state.set_state(States.FreeCourseAction.name)
        edit_message = await callback.message.edit_text(
            "Введите название кнопки: (оно будет отображаться так-же и у пользователя)", parse_mode="HTML",
            reply_markup=KeyBoards.cancelInline())
        await state.update_data(action="create",
                                edit_message=edit_message)
        return

    if callback.data == "free_courses_delete":
        await state.set_state(States.FreeCourseAction.select_button)
        edit_message = await callback.message.edit_text("Выберите удаляемую кнопку:", parse_mode="HTML",
                                                        reply_markup=KeyBoards.freeCoursesListSelectorInline("delete"))
        await state.update_data(action="delete",
                                edit_message=edit_message)
        return

    if callback.data == "free_courses_edit":
        await state.set_state(States.FreeCourseAction.select_button)
        try:
            edit_message = await callback.message.edit_text(
                "Выберите изменяемую кнопку:", parse_mode="HTML",
                reply_markup=KeyBoards.freeCoursesListSelectorInline("edit"))
        except:
            edit_message = await callback.message.answer("Выберите изменяемую кнопку:", parse_mode="HTML",
                                                         reply_markup=KeyBoards.freeCoursesListSelectorInline("edit"))
        await state.update_data(action="edit",
                                edit_message=edit_message)
        return


# noinspection PyUnboundLocalVariable,PyComparisonWithNone,PySimplifyBooleanCheck,PyShadowingNames
@dp.message(lambda m: m and m.chat.type == ChatType.PRIVATE)
async def message(message: Message, state: FSMContext):
    global paymentapi
    userId = message.chat.id
    text = message.text

    try:
        user: db.User | None = db.User.get(db.User.id == userId)
    except:
        user = None

    if user is None:
        user = db.User.create(
            id=userId, username="Неизвестный" if message.from_user.username is None else message.from_user.username,
            captcha=CaptchaGenerator.generateCaptcha())
        # CaptchaGenerator.saveCaptcha(user.captcha, user.id)

    if user.banned:
        await message.answer(locale.get_message("banned_user"), parse_mode="HTML")
        return

    if user.captcha is not None:
        if user.captcha.lower() != text.lower():
            await message.answer(locale.get_message("captcha_wrong"), parse_mode="HTML")
            return

        user.captcha = None
        # CaptchaGenerator.deleteCaptcha(user.id)

        referral_user = None

        if user.from_referral != 0:
            referral_user = db.User.select().where(db.User.id == user.from_referral).get()

            if referral_user != None:
                referral_user.referrals += 1
                referral_user.balance += 10
                referral_user.save()

        await Logs.logStart(bot, user, referral_user)

        await message.answer(locale.get_message("captcha_accept"), parse_mode="HTML",
                             reply_markup=KeyBoards.captchaSuccessInline())
        user.save()
        return

    if user.username != "Неизвестный" if message.from_user.username is None else message.from_user.username:
        user.username = "Неизвестный" if message.from_user.username is None else message.from_user.username
        user.save()

    if not (await Checks.subscribed(bot, userId)):
        return

    curr_state: None | str = await state.get_state()

    if curr_state is not None:
        state_data = await state.get_data()
        try:
            edit_message: Message = state_data["edit_message"]
        except:
            print("edit_message not found in state data: #1845")

        if curr_state == States.Cart.waiting_check or curr_state == States.BalanceTopUp.waiting_check:
            await message.delete()

            save_path = f"data/media/temp/{Math.current_milli_time() * Math.randInt(2, 999)}.png"

            if not (await MessageHelper.download_photo(bot, message, save_path)):
                await edit_message.edit_caption(caption="Попробуйте снова отправить чек, в формате фото без сжатия")
                return

            uid = state_data['id']
            dst: str = f"data/media/payments/{uid}.png"

            if os.path.exists(dst):
                os.unlink(dst)

            os.rename(save_path, dst)
            data = paymentapi.payments[uid]

            try:
                await bot.send_photo(data['drop'].channel,
                                     caption=f"🧾 Чек: @{user.username} {user.id} пополнил баланс"
                                             f"\n\n📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                                             f"\n\n🏦 Банк: {MessageHelper.bank_display(state_data['bank'])}"
                                             f"\n💳 Номер карты/телефона: {data['card']}"
                                             f"\n💸 Сумма пополнения: {data['amount']} ₽"
                                             f"\n\nTransaction ID: <code>{uid}</code>",
                                     parse_mode="HTML",
                                     photo=Cache.cachedInputFile(f"data/media/payments/{uid}.png", "loose again.mp4"),
                                     reply_markup=KeyBoards.dropCheckAcceptorInline(uid))
            except TelegramBadRequest:
                await edit_message.edit_caption(caption="Свяжитесь с менеджером, произошла ошибка!")
                return

            await state.set_state()
            await edit_message.edit_caption(caption="Ожидайте одобрения вашей оплаты.")
            return

        if curr_state == States.SettingsMedia.media:
            await message.delete()

            save_path = f"data/media/temp/{Math.current_milli_time() * Math.randInt(2, 999)}.png"

            if not (await MessageHelper.download_photo(bot, message, save_path)):
                await edit_message.edit_text("Попробуйте снова отправить новую медию:")
                return

            dst: str = f"data/media/global/{state_data['action']}.png"

            if os.path.exists(dst):
                os.unlink(dst)

            os.rename(save_path, dst)
            Cache.cacheClear()
            await edit_message.edit_text(
                "Выбираем медию для настройки:", parse_mode="HTML",
                     reply_markup=None if state_data['cat'] == -1 else KeyBoards.settingsMediaSelectorInline())
            await state.clear()
            return

        if curr_state == States.SettingsBot.intValue:
            await message.delete()

            try:
                value: int = int(message.html_text.replace("%", ""))
            except:
                return

            action = state_data["action"]
            exec(f"import data.db as db\nset = db.getSettings()\nset.{action} = {value}\nset.save()")

            await edit_message.edit_text("Выбираем категорию бота:", reply_markup=KeyBoards.settingsBotSelectorInline())
            await state.clear()
            return

        if curr_state == States.DropCreate.name:
            await message.delete()
            await state.set_state(States.DropCreate.user)
            await state.update_data(drop_name=message.html_text)
            await edit_message.edit_text(
                "Введи айди/перешли сообщение с юзера дропа в тг для доступа к его сообщениям:")
            return

        if curr_state == States.DropCreate.user:
            await message.delete()

            try:
                if message.forward_from_chat != None:
                    channel = message.forward_from_chat.id
                else:
                    channel = int(message.text)
            except:
                await edit_message.edit_text(
                    "Это не число, введи/перешли айди/сообщение с юзера дропа в тг для доступа к его сообщениям:")
                return

            await state.update_data(drop_user=channel)
            await state.set_state(States.DropCreate.channel)
            await edit_message.edit_text("Введи айди/перешли сообщение с канала для поступления новых запросов оплаты:")
            return

        if curr_state == States.DropCreate.channel:
            await message.delete()

            try:
                if message.forward_from_chat != None:
                    channel = message.forward_from_chat.id
                else:
                    channel = int(message.text)
            except:
                await edit_message.edit_text(
                    "Это не число, введи/перешли айди/сообщение с канала для новых поступления новых запросов оплаты:")
                return

            await state.update_data(drop_channel=channel)
            await state.set_state(States.DropCreate.sber)
            await edit_message.edit_text("Введи реквизиты для оплаты по сберу:",
                                         reply_markup=KeyBoards.skipInline("settings_drops_create_tinkoff"))
            return

        if curr_state == States.DropCreate.sber:
            await message.delete()
            await state.update_data(drop_sber=message.html_text)
            await state.set_state(States.DropCreate.tinkoff)
            await edit_message.edit_text("Введи реквизиты для оплаты по тинькоффу:",
                                         reply_markup=KeyBoards.skipInline("settings_drops_create_raiffeisenbank"))
            return

        if curr_state == States.DropCreate.tinkoff:
            await message.delete()
            await state.update_data(drop_tinkoff=message.html_text)
            await state.set_state(States.DropCreate.raiffeisenbank)
            await edit_message.edit_text("Введи реквизиты для оплаты по райфайзену:",
                                         reply_markup=KeyBoards.skipInline("settings_drops_create_raiffeisenbank"))
            return

        if curr_state == States.DropCreate.raiffeisenbank:
            await message.delete()
            await state.update_data(drop_raiffeisenbank=message.html_text)
            await state.set_state(States.DropCreate.sbp)
            await edit_message.edit_text("Введи реквизиты для оплаты по сбп:",
                                         reply_markup=KeyBoards.skipInline("settings_drops_create_sbp"))
            return

        if curr_state == States.DropCreate.sbp:
            await message.delete()
            await state.update_data(drop_sbp=message.html_text)
            await state.set_state()
            await edit_message.edit_text("Завершить создание дропа?",
                                         reply_markup=KeyBoards.customInline("Завершить", "settings_drops_create_end"))
            return

        if curr_state == States.SubscribeChannelCreate.name:
            await message.delete()
            await state.update_data(sub_name=message.html_text)
            await state.set_state(States.SubscribeChannelCreate.channel)
            await edit_message.edit_text("Введи айди/перешли сообщение с канала на который нужно подписаться:")
            return

        if curr_state == States.SubscribeChannelCreate.channel:
            await message.delete()

            try:
                if message.forward_from_chat != None:
                    channel = message.forward_from_chat.id
                else:
                    channel = int(message.text)
            except:
                await edit_message.edit_text("Это не число, введи/перешли айди/сообщение с канала для нового курса:")
                return

            await state.set_state()
            db.SubscribeChannel.create(id=Math.current_milli_time() + len(db.SubscribeChannel.select()) + 1,
                                       name=state_data["sub_name"], channel=channel)
            await edit_message.edit_text("Выбираем канал для удаления или создаем новый:",
                                         reply_markup=KeyBoards.settingsBotSettingsSubscribeChannelSelectorInline())
            return

        if curr_state == States.LogsCreate.name:
            await message.delete()
            await state.set_state(States.LogsCreate.channel)
            await state.update_data(logs_name=message.html_text)
            await edit_message.edit_text(
                "Введи айди/перешли сообщение с канала в который будут поступать логи этого типа логов:")
            return

        if curr_state == States.LogsCreate.channel:
            await message.delete()
            try:
                if message.forward_from_chat != None:
                    channel = message.forward_from_chat.id
                else:
                    channel = int(message.text)
            except:
                await edit_message.edit_text("Это не число, введи/перешли айди/сообщение с канала для нового курса:")
                return
            await state.set_state()
            db.LogChannel.create(id=Math.current_milli_time() + len(db.LogChannel.select()) + 1,
                                 name=state_data["logs_name"], channel=channel, type=state_data["logs_category"])
            await edit_message.edit_text("Выбираем канал для удаления или создаем новый:",
                                         reply_markup=KeyBoards.settingsLogsChannelSelectorInline(
                                             state_data["logs_category"]))
            return

        if curr_state == States.EditBotMessage.waiting_value.state:
            await state.clear()

            category: str | int = state_data["category"]
            msg_id: str | int = state_data["msg_id"]

            if msg_id == 'None':
                if category == "messages":
                    msg_id = message.message_id
                    locale.set_message(msg_id, message.html_text)
                else:
                    locale.set_button(msg_id, message.html_text)
            else:
                if category == "messages":
                    locale.set_message(msg_id, message.html_text)
                else:
                    locale.set_button(msg_id, message.html_text)

            await message.delete()
            await edit_message.edit_text("Сохранено!\nВыберите следующую цель для изменения:", parse_mode="HTML",
                                         reply_markup=KeyBoards.settingsLocaleSelectorInline(category))
            return

        if curr_state == States.Profile.promocode.state:
            if MessageHelper.is_menu_used(message.text):
                await state.set_state()
            else:
                await message.delete()

                try:
                    promocode: db.PromoCode | None = db.PromoCode.select().where(
                        (db.PromoCode.code == message.text) | (db.PromoCode.name == message.text)).get()
                except:
                    promocode = None

                if promocode is None or (
                        0 < promocode.max_usages <= promocode.used) or not promocode.enabled:
                    await edit_message.edit_caption(caption=locale.get_message("promo_not_search"), parse_mode="HTML",
                                                    reply_markup=KeyBoards.backToProfileInline())
                    return

                await state.set_state()

                promocode.used += 1
                promocode.save()

                await state.update_data(promo=None)
                if promocode.type == "discount":
                    await state.update_data(promocode=promocode)
                    await edit_message.edit_caption(
                        caption=locale.get_message("promo_discount2", discount=promocode.discount),
                        parse_mode="HTML", reply_markup=KeyBoards.backToProfileInline())
                elif promocode.type == "channel":
                    await Logs.logPromoUsage(bot, user, promocode)
                    await edit_message.edit_caption(caption=locale.get_message("secretchannel_promo", invite_channel=(
                        await bot.create_chat_invite_link(promocode.channel, member_limit=1)).invite_link),
                                                    parse_mode="HTML", reply_markup=KeyBoards.backToProfileInline())
                elif promocode.type == "balance":
                    user.balance += promocode.amount
                    await Logs.logPromoUsage(bot, user, promocode)
                    user.save()
                    await edit_message.edit_caption(
                        caption=locale.get_message("activate_promo_bal", amount=promocode.amount),
                        parse_mode="HTML", reply_markup=KeyBoards.backToProfileInline())
                return

        if curr_state == States.CourseSelection.promocode.state:
            if MessageHelper.is_menu_used(message.text):
                await state.set_state()
            else:
                await message.delete()

                try:
                    promocode: db.PromoCode | None = db.PromoCode.select().where(
                        (db.PromoCode.code == message.text) | (db.PromoCode.name == message.text)).get()
                except:
                    promocode = None

                if promocode is None or (
                        promocode.max_usages < 0 and promocode.used >= promocode.max_usages) or not promocode.enabled:
                    await edit_message.edit_caption(caption=locale.get_message("promo_not_search"), parse_mode="HTML",
                                                    reply_markup=KeyBoards.cancelInline())
                    return

                await state.set_state()

                promocode.used += 1
                promocode.save()

                if promocode.type == "discount":
                    await state.update_data(promocode=promocode)
                    await edit_message.edit_caption(
                        caption=locale.get_message("promo_discount", discount=promocode.discount),
                        parse_mode="HTML", reply_markup=KeyBoards.cancelInline(
                            f"paid_courses_select_course_{state_data['course'].id}"))
                elif promocode.type == "channel":
                    await Logs.logPromoUsage(bot, user, promocode)
                    await edit_message.edit_caption(caption=locale.get_message("secretchannel_promo", invite_channel=(
                        await bot.create_chat_invite_link(promocode.channel, member_limit=1)).invite_link),
                                                    parse_mode="HTML", reply_markup=KeyBoards.cancelInline(
                            f"paid_courses_select_course_{state_data['course'].id}"))
                elif promocode.type == "balance":
                    user.balance += promocode.amount
                    await Logs.logPromoUsage(bot, user, promocode)
                    user.save()
                    await edit_message.edit_caption(
                        caption=locale.get_message("activate_promo_bal", amount=promocode.amount),
                        parse_mode="HTML", reply_markup=KeyBoards.cancelInline(
                            f"paid_courses_select_course_{state_data['course'].id}"))

                return

        if curr_state == States.Mailing.message.state:
            await edit_message.delete()
            edit_message = await message.reply("Точно отправить это сообщение?", parse_mode="HTML",
                                               reply_markup=KeyBoards.confirmMail())
            await state.update_data(edit_message=edit_message,
                                    message=message)
            await state.set_state(States.Mailing.confirm)
            return

        if curr_state == States.PromoCodeCreate.name.state:
            await state.update_data(promocode_name=message.text)
            await message.delete()
            await state.set_state(States.PromoCodeCreate.maxUsages)
            await edit_message.edit_text("Максимальное количество использований промо: (-1 = бесконечно)",
                                         parse_mode="HTML", reply_markup=KeyBoards.cancelInline())
            return

        if curr_state == States.CategoryEdit.name.state:
            await message.delete()
            category: db.CourseCategory = state_data["category"]
            parent_category: db.CourseCategory = state_data["category_parent"]

            category.name = message.html_text

            await state.set_state()
            await edit_message.edit_text(
                f"Название: {category.name}\nОписание: {category.description}\n"
                f"Категория: {'Глобальная' if parent_category is None else parent_category.name}"
                # f"\nСкидка: {category.discount}%"
                "\nВыбери действие для изменения:"
                , parse_mode="HTML",
                reply_markup=KeyBoards.editPaidCategorySelectActionsSelectorInline(category))
            return

        if curr_state == States.CategoryEdit.description.state:
            await message.delete()
            category: db.CourseCategory = state_data["category"]
            parent_category: db.CourseCategory = state_data["category_parent"]

            category.description = message.html_text
            cat = db.CourseCategory
            cat.update(description=message.html_text).where(cat.id == category.id).execute()

            await state.set_state()
            try:
                await edit_message.edit_text(
                    f"Название: {category.name}\nОписание: {category.description}\n"
                    f"Категория: {'Глобальная' if parent_category is None else parent_category.name}"
                    # f"\nСкидка: {category.discount}%"
                    "\nВыбери действие для изменения:"
                    , parse_mode="HTML",
                    reply_markup=KeyBoards.editPaidCategorySelectActionsSelectorInline(category))
            except:
                await message.answer(
                    f"Название: {category.name}\nОписание: {category.description}\n"
                    f"Категория: {'Глобальная' if parent_category is None else parent_category.name}"
                    # f"\nСкидка: {category.discount}%"
                    "\nВыбери действие для изменения:"
                    , parse_mode="HTML",
                    reply_markup=KeyBoards.editPaidCategorySelectActionsSelectorInline(category))
            return

        if curr_state == States.CategoryEdit.media:
            await message.delete()
            name = f'{Math.current_milli_time() * Math.randInt(2, 999)}.png'
            save_path = f"data/media/temp/{name}"

            if not (await MessageHelper.download_photo(bot, message, save_path)):
                await edit_message.edit_text("Попробуйте снова отправить медию для категории:")
                return

            category: db.CourseCategory = state_data["category"]
            parent_category: db.CourseCategory = state_data["category_parent"]

            if category.media and os.path.exists(str(category.media)):
                os.unlink(category.media)
            if category.media is None:
                category.media = f'data/media/category/{name}'

            Cache.cacheClear()
            try:
                os.rename(save_path, str(category.media))
            except:
                pass

            dbcat = db.CourseCategory
            dbcat.update(media=str(category.media)).where(dbcat.id == category.id).execute()

            await state.set_state()
            try:
                await edit_message.edit_text(
                    f"Название: {category.name}\nОписание: {category.description}\n"
                    f"Категория: {'Глобальная' if parent_category is None else parent_category.name}"
                    # f"\nСкидка: {category.discount}%"
                    "\nВыбери действие для изменения:"
                    , parse_mode="HTML",
                    reply_markup=KeyBoards.editPaidCategorySelectActionsSelectorInline(category))
            except:
                await message.answer(
                    f"Название: {category.name}\nОписание: {category.description}\n"
                    f"Категория: {'Глобальная' if parent_category is None else parent_category.name}"
                    # f"\nСкидка: {category.discount}%"
                    "\nВыбери действие для изменения:"
                    , parse_mode="HTML",
                    reply_markup=KeyBoards.editPaidCategorySelectActionsSelectorInline(category))
            return

        if curr_state == States.CourseEdit.name:
            await message.delete()
            course: db.Course = state_data["course"]
            category: db.CourseCategory = state_data["category"]
            course.name = message.html_text

            await state.set_state()
            await edit_message.edit_text(
                f"Название: {course.name}\nОписание: {course.description}\n"
                f"Категория: {category.name}\nКанал: {course.channel}"
                f"\nСкидка: {course.discount}%\nВыбери действие для изменения:", parse_mode="HTML",
                reply_markup=KeyBoards.editPaidCourseSelectActionsSelectorInline())
            return

        if curr_state == States.CourseEdit.description:
            await message.delete()
            if 'category' not in state_data:
                course: db.Course = db.Course  # NOQA
                course: db.Course = course.select().where(course.id == state_data["course"])[0]
                category: db.CourseCategory = db.CourseCategory  # NOQA
                category: db.CourseCategory = category.select().where(category.id == course.category)[0]
            else:
                course: db.Course = state_data["course"]
                category: db.CourseCategory = state_data["category"]
            course.description = message.html_text
            course.save()

            await state.set_state()
            await edit_message.edit_text(
                f"Название: {course.name}\nОписание: {course.description}\nКатегория: {category.name}\n"
                f"Канал: {course.channel}"
                f"\nСкидка: {course.discount}%\nВыбери действие для изменения:", parse_mode="HTML",
                reply_markup=KeyBoards.editPaidCourseSelectActionsSelectorInline())
            return

        if curr_state == States.CourseEdit.price:
            await message.delete()
            category: int = int(state_data["category"])

            try:
                new_price = int(message.text)
                if new_price <= 0:
                    raise ValueError
            except:
                await edit_message.edit_text("Это не число, введи новую стоимость категории:")
                return

            c = db.Course
            if category >= 0:
                parents = recursiveParentIDS(category)
                for i in parents:
                    c.update(price=new_price).where(c.category == i).execute()
                    pass
            else:
                parents = c.select()
                c.update(price=new_price).execute()

            await state.set_state()
            await edit_message.edit_text(f'✅ Вы успешно поменяли цену {len(parents)} курсам на {new_price}')
            return

        if curr_state == States.CategoryEdit.discount:
            await message.delete()
            category: int = int(state_data["category"])

            try:
                new_discount = int(message.text.replace('%', ''))
                print(message.text, new_discount)
                if new_discount < 0:
                    raise ValueError
            except:
                await edit_message.edit_text("Это не число, введи новую скидку категории:")
                return

            courses = db.Course
            if category >= 0:
                parents = recursiveParentIDS(category)
                for i in parents:
                    courses.update(discount=new_discount).where(courses.category == i).execute()
                    pass
            else:
                parents = courses.select()
                courses.update(discount=new_discount).execute()

            await state.set_state()
            await edit_message.edit_text(f'✅ Вы успешно поменяли скидку {len(parents)} курсам на {new_discount}')
            return

        if curr_state == States.CourseEdit.channel:
            await message.delete()
            if 'category' not in state_data:
                course: db.Course = db.Course  # NOQA
                course: db.Course = course.select().where(course.id == state_data["course"])[0]
                category: db.CourseCategory = db.CourseCategory  # NOQA
                category: db.CourseCategory = category.select().where(category.id == course.category)[0]
            else:
                course: db.Course = state_data["course"]
                category: db.CourseCategory = state_data["category"]

            try:
                if message.forward_from_chat != None:
                    course.channel = message.forward_from_chat.id
                else:
                    course.channel = int(message.text)
            except:
                await edit_message.edit_text("Это не число, введи/перешли айди/сообщение с канала для курса:")
                traceback.print_exc()
                return
            course.save()

            await state.set_state()
            await edit_message.edit_text(
                f"Название: {course.name}\nОписание: {course.description}\nКатегория: {category.name}\n"
                f"Канал: {course.channel}"
                f"\nСкидка: {course.discount}%\nВыбери действие для изменения:", parse_mode="HTML",
                reply_markup=KeyBoards.editPaidCourseSelectActionsSelectorInline())
            return

        if curr_state == States.CourseEdit.discount:
            await message.delete()
            if 'category' not in state_data:
                course: db.Course = db.Course  # NOQA
                course: db.Course = course.select().where(course.id == state_data["course"])[0]
                category: db.CourseCategory = db.CourseCategory  # NOQA
                category: db.CourseCategory = category.select().where(category.id == course.category)[0]
            else:
                course: db.Course = state_data["course"]
                category: db.CourseCategory = state_data["category"]

            try:
                course.discount = int(message.text.replace("%", ""))
            except:
                await edit_message.edit_text("Это не число, введи новую скидку для курса:")
                return
            course.save()

            await state.set_state()
            await edit_message.edit_text(
                f"Название: {course.name}\nОписание: {course.description}\nКатегория: {category.name}\n"
                f"Канал: {course.channel}"
                f"\nСкидка: {course.discount}%\nВыбери действие для изменения:", parse_mode="HTML",
                reply_markup=KeyBoards.editPaidCourseSelectActionsSelectorInline())
            return

        if curr_state == States.CourseEdit.media:
            await message.delete()
            if 'category' not in state_data:
                course: db.Course = db.Course  # NOQA
                course: db.Course = course.select().where(course.id == state_data["course"])[0]
                category: db.CourseCategory = db.CourseCategory  # NOQA
                category: db.CourseCategory = category.select().where(category.id == course.category)[0]
            else:
                course: db.Course = state_data["course"]
                category: db.CourseCategory = state_data["category"]
            save_path = f"data/media/course/{course.id}.png"

            if not (await MessageHelper.download_photo(bot, message, save_path)):
                await edit_message.edit_text("Попробуйте снова отправить медию для курса:")
                return

            await state.set_state()
            await edit_message.edit_text(
                f"Название: {course.name}\nОписание: {course.description}\nКатегория: {category.name}\n"
                f"Канал: {course.channel}"
                f"\nСкидка: {course.discount}%\nВыбери действие для изменения:", parse_mode="HTML",
                reply_markup=KeyBoards.editPaidCourseSelectActionsSelectorInline())
            return

        if curr_state == States.CourseEdit.price_single:
            await message.delete()
            if 'category' not in state_data:
                course: db.Course = db.Course  # NOQA
                course: db.Course = course.select().where(course.id == state_data["course"])[0]
                category: db.CourseCategory = db.CourseCategory  # NOQA
                category: db.CourseCategory = category.select().where(category.id == course.category)[0]
            else:
                course: db.Course = state_data["course"]
                category: db.CourseCategory = state_data["category"]

            try:
                new_price = int(message.text)
                if new_price <= 0:
                    raise ValueError
            except:
                await edit_message.edit_text("Это не число, введи новую стоимость курса:")
                return

            c = db.Course
            c.update(price=new_price).where(c.category == category.id).execute()

            await state.set_state()
            await edit_message.edit_text(f'✅ Вы успешно поменяли цену курсу {course.name} на {new_price}')
            return

        if curr_state == States.CourseCreate.name:
            await message.delete()
            await state.set_state(States.CourseCreate.description)
            if 'rto' in state_data:
                await state.update_data(course_name=message.html_text, rto=state_data['rto'])
            else:
                await state.update_data(course_name=message.html_text)
            await edit_message.edit_text("Введи описание для нового курса:")
            return

        if curr_state == States.CourseCreate.description:
            await message.delete()
            await state.set_state(States.CourseCreate.price)
            if 'rto' in state_data:
                await state.update_data(course_description=message.html_text, rto=state_data['rto'])
            else:
                await state.update_data(course_description=message.html_text)
            await edit_message.edit_text("Введи стоимость нового курса:")
            return

        if curr_state == States.CourseCreate.price:
            try:
                await message.delete()
            except:
                pass
            try:
                price = int(message.text)
            except:
                try:
                    await edit_message.edit_text("Это не число, введи стоимость нового курса:")
                except:
                    await message.answer("Это не число, введи стоимость нового курса:")
                return

            await state.set_state(States.CourseCreate.channel)
            if 'rto' in state_data:
                await state.update_data(course_price=price, rto=state_data['rto'])
            else:
                await state.update_data(course_price=price)
            try:
                await edit_message.edit_text("Введи/Перешли айди/сообщения с канала для нового курса:")
            except:
                await message.answer("Введи/Перешли айди/сообщения с канала для нового курса:")
            return

        if curr_state == States.CourseCreate.channel:
            await message.delete()
            try:
                if message.forward_from_chat != None:
                    channel = message.forward_from_chat.id
                else:
                    channel = int(message.text)
            except:
                await edit_message.edit_text("Это не число, введи/перешли айди/сообщение с канала для нового курса:")
                return

            await state.set_state(States.CourseCreate.discount)
            if 'rto' in state_data:
                await state.update_data(course_channel=channel, rto=state_data['rto'])
            else:
                await state.update_data(course_channel=channel)
            await edit_message.edit_text("Введи скидку в процентах для нового курса:\nНапример: 99%")
            return

        if curr_state == States.CourseCreate.discount:
            await message.delete()
            try:
                discount = int(message.text.replace("%", ""))
            except:
                await edit_message.edit_text("Это не число, введи скидку для нового курса:")
                return

            await state.set_state(States.CourseCreate.media)
            if 'rto' in state_data:
                await state.update_data(course_discount=discount, rto=state_data['rto'])
            else:
                await state.update_data(course_discount=discount)
            await edit_message.edit_text("Отправьте медию для нового курса:")
            return

        if curr_state == States.CourseCreate.media:
            await message.delete()
            save_path = f"data/media/temp/{Math.current_milli_time() * Math.randInt(2, 999)}.png"

            if not (await MessageHelper.download_photo(bot, message, save_path)):
                await edit_message.edit_text("Попробуйте снова отправить медию для нового курса:")
                return

            category: db.CourseCategory = state_data["course_category"]
            id = Math.current_milli_time() + len(db.Course.select()) + 1
            course: db.Course = db.Course.create(id=id,
                                                 name=state_data["course_name"],
                                                 description=state_data["course_description"], category=category,
                                                 price=state_data["course_price"], channel=state_data["course_channel"],
                                                 discount=state_data["course_discount"],
                                                 media=f"data/media/course/{id}.png")
            os.rename(save_path, course.media)

            await state.clear()
            if 'rto' in state_data:
                category: int = int(state_data['rto'])
                course_category: db.CourseCategory = db.CourseCategory.select().where(
                    db.CourseCategory.id == category).get()
                await state.update_data(course_category=course_category)

                await edit_message.answer_photo(
                    photo=Cache.cachedInputFile("data/media/global/courses.png" if course_category.media is None else
                                                course_category.media,"loose again.mp4"),
                    caption=None if not course_category.description else
                    course_category.description, parse_mode="HTML",
                    reply_markup=KeyBoards.coursesInline(course_category.parent, course_category.id, user))
                return
            await edit_message.edit_text(
                f"Новый курс создан! Вот его подробности:\n\nНазвание: {course.name}\n"
                f"Описание: {course.description}\nКатегория: {category.name}\nКанал: {course.channel}"
                f"\nСкидка: {course.discount}%", parse_mode="HTML",
                reply_markup=KeyBoards.cancelInline("paid_courses", course.id, cc=True))
            return

        if curr_state == States.PromoCodeEdit.maxUsages:
            try:
                maxUsages = int(message.text)
            except:
                await message.delete()
                return

            promocode: db.PromoCode = (await state.get_data())["promocode"]
            promocode.max_usages = maxUsages

            await message.delete()
            await state.set_state()

            await edit_message.edit_text(
                f"Название: {promocode.name}\nКод: <code>{promocode.code}</code>\nИспользований: "
                f"{promocode.used}/{promocode.max_usages}\nВключен: {'да' if promocode.enabled else 'нет'}\n" + str(
                    f"Канал: #<code>{promocode.channel}</code>" if promocode.type == "channel" else 
                    f"Скидка: {promocode.discount}%" if promocode.type == "discount" else 
                    f"Баланс: {promocode.amount}"
                ),
                parse_mode="HTML", reply_markup=KeyBoards.editPromoCodeSelectActionsSelectorInline(promocode))
            return

        if curr_state == States.PromoCodeEdit.value.state:
            promocode: db.PromoCode = (await state.get_data())["promocode"]

            text: str = message.text
            await message.delete()

            try:
                if promocode.type == "discount":
                    promocode.discount = int(text.replace("%", ""))
                elif promocode.type == "balance":
                    promocode.amount = int(text)
                elif promocode.type == "channel":
                    if message.forward_from_chat != None:
                        promocode.channel = message.forward_from_chat.id
                    else:
                        promocode.channel = int(text)
            except:
                return

            await state.set_state()
            await edit_message.edit_text(
                f"Название: {promocode.name}\nКод: <code>{promocode.code}</code>\nИспользований: "
                f"{promocode.used}/{promocode.max_usages}\nВключен: {'да' if promocode.enabled else 'нет'}\n" + str(
                    f"Канал: #<code>{promocode.channel}</code>" if promocode.type == "channel" else 
                    f"Скидка: {promocode.discount}%" if promocode.type == "discount" else 
                    f"Баланс: {promocode.amount}"
                ),
                parse_mode="HTML", reply_markup=KeyBoards.editPromoCodeSelectActionsSelectorInline(promocode))
            return

        if curr_state == States.PromoCodeCreate.maxUsages.state:
            try:
                maxUsages = int(message.text)
            except:
                await message.delete()
                return

            await state.update_data(promocode_max_usages=maxUsages)
            await message.delete()
            await state.set_state(States.PromoCodeCreate.type)
            await edit_message.edit_text("Выбери тип промо-кода", parse_mode="HTML",
                                         reply_markup=KeyBoards.promoCodeTypeSelectInline())
            return

        if curr_state == States.PromoCodeCreate.value.state:
            type: str = state_data["promocode_type"]

            discount: int | None = None
            channel: int | None = None
            amount: int | None = None
            text: str = message.text
            await message.delete()

            try:
                if type == "discount":
                    discount = int(text.replace("%", ""))
                elif type == "balance":
                    amount = int(text)
                elif type == "channel":
                    if message.forward_from_chat is not None:
                        channel = message.forward_from_chat.id
                    else:
                        channel = int(text)
            except:
                return

            code = CaptchaGenerator.randomText()

            db.PromoCode.create(name=state_data["promocode_name"],
                                code=code,
                                type=type,
                                max_usages=int(state_data["promocode_max_usages"]),
                                channel=channel,
                                discount=discount,
                                amount=amount)
            await state.clear()
            await edit_message.edit_text(
                f"Промокод создан! <code>{state_data['promocode_name']}</code> <code>{code}</code>", parse_mode="HTML",
                reply_markup=KeyBoards.managePromoCodesSelectorInline())
            return

        if curr_state == States.BalanceTopUp.amount.state:
            try:
                amount: int = int(message.text)
                await message.delete()
            except:
                amount = None

            if amount is not None:
                if amount < db.getSettings().minimum_topup or amount > db.getSettings().maximum_topup:
                    return

                # await state.set_state(States.BalanceTopUp.bank)
                await state.update_data(amount=amount)

                payment = paymentapi.createPaymentCard(user, amount, 'None')

                await state.set_state(States.BalanceTopUp.waiting_payment)
                await state.update_data(id=payment["id"],
                                        amount=amount,
                                        bank='None')
                await edit_message.edit_caption(caption=f'✔ Нажмите на кнопку ниже для оплаты', parse_mode="HTML",
                                                reply_markup=KeyBoards.selectBankInline(payment['url']))
                return

        if curr_state == States.CategoryCreate.name.state:
            await message.delete()
            if 'rto' in state_data:
                await state.update_data(category_name=message.html_text, rto=state_data['rto'])
            else:
                await state.update_data(category_name=message.html_text)
            await state.set_state(States.CategoryCreate.description)
            await edit_message.edit_text("Введите описание новой категории:", reply_markup=KeyBoards.skipInline(
                "paid_courses_category_create_skip_description"))
            return

        if curr_state == States.CategoryCreate.description.state:
            await message.delete()
            if 'rto' in state_data:
                await state.update_data(category_description=message.html_text, rto=state_data['rto'])
            else:
                await state.update_data(category_description=message.html_text)
            await state.set_state(States.CategoryCreate.media)
            await edit_message.edit_text("Отправьте медию для новой категории:",
                                         reply_markup=KeyBoards.skipInline("paid_courses_category_create_skip_media"))
            return

        if curr_state == States.CategoryCreate.media:
            await message.delete()
            save_path = f"data/media/temp/{Math.current_milli_time() * Math.randInt(2, 999)}.png"

            if not (await MessageHelper.download_photo(bot, message, save_path)):
                await edit_message.edit_text("Попробуйте снова отправить медию для новой категории:",
                                             reply_markup=KeyBoards.skipInline(
                                                 "paid_courses_category_create_skip_media"))
                return

            await state.set_state()
            if 'rto' in state_data:
                await state.update_data(category_media=save_path, rto=state_data['rto'])
            else:
                await state.update_data(category_media=save_path)
            await edit_message.edit_text("Завершить создание категории?",
                                         reply_markup=KeyBoards.customInline("Завершить",
                                                                             "paid_courses_category_create_end"))
            return

        if curr_state == States.CategoryEdit.name.state:
            category: db.CourseCategory = state_data["category_edit"]

            category.name = message.html_text
            category.save()

            await state.set_state()
            await message.delete()
            await edit_message.edit_text("Выбери категорию для изменения:", parse_mode="HTML",
                                         reply_markup=KeyBoards.paidCoursesSelectorInline("category", "edit",
                                                                                          state_data["category_parent"],
                                                                                          state_data[
                                                                                              "category_current"]))
            return

        if curr_state == States.ManageBanMember.selectUser.state:
            entered = message.text
            multi = state_data["action"].endswith("users")

            await message.delete()
            if not multi:
                try:
                    selected_user: int | None = int(entered)
                except:
                    selected_user: str | None = str(entered).replace("@", "").replace("https://t.me/", "")

                try:
                    if isinstance(selected_user, int):
                        selected_user: db.User | None = db.User.select().where(db.User.id == selected_user).get()
                    else:
                        selected_user: db.User | None = db.User.select().where(db.User.username == selected_user).get()
                except:
                    selected_user = None

                if selected_user is None or selected_user.id == userId:
                    await state.clear()
                    await edit_message.edit_text("Неверный пользователь!", parse_mode="HTML",
                                                 reply_markup=KeyBoards.backToAdminPanelInline())
                else:
                    if selected_user.admin:
                        await edit_message.edit_text("Пользователь - админ!\nУкажите айди/ссылку/тег пользователя:",
                                                     parse_mode="HTML", reply_markup=KeyBoards.backToAdminPanelInline())
                        return

                    if state_data["action"].startswith("ban"):
                        await state.clear()
                        if selected_user.banned == True:
                            await edit_message.edit_text(f"Пользователь @{selected_user.username} уже забанен!",
                                                         parse_mode="HTML",
                                                         reply_markup=KeyBoards.backToAdminPanelInline())
                            return

                        selected_user.banned = True
                        selected_user.save()
                        await Logs.logBan(bot, selected_user, user)
                        await edit_message.edit_text(f"Пользователь @{selected_user.username} забанен.",
                                                     parse_mode="HTML", reply_markup=KeyBoards.backToAdminPanelInline())
                        return
                    if state_data["action"].startswith("unban"):
                        await state.clear()
                        if selected_user.banned == False:
                            await edit_message.edit_text(f"Пользователь @{selected_user.username} не забанен!",
                                                         parse_mode="HTML",
                                                         reply_markup=KeyBoards.backToAdminPanelInline())
                            return

                        selected_user.banned = False
                        selected_user.save()
                        await Logs.logUnban(bot, selected_user, user)
                        await edit_message.edit_text(f"Пользователь @{selected_user.username} разбанен.",
                                                     parse_mode="HTML", reply_markup=KeyBoards.backToAdminPanelInline())
                        return
            else:
                selected_users: list = str(entered).replace("@", "").replace("https://t.me/", "").split("\n")

                text = ""
                for selected_user in selected_users:
                    try:
                        exp = db.User.id == int(selected_user) if simplify(
                            selected_user).is_integer else db.User.username == selected_user
                        user: db.User = db.User.select().where(exp).get()
                    except:
                        await state.clear()
                        await edit_message.edit_text(f"{selected_user} - Неверный пользователь!", parse_mode="HTML",
                                                     reply_markup=KeyBoards.backToAdminPanelInline())
                        break
                    tag = f"@{user.username}" if user.username != "Неизвестный" else user.id

                    if user is None or user.id == userId:
                        await state.clear()
                        await edit_message.edit_text(f"{selected_user} - Неверный пользователь!", parse_mode="HTML",
                                                     reply_markup=KeyBoards.backToAdminPanelInline())
                        break

                    if user.admin:
                        text += f"{tag} - админ!\n"
                        continue

                    if state_data["action"].startswith("ban"):
                        if user.banned:
                            text += f"{tag} уже забанен!\n"
                            continue

                        user.banned = True
                        user.save()
                        await Logs.logBan(bot, selected_user, user)
                        text += f"{tag} забанен.\n"
                    else:
                        if not user.banned:
                            text += f"{tag} не забанен!\n"
                            continue

                        user.banned = False
                        user.save()
                        await Logs.logUnban(bot, selected_user, user)
                        text += f"{tag} разбанен.\n"

                await edit_message.edit_text(f"{text}\nУкажите айди/ссылку/тег пользователя(-ей):", parse_mode="HTML",
                                             reply_markup=KeyBoards.backToAdminPanelInline())

                return

        if curr_state == States.FreeCourseAction.name.state:
            action = state_data["action"]

            await message.delete()

            if action == "create":
                await state.update_data(course_name=message.text)
                await state.set_state(States.FreeCourseAction.url)
                await edit_message.edit_text("Введите ссылку для кнопки:", parse_mode="HTML",
                                             reply_markup=KeyBoards.cancelInline())
                return

            if action == "edit":
                await state.update_data(course_name=message.text)
                await state.set_state(States.FreeCourseAction.action)
                await edit_message.edit_text("Это все изменения?", parse_mode="HTML",
                                             reply_markup=KeyBoards.editFreeCoursesSelectActionsSelectorInline())
                return

        if curr_state == States.FreeCourseAction.url.state and not MessageHelper.is_menu_used(message.text):
            action = state_data["action"]

            await message.delete()

            if not message.text.lower().startswith("http"):
                await edit_message.edit_text("Это не ссылка!")
                return

            if action == "create":
                db.FreeCourses.create(name=state_data["course_name"], url=message.text)
                await state.clear()
                await edit_message.edit_text("Выбираем действие для бесплатных курсов:", parse_mode="HTML",
                                             reply_markup=KeyBoards.freeCoursesActionsSelectorInline())
                return

            if action == "edit":
                await state.update_data(course_url=message.text)
                await state.set_state(States.FreeCourseAction.action)
                await edit_message.edit_text("Это все изменения?", parse_mode="HTML",
                                             reply_markup=KeyBoards.editFreeCoursesSelectActionsSelectorInline())
                return

        await MessageHelper.state_clear_light(state)

    if text == locale.get_button("buy_course"):
        await message.answer_photo(photo=Cache.cachedInputFile("data/media/global/courses.png", "loose again.mp4"),
                                   caption=locale.get_message("paid_courses"), parse_mode="HTML",
                                   reply_markup=KeyBoards.coursesInline(user=user))
        return

    if text == locale.get_button("free_courses"):
        edit_message = await message.answer_photo(
            photo=Cache.cachedInputFile("data/media/global/freecourses.png", "loose again.mp4"),
            caption=locale.get_message("free_courses", user=user), parse_mode="HTML",
            reply_markup=KeyBoards.freeCoursesInline(user))
        await state.update_data(edit_message=edit_message)
        return

    if text == locale.get_button("personal_cabinet"):
        await message.answer_photo(
            photo=Cache.cachedInputFile("data/media/global/personal_cabinet.png", "loose again.mp4"),
            caption=locale.get_message("id+balik", id=user.id, amount=user.balance,
                                       registered=user.registered.strftime('%Y-%m-%d %H:%M:%S')),
            parse_mode="HTML", reply_markup=KeyBoards.profileInline())
        return

    if text == locale.get_button("help"):
        await message.answer_photo(photo=Cache.cachedInputFile("data/media/global/help.png", "loose again.mp4"),
                                   caption=locale.get_message("help_message"), parse_mode="HTML",
                                   reply_markup=KeyBoards.helpInline())
        return

    if text == locale.get_button("cart"):
        data = await state.get_data()
        if "cart_storage" not in data or len(data["cart_storage"]) == 0:
            await message.answer_photo(photo=Cache.cachedInputFile("data/media/global/cart.png", "xd"),
                                       caption=locale.get_message("cart_empty"), parse_mode="HTML")
            return

        cartmsg = locale.get_message("cart") + "\n"
        all_sum = 0

        for course in data["cart_storage"]:
            cartmsg += f"\n{course.name} - {course.price} рублей"
            all_sum += course.price

        cartmsg += f"\nОбщая сумма: {all_sum}"
        await message.answer_photo(photo=Cache.cachedInputFile("data/media/global/cart.png", "xd"), caption=cartmsg,
                                   parse_mode="HTML", reply_markup=KeyBoards.cartInline())
        return

    if text == locale.get_button("balance_topup"):
        await state.set_state(States.BalanceTopUp.amount)
        edit_message = await message.answer_photo(
            photo=Cache.cachedInputFile("data/media/global/balance_topup.png", "xd"),
            caption=locale.get_message("pay_create"), reply_markup=KeyBoards.changePayment(user, db.getSettings().bank),
            parse_mode="HTML")
        await state.update_data(edit_message=edit_message)
        return

    if not (await Checks.admin(user)):
        return

    if text == "🎩 Админ-панель 🎩":
        await message.answer("Открываю админ-панель 🎩🎩🎩", parse_mode="HTML", reply_markup=KeyBoards.adminMenuReply())
        return

    if text == "Курсы 📚":
        await message.answer("Выберите тип курсов для настройки: ", parse_mode="HTML",
                             reply_markup=KeyBoards.manageCoursesSelectorInline())
        return

    if text == "Промокоды 🔖":
        await message.answer("Выберите тип курсов для настройки: ", parse_mode="HTML",
                             reply_markup=KeyBoards.managePromoCodesSelectorInline())
        return

    if text == "Блокировки 🔨":
        await message.answer("Выбираем действие:", parse_mode="HTML", reply_markup=KeyBoards.manageBansSelectorInline())
        return

    if text == "Статистика 📊":
        users = db.User.select()
        info = db.getInfo()
        referrals = users.where(db.User.referrals > 0)
        from_referrals = 0
        total_on_balances = 0
        total_purchases = len(db.Purchase.select())
        topup_for_day = 0

        for referral in referrals:
            from_referrals += referral.referrals

        for user_with_balance in users.where(db.User.balance > 0):
            total_on_balances += user_with_balance.balance

        for payment in db.BalanceHistory.select().where(
                (db.BalanceHistory.date.between(datetime.now() - timedelta(hours=24), datetime.now())) & (
                        db.BalanceHistory.amount > 0)):
            topup_for_day += payment.amount

        await message.answer(
            "Денюшек: 💰"
            f"\n Всего заработанно: {info.earned}"
            f"\n Всего на балансах: {total_on_balances}"
            f"\n За этот день: {topup_for_day}"
            f"\n Всего покупок: {total_purchases}"
            "\n"
            "\nПользователей: 🥸"
            f"\n Всего: {len(users)}"
            f"\n Проходящих капчу: {len(users.where(db.User.captcha != None))}"
            f"\n Заблокированных: {len(users.where(db.User.banned == True))}"
            f"\n Заплативших: {len(users.where(db.User.purchases > 0 | db.User.balance > 0))}"
            f"\n Рефералов: {len(referrals)}"
            f"\n От рефералов: {from_referrals}"
            f"\n За этот день: {len(users.where(db.User.registered.between(datetime.now() - timedelta(hours=24), datetime.now())))}"
            f"\n Заблокировало бота: {len(users.where(db.User.blocked_bot == True))}",
            parse_mode="HTML", reply_markup=KeyBoards.backToAdminPanelInline())
        return

    if text == "Экспорт информации 🧮":
        await message.answer("Выбери категорию экспортира:", parse_mode="HTML",
                             reply_markup=KeyBoards.exportInformationSelectorInline())
        return

    if text == "Рассылка 🪃":
        await message.answer("Выбери категорию рассылки:", parse_mode="HTML",
                             reply_markup=KeyBoards.mailingSelectorInline())
        return

    if text == "Настройки ⚙️":
        await message.answer("Выбери категорию настройки:", parse_mode="HTML",
                             reply_markup=KeyBoards.settingsSelectorInline())
        return

    if text == "🎩 Обратно 🎩":
        await message.answer("Закрываю админ-панель 🎩🎩🎩", parse_mode="HTML", 
                             reply_markup=KeyBoards.welcomeReply(True))
        return


async def syk(s):
    print(s)


async def main():
    # scheduler.start()
    # print(scheduler.schedule(syk("xad"), delay=5))
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    print("1 ... Очистка временных файлов")
    Cleaner.clearTemp()

    print("2 ... Пре-генерация капчи")
    asyncio.run(CaptchaGenerator.pre_generate_and_save_captcha())

    print("3 ... Запуск сервисов")
    Cache.start()
    locale.start()

    print("4 ... Запуск бота")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        Cache.cacheUpdate("mode.running", False)
        sys.exit(0)
