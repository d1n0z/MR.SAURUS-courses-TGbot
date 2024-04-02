import traceback

import data.db as db
import utils.Cache as Cache

messages = {
    "cart_empty": "Корзина пустая!", "bank_select": "Выберите банк:", "help_message": "Поддержки нет.",
    "banned_user": "❌ Вы заблокированы администратором.",
    "subscribe": "❗️ Бот не может продолжать свою работу"
                 "\nБез твоих подписок на каналы. "
                 "Обязательно проверь их наличие, что бы не потерять нас"
                 " и всегда быть на связи!", "captcha": "❌ Для начала вы должны ввести капчу:",
    "welcome": "@{user} приветствуем тебя!", "cancel": "Отменено ❌",
    "pay_error": "Оплата ещё не пришла или её не было! "
                 "Подождите 1-2 минуту и попробуйте снова, если проблемы то свяжитесь с поддержкой!",
    "pay_success": "Оплата принята ✅"
                   "\nВаш счёт пополнен на {amount} рублей",
    "pay_create": "Введите сумму пополнения: (Минимум 100 рублей)", "pay_error2": "Извините, произошла ошибка!",
    "oplata_created_card": "⚠️ <u>Реквизиты для оплаты курсов:</u>"
                           "\n\nТыкни и скопируется сразу удобные для тебя реквизиты👇"
                           "\n\n{bank_display}: <code>{card}</code> - <b>Только в {bank_display}</b>"
                           "\nИмя получатель не зависит от перевода"
                           "\n\n❌ Обязательный комментарий для нахождения платежа: <code>Курсы</code>"
                           "\n\n📌 <i>После оплаты пришлите полный чек в бота или скрин перевода с вашего банка."
                           "</i> Скидывать в формате фото",
    "oplata_created_form": "Оплата по форме 📲"
                           "\n\nПерейдите по ссылке <a href=\"{url}\">ОПЛАТА</a>"
                           "\nИ оплатите сумму: <code>{amount}</code> руб."
                           "\n\nВаш ID заявки: {id}"
                           "\n\nПосле оплаты подождите 2-3 минуты и нажмите на кнопку \"Я оплатил\"",
    "pay_notsend": "Оплата ещё не пришла или её не было! "
                   "Подождите 1-2 минуту и попробуйте снова, если проблемы то свяжитесь с поддержкой!",
    "pay_accept": "Оплата принята ✅",
    "pay_history": "Список ваших пополнений:\n", "pay_error_history": "Вы ничего не пополняли.",
    "not_buy": "Вы ничего не покупали.", "not_replenishment": "Вы ничего не пополняли",
    "subscribe2": "Вы ещё не подписались на все каналы!", "thx": "Спасибо, что решил воспользоваться нашим сервисом."
                                                                 "\nЕсли у тебя возникли какие либо вопросы обзяательно"
                                                                 " пиши нашему менеджеру."
                                                                 "\nМенеджер - @Saurus_help",
    "buy_history": "Список ваших покупок:\n", "id+balik": "ID - {id}"
                                                          "\nБаланс - {amount} рублей"
                                                          "\nДата регистрации - {registered}",
    "referal_system": "Реферальная система"
                      "\n🫵 Сколько вы привели людей - {amount}"
                      "\n🔖 Ваша ссылка, которой нужно делиться - <code>https://t.me/{bot}?start={id}</code>"
                      "\n\nЧто нужно делать?"
                      "\n☑️️ Скопировать свою ссылку и распространять везде где только можно:"
                      "\nбеседы вк, чаты телеграмм, друзьям и везде, где только можно.",
    "captcha_wrong": "❌ Вы ошиблись в капче!", "captcha_accept": "✅ Капча введена правильно!",
    "cart": "Ваши товары в корзине:", "course_select": "{description}\n \n<b>Цена курса:</b> {price}руб.",
    "course_already_bought": "Курс уже куплен!",
    "course_buy_confirm": "Вы точно хотите приобрести курс {name} стоимостью {price} рублей?",
    "course_bought": "Спасибо за покупку курса {name}!\n Заходи в каналы ниже:\n{urls}",
    "free_courses": "Тут будут бесплатные курсы", "paid_courses": "Тут будут платные курсы",
    "send_promo": "Введите промокод:", "del_cart": "Убрано из корзины", "add_cart": "Добавлено в корзину",
    "accept_buy_cart": "Подтверждение покупки из корзины на сумму {amount} рублей",
    "invites_send": "Приглашения в каналы:\n{urls}",
    "select_the_course_to_delete_from_the_trash": "Выберите курс для удаления из корзины",
    "any": "Любого",
    "sorry_error": "Извините, произошла ошибка!",
    "activate_promo_bal": "Промокод активирован!\nНа баланс зачислено {amount} рублей",
    "promo_discount": "Промокод активирован!\nВаша скидка {discount}%",
    "promo_discount2": "Вы нашли промокод на скидку, однако его можно применить только на товары!\n"
                       "Ваша скидка: {discount}%",
    "promo_not_search": "Промокод не найден, попробуйте снова!",
    "not_enough_balance": "Не хватает средств пополните баланс",
    "secretchannel_promo": "Промокод активирован!\nСекретный канал получен! Заходи скорее: {invite_channel}",
    "course_unavailable": "Этот курс временно недоступен, извините!",
    "drop_check_translation": "<b>Пришлите полный чек в бота или скрин перевода с вашего банка. "
                              "Скидывать в формате фото</b>",
    "drop_check_translation_ok": "✅ На ваш баланс зачислено {amount} рублей.",
    "drop_check_translation_fail": "❌ Пополнение баланса на {amount} рублей отклонено!\n"
                                   "Если это ошибка, напишите менеджеру - @Saurus_help\n"
                                   "И перешлите это сообщение, <b>ни в коем случае не пытайтесь обмануть менеджера</b> "
                                   "⚠️\n\nTransaction ID: <code>{uid}</code>"
}

buttons = {
    "manager": "Менеджер",
    "go_to_bot": "Перейти к боту",
    "buy_course": "💳 Купить курсы",
    "personal_cabinet": "👨‍💻 Личный кабинет",
    "cart": "🛒 Корзина",
    "help": "📝 Помощь",
    "balance_topup": "💰 Пополнить баланс",
    "free_courses": "☑️ Бесплатные курсы",
    "add_category": "➕ Добавление категорий",
    "add_product": "➕ Добавление товаров",
    "category_discount": "🔖 Скидка на категорию",
    "direct_link_to_product": "🔗 Прямая ссылка на товар",
    "direct_link_to_category": "🔗 Прямая ссылка на категорию",
    "product_discount": "🔖 Скидка на товар",
    "set_desc": "📜 Изменение описания",
    "set_photo": "📷 Изменение фото",
    "set_cost": "💲 Изменение цены",
    "set_costs": "💲 Изменение цен",
    "set_channel": "💬 Изменение канала",
    "del_category": "➖ Удаление категории",
    "back": "Обратно",
    "history_buy": "История покупок",
    "history_replenishment": "История пополнение баланса",
    "buy2_course": "Оплатить курс",
    "delete_course": "Удалить курс",
    "apply_promo": "Применить промокод",
    "referal_system": "Реферальная система",
    "activate_promo": "Активация промокода",
    "replenishment_balance": "Пополнить баланс",
    "accept_buy": "Подтвердить покупку",
    "purchase_now": "Приобрести сейчас",
    "i_purchase": "Я оплатил",
    "sber": "Сбер",
    "tinkoff": "Тинькофф",
    "sbp": "СБП",
    "raifaisen": "Райфайзен",
    "instruktion": "Инструкция по боту",
    "Tos": "Соглашение"
}

description_keys = {
    "messages": {
        "drop_check_translation": "Чек оплаты (дроп)",
        "any": "Любой",
        "sorry_error": "Извините, произошла ошибка",
        "activate_promo_bal": "Промокод на баланс",
        "drop_check_translation_ok": "Баланс пополнен (дроп)",
        "drop_check_translation_fail": "Баланс не пополнен (дроп)",
        "promo_discount": "Промокод на скидку",
        "promo_discount2": "Промокод который нашёл человек только на товары",
        "promo_not_search": "Промокод не найден",
        "not_enough_balance": "Не хватает средств",
        "secretchannel_promo": "Секретный канал по промокоду",
        "cart": "Товары в корзине",
        "send_promo": "Ввод промокода",
        "accept_buy_cart": "Подтверждение покупки в корзине",
        "select_the_course_to_delete_from_the_trash": "Выбрать курс прежде чем удалять из корзины",
        "invites_send": "Приглашения в каналы отправлены",
        "del_cart": "Удаленно из корзины",
        "add_cart": "Добавлено в корзину",
        "referal_system": "Реферальная система",
        "captcha_wrong": "Капча введена не правильно",
        "cart_empty": "Корзина пуста",
        "oplata_created_card": "Сообщение с оплатой",
        "oplata_created_form": "Сообщение с оплатой (ссылка)",
        "bank_select": "Выбор банка",
        "help_message": "Помощь",
        "banned_user": "Забанен",
        "subscribe": "Подписка на каналы",
        "captcha": "Ввести капчу",
        "welcome": "Привествие",
        "cancel": "Отмена",
        "pay_error": "Оплата ошибка",
        "pay_success": "Оплата успешно",
        "pay_create": "Оплата создана",
        "pay_error2": "Оплата не пришла (алёрт)",
        "oplata_created": "Создание оплаты",
        "pay_notsend": "Оплата не пришла",
        "pay_accept": "Оплата принята",
        "pay_history": "Список пополений баланса",
        "pay_error_history": "История покупок пуста",
        "not_buy": "Ничего не купленно",
        "not_replenishment": "Ничего не пополнено",
        "subscribe2": "Нужно подписаться на каналы",
        "free_courses": "Бесплатные курсов",
        "paid_courses": "Платные курсы",
        "thx": "Подписался на каналы",
        "buy_history": "История покупок",
        "id+balik": "Профиль",
        "captcha_accept": "Капча введена правильно",
        "course_select": "Выбор курса для оплаты",
        "course_already_bought": "Курс уже куплен",
        "course_buy_confirm": "Подтверждение покупки курса",
        "course_bought": "Курс куплен",
        "course_unavailable": "Курс недоступен"
    },
    "buttons": {
        "manager": "Менеджер",
        "go_to_bot": "Перейти к боту",
        "buy_course": "Купить курсы ",
        "personal_cabinet": "ЛК",
        "help": "Помощь",
        "balance_topup": "Пополнение баланса",
        "free_courses": "Бесплатные курсов",
        "add_category": "Добавление категорий",
        "add_product": "Добавление товаров",
        "category_discount": "Скидка на категорию",
        "direct_link_to_product": "Прямая ссылка на товар",
        "direct_link_to_category": "Прямая ссылка на категорию",
        "product_discount": "Скидка на товар",
        "set_desc": "Изменение описания",
        "set_photo": "Изменение фото",
        "set_cost": "Изменение цены",
        "set_costs": "Изменение цен",
        "set_channel": "Изменение канала",
        "del_category": "Удаление категории",
        "cart": "Корзина",
        "back": "Обратно",
        "history_buy": "История покупок",
        "history_replenishment": "История пополнение баланса",
        "referal_system": "Реферальная система",
        "activate_promo": "Активация промокода",
        "replenishment_balance": "Пополнить баланс",
        "accept_buy": "Подтвердить покупку",
        "purchase_now": "Приобрести сейчас",
        "i_purchase": "Я оплатил",
        "buy2_course": "Оплатить курс",
        "delete_course": "Удалить курс",
        "apply_promo": "Применение промокода",
        "sber": "Сбер",
        "tinkoff": "Тинькофф",
        "sbp": "СБП",
        "raifaisen": "Райфайзен",
        "instruktion": "Инструкция по боту",
        "Tos": "Соглашение"
    }
}


def set_message(key: str, value: str):
    # messages[key] = value
    try:
        key = f"msg-{key}"
        msg = Cache.cachedLocale(key)

        if msg is None:
            return

        msg.content = value
        msg.save()
    except:
        print(traceback.format_exc())


def set_button(key: str, value: str):
    # buttons[key] = value
    try:
        key = f"btn-{key}"
        btn = Cache.cachedLocale(key)

        if btn is None:
            return

        btn.content = value
        btn.save()
    except:
        print(traceback.format_exc())


def get_message(key: str, **kwargs) -> str:
    try:
        key = f"msg-{key}"
        msg = Cache.cachedLocale(key)

        if msg is None:
            msg = key
        else:
            msg = msg.content

        for key in kwargs.keys():
            msg = msg.replace("{" + key + "}", str(kwargs.get(key)))

        return msg
    except:
        print(traceback.format_exc())
        return "ключ не найден (ошибка поиска)"


def get_button(key: str, **kwargs) -> str:
    try:
        key = f"btn-{key}"
        msg = Cache.cachedLocale(key)

        if msg is None:
            msg = key
        else:
            msg = msg.content

        for key in kwargs.keys():
            msg = msg.replace("{" + key + "}", str(kwargs.get(key)))

        return msg
    except:
        print(traceback.format_exc())
        return "ключ не найден (ошибка поиска)"


def get_descripion_for_yebanskiy_key(category: str, key: str) -> str:
    return category if not (category in description_keys) else key if key not in description_keys[category] else \
        description_keys[category][key]


def start():
    values = db.LocalizedMessage.select()
    inserted = 0
    loaded = 0

    for name, value in buttons.items():
        try:
            clr_name = name
            name = f"btn-{name}"
            if len(values.where(db.LocalizedMessage.name == name)) > 0:
                lcl = values.where(db.LocalizedMessage.name == name).get()

                upd = False

                if lcl.default != value:
                    upd = True
                    lcl.default = value

                dsc_key = description_keys['buttons'][clr_name] if clr_name in description_keys[
                    'buttons'] else lcl.description

                if lcl.description != dsc_key:
                    upd = True
                    lcl.description = dsc_key

                if upd:
                    lcl.save()
                    inserted += 1
                continue

            db.LocalizedMessage.create(name=name, content=value, default=value,
                                       description=description_keys['buttons'][clr_name])
            inserted += 1
        except:
            print(f"Ошибка при вставке btn-{name}!")
            print(traceback.format_exc())

        if Cache.cachedLocale(name) is None:
            print(f"Ошибка при кешировании btn-{name}!")
        else:
            loaded += 1

    for name, value in messages.items():
        try:
            clr_name = name
            name = f"msg-{name}"
            if len(values.where(db.LocalizedMessage.name == name)) > 0:
                lcl = values.where(db.LocalizedMessage.name == name).get()

                upd = False

                if lcl.default != value:
                    upd = True
                    lcl.default = value

                dsc_key = description_keys['messages'][clr_name] if clr_name in description_keys[
                    'messages'] else lcl.description

                if lcl.description != dsc_key:
                    upd = True
                    lcl.description = dsc_key

                if upd:
                    lcl.save()
                    inserted += 1
                continue

            db.LocalizedMessage.create(name=name, content=value, default=value,
                                       description=description_keys['messages'][clr_name])
            inserted += 1
        except:
            print(f"Ошибка при вставке msg-{name}!")
            print(traceback.format_exc())

        if Cache.cachedLocale(name) is None:
            print(f"Ошибка при кешировании msg-{name}!")
        else:
            loaded += 1

    if inserted > 0:
        print(f"  ... Вставлено {inserted} строк с локализацией")
    if loaded > 0:
        print(f"  ... Кешированно {loaded} строк с локализацией")
