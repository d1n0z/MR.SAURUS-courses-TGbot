from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
import data.db as db
import utils.Cache as Cache
import locales as locale
from config import MANAGER_URL


async def subscribe(bot) -> InlineKeyboardMarkup:
    channels = []
    row = []

    for channel in db.SubscribeChannel.select():
        try:
            row.append(InlineKeyboardButton(text=channel.name, callback_data="_",
                                            url=(await Cache.cachedInvite(bot, channel.channel))))
        except Exception as e:
            print(f"Keyboards:subscribe(bot={bot}) -> InlineKeyboardMarkup, ", e)

        if len(row) > 1:
            channels.append(row)
            row = []

    if len(row) > 0:
        channels.append(row)
        row = []

    channels.append([InlineKeyboardButton(text="Проверить подписку ✅", callback_data="check_subscribe")])

    return InlineKeyboardMarkup(inline_keyboard=channels)


def logsUserManage(user: db.User, ban: bool = True, balance: bool = True) -> InlineKeyboardMarkup:
    keyboard = []
    row = []

    if ban:
        row.append(InlineKeyboardButton(text="Разбанить пользователя", callback_data=f"logs_unban_{user.id}") if user.banned else InlineKeyboardButton(text="Забанить пользователя", callback_data=f"logs_ban_{user.id}"))

    if balance:
        row.append(InlineKeyboardButton(text="Сбросить баланс", callback_data=f"logs_balance_{user.id}_0"))

    if len(row) != 0:
        keyboard.append(row)
        row = []

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def customInline(text: str, data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=data)]])


def skipInline(skip: str = "skip") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Пропустить", callback_data=skip)]])

def settingsDropsSelectorInline() -> InlineKeyboardMarkup:
    keyboard = []
    row = []

    for drop in db.Drop.select():
        row.append(InlineKeyboardButton(text=drop.name, callback_data=f"settings_drops_delete_{drop.userid}"))
        
        if len(row) > 1:
            keyboard.append(row)
            row = []

    if len(row) != 0:
        keyboard.append(row)
        row = []

    keyboard.append([InlineKeyboardButton(text="Добавить нового дропа", callback_data="settings_drops_create")])
    keyboard.append(cancelInline("settings").inline_keyboard[0])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def settingsBotSettingsSubscribeChannelSelectorInline() -> InlineKeyboardMarkup:
    keyboard = []
    row = []

    for channel in db.SubscribeChannel.select():
        row.append(InlineKeyboardButton(text=channel.name, callback_data=f"settings_bot_subscribe_delete_{channel.id}"))
        if len(row) > 1:
            keyboard.append(row)
            row = []

    if len(row) != 0:
        keyboard.append(row)
        row = []

    keyboard.append([InlineKeyboardButton(text="Добавить новый канал", callback_data="settings_bot_subscribe_create")])
    keyboard.append(cancelInline("settings_bot").inline_keyboard[0])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def settingsLogsChannelSelectorInline(category: str) -> InlineKeyboardMarkup:
    keyboard = []
    row = []

    for channel in db.LogChannel.select().where(db.LogChannel.type == category):
        row.append(InlineKeyboardButton(text=channel.name, callback_data=f"settings_logs_delete_{channel.id}"))
        if len(row) > 1:
            keyboard.append(row)
            row = []

    if len(row) != 0:
        keyboard.append(row)
        row = []

    keyboard.append([InlineKeyboardButton(text="Добавить новый канал", callback_data="settings_logs_create")])
    keyboard.append(cancelInline("settings_logs").inline_keyboard[0])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def settingsBotSelectorInline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Минимальная сумма пополнения", callback_data="settings_bot_minimum_topup")],
        [InlineKeyboardButton(text="Максимальная сумма пополнения", callback_data="settings_bot_maximum_topup")],
        [InlineKeyboardButton(text="Глобальная скидка на товары", callback_data="settings_bot_discount")],
        [InlineKeyboardButton(text=f"{'🟢' if Cache.cachedMode('test') else '🔴'} Тестовый режим {'🟢' if Cache.cachedMode('test') else '🔴'}", callback_data="settings_bot_test")],
        [InlineKeyboardButton(text="Платежка", callback_data="settings_bot_payment")],
        [InlineKeyboardButton(text="Подписки", callback_data="settings_bot_subscribe")],
        [InlineKeyboardButton(text=f"{'🟢' if Cache.cachedMode('sber_enabled') else '🔴'} Сбер {'🟢' if Cache.cachedMode('sber_enabled') else '🔴'}", callback_data="settings_bot_bank_sber_enabled")],
        [InlineKeyboardButton(text=f"{'🟢' if Cache.cachedMode('tinkoff_enabled') else '🔴'} Тинькофф {'🟢' if Cache.cachedMode('tinkoff_enabled') else '🔴'}", callback_data="settings_bot_bank_tinkoff_enabled")],
        [InlineKeyboardButton(text=f"{'🟢' if Cache.cachedMode('raiffaisen_enabled') else '🔴'} Райфайзен {'🟢' if Cache.cachedMode('raiffaisen_enabled') else '🔴'}", callback_data="settings_bot_bank_raiffaisen_enabled")],
        [InlineKeyboardButton(text=f"{'🟢' if Cache.cachedMode('sbp_enabled') else '🔴'} СБП {'🟢' if Cache.cachedMode('sbp_enabled') else '🔴'}", callback_data="settings_bot_bank_sbp_enabled")],
        cancelInline("settings").inline_keyboard[0],
    ])


def settingsBotPaymentSelectionInline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 PayLama", callback_data="settings_bot_payment_paylama")],
        [InlineKeyboardButton(text="2 Payok", callback_data="settings_bot_payment_payok")],
        [InlineKeyboardButton(text="3 AnyPay", callback_data="settings_bot_payment_anypay")],
        [InlineKeyboardButton(text="4 Дроп", callback_data="settings_bot_payment_drop")],
        cancelInline("settings_bot").inline_keyboard[0],
    ])


def settingsLogsSelectorInline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Регистрация", callback_data="settings_logs_start")],
        [InlineKeyboardButton(text="Покупка", callback_data="settings_logs_buy")],
        [InlineKeyboardButton(text="Пополнение баланса", callback_data="settings_logs_balancetopup")],
        [InlineKeyboardButton(text="Использование промо", callback_data="settings_logs_promocodeusage")],
        [InlineKeyboardButton(text="Бан", callback_data="settings_logs_ban")],
        [InlineKeyboardButton(text="Разбан", callback_data="settings_logs_unban")],
        cancelInline("settings_bot").inline_keyboard[0],
    ])


def promoCodeTypeSelectInline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Скидка", callback_data="promocode_type_discount")],
        [InlineKeyboardButton(text="Канал", callback_data="promocode_type_channel")],
        [InlineKeyboardButton(text="Баланс", callback_data="promocode_type_balance")],
    ])


def cancelInline(data: str = "cancel", course: int = None, cc: bool = False) -> InlineKeyboardMarkup:
    if cc:
        return InlineKeyboardMarkup(inline_keyboard=courseButtons([
            [InlineKeyboardButton(text=locale.get_button("back"), callback_data=data)]], course))
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=locale.get_button("back"), callback_data=data)]])


def cancelInlinePaidCoursesCategoryCreateEnd(category: db.CourseCategory, data: str = "cancel") -> InlineKeyboardMarkup:
    keyboard = [[InlineKeyboardButton(text=locale.get_button("back"), callback_data=data)]]
    keyboard = categoryButtons(keyboard, category.id)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def captchaSuccessInline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=locale.get_button("go_to_bot"), callback_data="check_subscribe")]])


def welcomeReply(is_admin: bool) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text=locale.get_button("buy_course")), KeyboardButton(text=locale.get_button("free_courses"))],
        [KeyboardButton(text=locale.get_button("personal_cabinet")), KeyboardButton(text=locale.get_button("cart"))],
        [KeyboardButton(text=locale.get_button("balance_topup")), KeyboardButton(text=locale.get_button("help"))]
    ]

    if is_admin:
        keyboard.append([KeyboardButton(text="🎩 Админ-панель 🎩")])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def settingsLocaleEditInline(category: str, id: str, button: str | None = None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [] if button is None else [InlineKeyboardButton(text=button, url="https://snowe.pw")],
        [InlineKeyboardButton(text="Изменить текст", callback_data=f"settings_{category}_{id}_edit")],
        [InlineKeyboardButton(text="Сбросить текст", callback_data=f"settings_{category}_{id}_reset")],
        [InlineKeyboardButton(text=locale.get_button("back"), callback_data=f"settings_{category}")]
    ])


def settingsLocaleSelectorInline(category: str) -> InlineKeyboardMarkup:
    keyboard = []
    row = []

    for k, v in locale.description_keys[category].items():
        row.append(InlineKeyboardButton(text=v, callback_data=f"settings_{category}_{k}"))

        if len(row) > 2:
            keyboard.append(row)
            row = []

    if len(row) != 0:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(text="Обратно", callback_data=f"settings")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def settingsMediaSelectorInline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Корзина", callback_data="settings_media_cart"), InlineKeyboardButton(text="Платные курсы", callback_data="settings_media_courses")],
        [InlineKeyboardButton(text="Бесплатные курсы", callback_data="settings_media_freecourses"), InlineKeyboardButton(text="Оплата", callback_data="settings_media_payment")],
        [InlineKeyboardButton(text="Оплачено", callback_data="settings_media_purchased"), InlineKeyboardButton(text="Медия не найдена", callback_data="settings_media_not_found_404_err")],
        [InlineKeyboardButton(text="Помощь", callback_data="settings_media_help"), InlineKeyboardButton(text="Личный кабинет", callback_data="settings_media_personal_cabinet")],
        [InlineKeyboardButton(text="Пополнить баланс", callback_data="settings_media_balance_topup")],
        [InlineKeyboardButton(text=locale.get_button("back"), callback_data="admin")],
    ])


def settingsSelectorInline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Бот", callback_data="settings_bot")],
        [InlineKeyboardButton(text="Логи", callback_data="settings_logs")],
        [InlineKeyboardButton(text="Кнопки", callback_data="settings_buttons")],
        [InlineKeyboardButton(text="Сообщения", callback_data="settings_messages")],
        [InlineKeyboardButton(text="Глобальная медия", callback_data="settings_media")],
        [InlineKeyboardButton(text="Дропы", callback_data="settings_drops")],
        [InlineKeyboardButton(text=locale.get_button("back"), callback_data="admin")],
    ])


def backToAdminPanelInline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=locale.get_button("back"), callback_data="admin")]
    ])


def backToProfileInline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=locale.get_button("back"), callback_data="profile")]
    ])


def profileInline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=locale.get_button("history_buy"), callback_data="history_purchases"),
         InlineKeyboardButton(text=locale.get_button("history_replenishment"), callback_data="history_balance")],
        [InlineKeyboardButton(text=locale.get_button("referal_system"), callback_data="referral_system"),
         InlineKeyboardButton(text=locale.get_button("activate_promo"), callback_data="promocode_activation")],
        [InlineKeyboardButton(text=locale.get_button("replenishment_balance"), callback_data="balance_topup")]
    ])


def backwardsToParentCourseCategory(parent: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Обратно", callback_data=f"course_category_{parent}")]])


def cartConfirmBuy() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=locale.get_button("accept_buy"), callback_data=f"cart_buy_confirm")],
        cancelInline().inline_keyboard[0],
    ])


def courseConfirmBuy(parent: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=locale.get_button("accept_buy"), callback_data=f"course_buy_confirm")],
        backwardsToParentCourseCategory(parent).inline_keyboard[0],
    ])


def courseInfoInline(parent: int, course_id: int, user: db.User | None = None) -> InlineKeyboardMarkup:
    keyboard=[
        [InlineKeyboardButton(text=locale.get_button("purchase_now"), callback_data=f"course_buy"),
         InlineKeyboardButton(text="Добавить в корзину", callback_data=f"course_cart")],
        [InlineKeyboardButton(text=locale.get_button("activate_promo"), callback_data=f"course_promocode")],
        [] if not user.admin else [InlineKeyboardButton(text="Поделиться товаром",
                                                        callback_data=f"course_share_{course_id}")],
        backwardsToParentCourseCategory(parent).inline_keyboard[0],
    ]

    if user is not None and user.admin:
        keyboard = courseButtons(keyboard, course_id)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def paidCoursesSelectorInline(type: str, action: str, parent: None | int = None, current: None | int = None, allow_select_global: bool = False, select_only_empty_categories: bool = False) -> InlineKeyboardMarkup:
    keyboard = []
    row = []

    for courseCategory in db.CourseCategory.select().where(db.CourseCategory.parent == current):
        row.append(InlineKeyboardButton(text=courseCategory.name, callback_data=f"paid_courses_{type}_select_category_{courseCategory.id}"))

        if len(row) >= 2:
            keyboard.append(row)
            row = []

    categories = len(keyboard)

    if len(row) != 0:
        keyboard.append(row)
        row = []

    if len(keyboard) == 0 and current is not None and type == "course":
        for course in db.Course.select().where(db.Course.category == current):
            row.append(InlineKeyboardButton(text=course.name, callback_data=f"paid_courses_{type}_{action}_course_{course.id}"))

            if len(row) > 2:
                keyboard.append(row)
                row = []

    if len(row) != 0:
        keyboard.append(row)
        row = []

    if type == "category":
        if (allow_select_global or current != None) or (select_only_empty_categories and categories == 0):
            keyboard.append([InlineKeyboardButton(text="✅ Выбрать эту категорию ✅", callback_data=f"paid_courses_{type}_{action}_finish")])

    if parent != None:
        keyboard.append([InlineKeyboardButton(text=locale.get_button("back"), callback_data=f"paid_courses_{type}_select_category_{parent}")])
    elif current != None:
        keyboard.append([InlineKeyboardButton(text=locale.get_button("back"), callback_data=f"paid_courses_{type}_{action}")])
    else:
        keyboard.append([InlineKeyboardButton(text=locale.get_button("back"), callback_data=f"paid_courses_{type}")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def categoryButtons(keyboard: list, category: int, set_photo: bool = True, set_costs: bool = True,
                    direct_link_to_category: bool = True, set_desc: bool = True, category_discount: bool = True,
                    add_category: bool = True, add_product: bool = True, del_category: bool = True) -> list:
    rows = []
    if set_photo:
        rows.append(InlineKeyboardButton(text=locale.get_button("set_photo"),
                                         callback_data=f'edit_category_set_photo_paid_{category}'))
    if set_costs:
        rows.append(InlineKeyboardButton(text=locale.get_button("set_costs"),
                                         callback_data=f'edit_courses_category_costs_paid_{category}'))
    if direct_link_to_category and category >= 0:
        rows.append(InlineKeyboardButton(text=locale.get_button("direct_link_to_category"),
                                         callback_data=f'category_share_{category}'))
    if set_desc and category >= 0:
        rows.append(InlineKeyboardButton(text=locale.get_button("set_desc"),
                                         callback_data=f'edit_category_set_desc_paid_{category}'))
    if category_discount:
        rows.append(InlineKeyboardButton(text=locale.get_button("category_discount"),
                                         callback_data=f'edit_courses_category_discount_paid_{category}'))
    if add_category:
        rows.append(InlineKeyboardButton(text=locale.get_button("add_category"),
                                         callback_data=f'edit_courses_add_category_paid_{category}'))
    if add_product and category >= 0:
        rows.append(InlineKeyboardButton(text=locale.get_button("add_product"),
                                         callback_data=f'edit_courses_add_product_paid_{category}'))
    if del_category and category >= 0:
        rows.append(InlineKeyboardButton(text=locale.get_button("del_category"),
                                         callback_data=f'edit_courses_delete_category_paid_{category}'))
    new_kbd = keyboard
    for k, i in enumerate(rows):
        if k % 2 == 0:
            new_kbd.insert(0, [])
        new_kbd[0].append(i)
    return new_kbd


def courseButtons(keyboard: list, course: int, set_photo: bool = True, set_costs: bool = True,
                  direct_link_to_category: bool = True, set_desc: bool = True, product_discount: bool = True) -> list:
    rows = []
    if set_photo:
        rows.append(InlineKeyboardButton(text=locale.get_button("set_photo"),
                                         callback_data=f'edit_course_set_photo_paid_{course}'))
    if set_costs:
        rows.append(InlineKeyboardButton(text=locale.get_button("set_cost"),
                                         callback_data=f'edit_course_set_cost_paid_{course}'))
    if direct_link_to_category:
        rows.append(InlineKeyboardButton(text=locale.get_button("set_channel"),
                                         callback_data=f'edit_course_set_channel_paid_{course}'))
    if set_desc:
        rows.append(InlineKeyboardButton(text=locale.get_button("set_desc"),
                                         callback_data=f'edit_course_set_desc_paid_{course}'))
    if product_discount:
        rows.append(InlineKeyboardButton(text=locale.get_button("product_discount"),
                                         callback_data=f'edit_course_product_discount_paid_{course}'))
    new_kbd = keyboard
    for k, i in enumerate(rows):
        if k % 2 == 0:
            new_kbd.insert(0, [])
        new_kbd[0].append(i)
    return new_kbd


def coursesInline(parent: None | int = None, current: None | int = None, user: db.User | None = None) -> InlineKeyboardMarkup:
    keyboard = []
    row = []

    for courseCategory in db.CourseCategory.select().where((db.CourseCategory.parent == current) & (db.CourseCategory.enabled == True)):
        row.append(InlineKeyboardButton(text=courseCategory.name, callback_data=f"course_category_{courseCategory.id}"))

        if len(row) >= 2:
            keyboard.append(row)
            row = []

    if len(row) != 0:
        keyboard.append(row)
        row = []

    if len(keyboard) == 0 and current is not None:
        for course in db.Course.select().where(db.Course.category == current):
            row.append(InlineKeyboardButton(text=course.name, callback_data=f"course_select_{course.id}"))

            if len(row) > 2:
                keyboard.append(row)
                row = []

    if len(row) != 0:
        keyboard.append(row)
        row = []

    if current != None:
        if user.admin:
            keyboard.append([InlineKeyboardButton(text="Поделиться категорией", callback_data=f"category_share_{current}")])

    if parent != None:
        keyboard.append([InlineKeyboardButton(text=locale.get_button("back"), callback_data=f"course_category_{parent}")])
    elif current != None:
        keyboard.append([InlineKeyboardButton(text=locale.get_button("back"), callback_data=f"course_category")])

    if user is not None and user.admin:
        if current is not None:
            keyboard = categoryButtons(keyboard, current)
        else:
            keyboard = categoryButtons(keyboard, -1)
    #keyboard.append(cancelInline().inline_keyboard[0])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def freeCoursesInline(user: db.User | None = None) -> InlineKeyboardMarkup:
    keyboard = []
    row = []

    for freeCourse in db.FreeCourses.select():
        row.append(InlineKeyboardButton(text=freeCourse.name, url=freeCourse.url))

        if len(row) >= 2:
            keyboard.append(row)
            row = []

    if len(row) != 0:
        keyboard.append(row)

    if user is not None and user.admin:
        keyboard.insert(0,
                        [InlineKeyboardButton(text="🖊 Изменить кнопки", callback_data=f'free_courses_edit')])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def translationInline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=locale.get_button("i_purchase"), callback_data="translation_check")],
        [InlineKeyboardButton(text=locale.get_button("back"), callback_data="cancel")],
    ])


def selectBankInline(url) -> InlineKeyboardMarkup:
    keyboard = [[InlineKeyboardButton(text="Оплатить", url=url)],
                [InlineKeyboardButton(text="✅ Готово", callback_data="translation_check")]]

    # keyboard = []
    # if Cache.cachedMode("sber_enabled"):
    #     keyboard.append([InlineKeyboardButton(text=locale.get_button("sber"), callback_data="bank_sberbank")])
    # if Cache.cachedMode("tinkoff_enabled"):
    #     keyboard.append([InlineKeyboardButton(text=locale.get_button("tinkoff"), callback_data="bank_tinkoff")])
    # if Cache.cachedMode("raiffaisen_enabled"):
    #     keyboard.append([InlineKeyboardButton(text=locale.get_button("raifaisen"), callback_data="bank_raiffeisenbank")])
    # if Cache.cachedMode("sbp_enabled"):
    #     keyboard.append([InlineKeyboardButton(text=locale.get_button("sbp"), callback_data="bank_sbp")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def mailingSelectorInline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отправить всем ✉️", callback_data="mailing_all")],
        [InlineKeyboardButton(text="Отправить покупателям ☄️", callback_data="mailing_customer")],
        [InlineKeyboardButton(text="Отправить не покупателям 🖕", callback_data="mailing_non_customer")],
        [InlineKeyboardButton(text="Отправить тем кто в бане ❄️", callback_data="mailing_banned")],
        [InlineKeyboardButton(text=locale.get_button("back"), callback_data="admin")],
    ])


def confirm_unbanban_all() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Я понимаю, что разблокирую всех", callback_data="unban_all_confirm")],
        backToAdminPanelInline().inline_keyboard[0]
    ])


def confirm_ban_all() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Я понимаю, что заблокирую всех", callback_data="ban_all_confirm")],
        backToAdminPanelInline().inline_keyboard[0]
    ])


def freeCoursesListSelectorInline(action: str) -> InlineKeyboardMarkup:
    keyboard = []
    row = []

    for course in db.FreeCourses.select():
        row.append(InlineKeyboardButton(text=f"{course.name} ({course.url})", callback_data=f"free_courses_{action}_{course.id}"))

        if len(row) >= 2:
            keyboard.append(row)
            row = []

    if len(row) != 0:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(text=locale.get_button("back"), callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def dropCheckAcceptorInline(uid, flag: bool | None = None) -> InlineKeyboardMarkup:
    if flag != None:
        if flag:
            return InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Одобренно", callback_data="ok")],
            ])
        else:
            return InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Отклоненно", callback_data="ok")],
            ])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Одобрить ✅", callback_data=f"drop_check_accept_{uid}"), InlineKeyboardButton(text="Отклонить ❌", callback_data=f"drop_check_deny_{uid}")],
    ])

def editFreeCoursesSelectActionsSelectorInline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Изменить название", callback_data="free_courses_edit_name"), InlineKeyboardButton(text="Изменить ссылку", callback_data="free_courses_edit_url")],
        [InlineKeyboardButton(text="Сохранить ✅", callback_data="free_courses_edit_save"), InlineKeyboardButton(text="Отменить ❌", callback_data="cancel")],
    ])


def freeCoursesActionsSelectorInline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Добавить", callback_data="free_courses_create"), InlineKeyboardButton(text="Удалить", callback_data="free_courses_delete")],
        [InlineKeyboardButton(text="Изменить", callback_data="free_courses_edit")],
        [InlineKeyboardButton(text="Обратно", callback_data="admin")],
    ])


def editPaidCategorySelectActionsSelectorInline(category: db.CourseCategory) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Изменить название", callback_data="paid_courses_category_edit_name"),
         InlineKeyboardButton(text="Изменить описание", callback_data="paid_courses_category_edit_description")],
        [#InlineKeyboardButton(text="Изменить скидку", callback_data="paid_courses_category_edit_discount"),
         InlineKeyboardButton(text="Спрятать" if category.enabled else "Показать", callback_data="paid_courses_category_edit_toggle"),
         InlineKeyboardButton(text="Изменить медию", callback_data="paid_courses_category_edit_media")],
        [InlineKeyboardButton(text="Сохранить ✅", callback_data="paid_courses_category_save")],
    ])


def editPaidCourseSelectActionsSelectorInline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Изменить название", callback_data="paid_courses_edit_name"),
         InlineKeyboardButton(text="Изменить описание", callback_data="paid_courses_edit_description")],
        [InlineKeyboardButton(text="Изменить категорию", callback_data="paid_courses_edit_category"),
         InlineKeyboardButton(text="Изменить канал", callback_data="paid_courses_edit_channel"), ],
        [InlineKeyboardButton(text="Изменить скидку", callback_data="paid_courses_edit_discount"),
         InlineKeyboardButton(text="Изменить медию", callback_data="paid_courses_edit_media")],
        [InlineKeyboardButton(text="Сохранить ✅", callback_data="paid_courses_save")],
    ])


def editPromoCodeSelectActionsSelectorInline(promocode: db.PromoCode) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Изменить код", callback_data="promocode_edit_generatecode"), ], #InlineKeyboardButton(text="Изменить тип", callback_data="promocode_edit_type")
        [(InlineKeyboardButton(text="Включить", callback_data="promocode_edit_toggle") if not promocode.enabled else InlineKeyboardButton(text="Выключить", callback_data="promocode_edit_toggle")),
         InlineKeyboardButton(text="Установить макс. использований", callback_data="promocode_edit_maxuses")],
        [(InlineKeyboardButton(text="Изменить канал" if promocode.type == "channel" else "Изменить баланс" if promocode.type == "balance" else "Изменить скидку", callback_data="promocode_edit_value"))],
        [InlineKeyboardButton(text="Сохранить ✅", callback_data="promocode_edit_save")],
    ])


def cartRemoveCourse(cartedCourses: list) -> InlineKeyboardMarkup:
    keyboard = []
    row = []

    for course in cartedCourses:
        row.append(InlineKeyboardButton(text=course.name, callback_data=f"cart_remove_{course.id}"))

        if len(row) > 1:
            keyboard.append(row)
            row = []

    if len(row) > 0:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(text=locale.get_button("back"), callback_data="cancel")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def promoCodeSelectorInline(action: str) -> InlineKeyboardMarkup:
    keyboard = []
    row = []

    for promocode in db.PromoCode.select():
        row.append(InlineKeyboardButton(text=promocode.name, callback_data=f"promocode_{action}_{promocode.id}"))

        if len(row) > 1:
            keyboard.append(row)
            row = []

    if len(row) > 0:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(text="Обратно", callback_data="admin")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def managePromoCodesSelectorInline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Создать", callback_data="promocode_create"),
         InlineKeyboardButton(text="Удалить", callback_data="promocode_delete")],
        [InlineKeyboardButton(text="Изменить", callback_data="promocode_edit")],
        [InlineKeyboardButton(text="Обратно", callback_data="admin")],
    ])


def managePaidCoursesTypeSelectorInline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Категории", callback_data="paid_courses_category"),
         InlineKeyboardButton(text="Курсы", callback_data="paid_courses_course")],
        [InlineKeyboardButton(text="Обратно", callback_data="admin")],
    ])


def managePaidCoursesSelectorInline(action: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Создать", callback_data=f"paid_courses_{action}_create"), InlineKeyboardButton(text="Удалить", callback_data=f"paid_courses_{action}_delete")],
        [InlineKeyboardButton(text="Изменить", callback_data=f"paid_courses_{action}_edit")],
        [InlineKeyboardButton(text="Обратно", callback_data="paid_courses")],
    ])


def manageCoursesSelectorInline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Бесплатные курсы", callback_data="free_courses")],
        [InlineKeyboardButton(text="Платные курсы", callback_data="paid_courses")],
        [InlineKeyboardButton(text="Обратно", callback_data="admin")],
    ])


def exportInformationSelectorInline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пользователи", callback_data="export_users")],
        [InlineKeyboardButton(text="История балансов", callback_data="export_balance_history")],
        [InlineKeyboardButton(text="История покупок", callback_data="export_purchases_history")],
        [InlineKeyboardButton(text="Промокоды", callback_data="export_promocode")],
        [InlineKeyboardButton(text="Обратно", callback_data="paid_courses")],
    ])


def manageBansSelectorInline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Разблокировка", callback_data="unban")],
        [InlineKeyboardButton(text="Блокировка", callback_data="ban")],
        [InlineKeyboardButton(text="Обратно", callback_data="admin")],
    ])


def unbanSelectorInline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Разбанить всех 💀", callback_data="unban_all")],
        #[InlineKeyboardButton(text="Разбанить пользователя ☄️", callback_data="unban_user")],
        [InlineKeyboardButton(text="Разбанить пользователей 🌪", callback_data="unban_users")],
        [InlineKeyboardButton(text="Обратно", callback_data="managebans")],
    ])


def banSelectorInline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Забанить всех 💀", callback_data="ban_all")],
        #[InlineKeyboardButton(text="Забанить пользователя ☄️", callback_data="ban_user")],
        [InlineKeyboardButton(text="Забанить пользователей 🌪", callback_data="ban_users")],
        [InlineKeyboardButton(text="Обратно", callback_data="managebans")],
    ])


def cartInline() -> InlineKeyboardMarkup: # изменить
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=locale.get_button("buy2_course"), callback_data="cart_pay")],
        [InlineKeyboardButton(text=locale.get_button("delete_course"), callback_data="cart_remove")],
        [InlineKeyboardButton(text=locale.get_button("apply_promo"), callback_data="cart_promocode")]
    ])


def helpInline() -> InlineKeyboardMarkup: 
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=locale.get_button("manager"), url=MANAGER_URL)]
    ])


def adminMenuReply() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Курсы 📚"), KeyboardButton(text="Блокировки 🔨")],
        [KeyboardButton(text="Статистика 📊"), KeyboardButton(text="Экспорт информации 🧮")],
        [KeyboardButton(text="Рассылка 🪃"), KeyboardButton(text="Настройки ⚙️")],
        [KeyboardButton(text="Промокоды 🔖"), KeyboardButton(text="🎩 Обратно 🎩")],
    ], one_time_keyboard=True, resize_keyboard=True)


def welcomeInline() -> InlineKeyboardMarkup: 
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=locale.get_button("instruktion"), url="https://snowe.pw/"), InlineKeyboardButton(text=locale.get_button("Tos"), url="https://snowe.pw")],
    ])


def confirmMail(linebreak=True) -> InlineKeyboardMarkup:
    kbd = [
        [InlineKeyboardButton(text="Отправить!", callback_data="mailing_confirm")],
        [InlineKeyboardButton(text="Добавить кнопку", callback_data="mailing_add_button")],
        [InlineKeyboardButton(text="Не отправлять", callback_data="cancel")]
    ]
    if linebreak:
        kbd.insert(2, [InlineKeyboardButton(text="Перенести кнопки на следующий ряд",
                                            callback_data="mailing_add_line")])
    return InlineKeyboardMarkup(inline_keyboard=kbd)


def mailKeyboard(buttons) -> InlineKeyboardMarkup:
    kbd = []
    for y in buttons:
        kbd.append([])
        for i in y:
            kbd[-1].append(InlineKeyboardButton(text=i[0], url=i[1], callback_data="_"))
    print(kbd)
    return InlineKeyboardMarkup(inline_keyboard=kbd)


def changePayment(user, currentbank):
    print(currentbank)
    if currentbank == 4:
        currentbank = 'bovapay'
    elif currentbank == 3:
        currentbank = 'nicepay'
    elif currentbank == 2:
        currentbank = 'aaio'
    else:
        currentbank = 'anypay'
    banks = ['anypay', 'aaio', 'nicepay', 'bovapay']
    banks.remove(currentbank)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сменить на " + banks[0], callback_data=f"switch_payment_{banks[0]}")],
        [InlineKeyboardButton(text="Сменить на " + banks[1], callback_data=f"switch_payment_{banks[1]}")],
        [InlineKeyboardButton(text="Сменить на " + banks[2], callback_data=f"switch_payment_{banks[2]}")],
    ]) if user.admin else None
