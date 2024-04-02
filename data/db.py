from datetime import datetime

from peewee import *

db = SqliteDatabase('data/sqlite.db')


class BaseModel(Model):
    class Meta:
        database = db


class Settings(BaseModel):
    minimum_topup = IntegerField(default=100)
    maximum_topup = IntegerField(default=10000)
    discount = IntegerField(default=0)
    payment = IntegerField(default=0)
    sber_enabled = BooleanField(default=True)
    tinkoff_enabled = BooleanField(default=True)
    raiffaisen_enabled = BooleanField(default=True)
    sbp_enabled = BooleanField(default=True)
    bank = IntegerField(default=2)


class Info(BaseModel):
    earned = IntegerField(default=0)


class User(BaseModel):
    id = IntegerField()
    username = TextField()
    admin = BooleanField(default=False)
    banned = BooleanField(default=False)
    blocked_bot = BooleanField(default=False)
    captcha = TextField(null=True)
    from_referral = IntegerField(default=0)
    referrals = IntegerField(default=0)
    purchases = IntegerField(default=0)
    balance = IntegerField(default=0)
    registered = DateTimeField(default=datetime.now())


class FreeCourses(BaseModel):
    id = IntegerField(primary_key=True, unique=True)
    name = TextField()
    url = TextField()
    created = DateTimeField(default=datetime.now())
    updated = DateTimeField(default=datetime.now())


class PromoCode(BaseModel):
    name = TextField()
    code = TextField(unique=True)
    type = TextField(default="discount")  # discount, channel, balance
    channel = IntegerField(null=True)
    discount = IntegerField(null=True)
    amount = IntegerField(null=True)
    max_usages = IntegerField()
    used = IntegerField(default=0)
    enabled = BooleanField(default=True)
    created = DateTimeField(default=datetime.now())
    updated = DateTimeField(default=datetime.now())


class CourseCategory(BaseModel):
    id = IntegerField(primary_key=True, unique=True)
    name = TextField()
    description = TextField(null=True)
    media = TextField(null=True)
    discount = IntegerField(null=True)
    parent = IntegerField(null=True)
    enabled = BooleanField(default=True)
    created = DateTimeField(default=datetime.now())
    updated = DateTimeField(default=datetime.now())


class Course(BaseModel):
    id = IntegerField(primary_key=True, unique=True)
    name = TextField()
    media = TextField(null=True)
    description = TextField()
    category = ForeignKeyField(CourseCategory)
    price = IntegerField()
    channel = IntegerField()
    discount = IntegerField(default=0)
    created = DateTimeField(default=datetime.now())
    updated = DateTimeField(default=datetime.now())


class Purchase(BaseModel):
    id = IntegerField(primary_key=True, unique=True)
    course = ForeignKeyField(Course)
    customer = ForeignKeyField(User)
    price = IntegerField()
    discount = IntegerField(default=0)
    date = DateTimeField(default=datetime.now())


class BalanceHistory(BaseModel):
    customer = ForeignKeyField(User)
    amount = IntegerField()
    date = DateTimeField(default=datetime.now())


class LogChannel(BaseModel):
    id = IntegerField(primary_key=True, unique=True)
    name = TextField()
    channel = IntegerField()
    type = TextField()  # start, buy, balancetopup, promocodeusage, ban, unban


class SubscribeChannel(BaseModel):
    id = IntegerField(primary_key=True, unique=True)
    name = TextField()
    channel = IntegerField()


class LocalizedMessage(BaseModel):
    name = TextField()
    default = TextField()
    content = TextField()
    description = TextField()


class Drop(BaseModel):
    name = TextField()
    userid = IntegerField()
    channel = IntegerField()
    sberbank = TextField(null=True)
    sbp = TextField(null=True)
    tinkoff = TextField(null=True)
    raiffeisenbank = TextField(null=True)


db.connect()
db.create_tables(
    [Info, User, Purchase, BalanceHistory, FreeCourses, CourseCategory, Course, PromoCode, Settings, LogChannel,
     SubscribeChannel, LocalizedMessage, Drop])

if len(Info.select()) == 0:
    Info.create()
if len(Settings.select()) == 0:
    Settings.create()


def getInfo() -> Info:
    return Info.get_by_id(1)


def getSettings() -> Settings:
    return Settings.get_by_id(1)
