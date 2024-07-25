from aiogram.fsm.state import State, StatesGroup


class Profile(StatesGroup):
    promocode = State()


class Mailing(StatesGroup):
    message = State()
    confirm = State()
    button_text = State()
    button_url = State()


class BalanceTopUp(StatesGroup):
    bank = State()
    amount = State()
    waiting_payment = State()
    waiting_check = State()


class ManageBanMember(StatesGroup):
    selectUser = State()


class FreeCourseAction(StatesGroup):
    name = State()
    url = State()
    action = State()
    select_button = State()


class CourseSelection(StatesGroup):
    promocode = State()
    bank = State()
    waiting_payment = State()


class EditBotMessage(StatesGroup):
    waiting_value = State()


class PromoCodeEdit(StatesGroup):
    maxUsages = State()
    type = State()
    value = State()


class PromoCodeCreate(StatesGroup):
    name = State()
    maxUsages = State()
    type = State()
    value = State()


class Cart(StatesGroup):
    bank = State()
    waiting_payment = State()
    waiting_check = State()


class CategoryEdit(StatesGroup):
    name = State()
    description = State()
    media = State()
    discount = State()


class CategoryCreate(StatesGroup):
    name = State()
    description = State()
    media = State()
    discount = State()


class CourseEdit(StatesGroup):
    name = State()
    description = State()
    price = State()
    price_single = State()
    channel = State()
    discount = State()
    media = State()


class CourseCreate(StatesGroup):
    name = State()
    description = State()
    price = State()
    channel = State()
    discount = State()
    media = State()


class LogsCreate(StatesGroup):
    name = State()
    channel = State()


class SettingsBot(StatesGroup):
    intValue = State()
    payment = State()


class SettingsMedia(StatesGroup):
    media = State()


class SubscribeChannelCreate(StatesGroup):
    name = State()
    channel = State()


class DropCreate(StatesGroup):
    name = State()
    user = State()
    channel = State()
    sber = State()
    tinkoff = State()
    raiffeisenbank = State()
    sbp = State()
