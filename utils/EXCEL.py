import traceback

from pandas import DataFrame
import data.db as db


def export_users(name: str) -> str:
    ids = []
    usernames = []
    admins = []
    banneds = []
    blockeds = []
    captchas = []
    from_referrals = []
    referralss = []
    purchases = []
    balances = []
    registereds = []

    for user in db.User.select():
        ids.append(user.id)
        usernames.append(user.username)
        admins.append("yes" if user.admin else "no")
        banneds.append("yes" if user.banned else "no")
        blockeds.append("yes" if user.blocked_bot else "no")
        captchas.append(user.captcha if user.captcha else "")
        from_referrals.append(user.from_referral if user.from_referral else "", )
        referralss.append(user.referrals)
        purchases.append(user.purchases)
        balances.append(user.balance)
        registereds.append(user.registered.strftime('%Y-%m-%d %H:%M:%S'))

    df = DataFrame({'id': ids, 'username': usernames, 'admin': admins, 'banned': banneds, 'blocked': blockeds,
                    'captcha': captchas, 'from_referral': from_referrals, 'referrals': referralss,
                    'purchase': purchases, 'balance': balances, 'registered': registereds})
    df.to_excel(f'data/export/{name}.xlsx', index=False)

    return f"data/export/{name}.xlsx"


def export_balance_history(name: str) -> str:
    ids = []
    users = []
    usernames = []
    amounts = []
    dates = []

    for history in db.BalanceHistory.select():
        ids.append(history.id)
        users.append(history.customer.id)
        usernames.append(history.customer.username)
        amounts.append(history.amount)
        dates.append(history.date.strftime('%Y-%m-%d %H:%M:%S'))

    df = DataFrame({'id': ids, 'amount': amounts, 'date': dates})
    df.to_excel(f'data/export/{name}.xlsx', index=False)

    return f"data/export/{name}.xlsx"


def export_purchases_history(name: str) -> str:
    ids = []
    users = []
    usernames = []
    courses = []
    prices = []
    discounts = []
    dates = []

    for purchase in db.Purchase.select():
        ids.append(purchase.id)
        try:
            courses.append(purchase.course)
        except:
            courses.append(0)
        users.append(purchase.customer.id)
        usernames.append(purchase.customer.username)
        prices.append(purchase.price)
        discounts.append(purchase.discount)
        dates.append(purchase.date.strftime('%Y-%m-%d %H:%M:%S'))

    df = DataFrame({'id': ids, 'course': courses, 'user': users, 'username': usernames, 'price': prices,
                    'discount': discounts, 'date': dates})
    df.to_excel(f'data/export/{name}.xlsx', index=False)

    return f"data/export/{name}.xlsx"


def export_promocode(name: str) -> str:
    names = []
    codes = []
    discounts = []
    max_usagess = []
    useds = []
    enableds = []
    createds = []
    updateds = []

    for promocode in db.PromoCode.select():
        names.append(promocode.name)
        codes.append(promocode.code)
        discounts.append(promocode.discount)
        max_usagess.append(promocode.max_usages)
        useds.append(promocode.used)
        enableds.append("yes" if promocode.enabled else "no")
        createds.append(promocode.created.strftime('%Y-%m-%d %H:%M:%S'))
        updateds.append(promocode.updated.strftime('%Y-%m-%d %H:%M:%S'))

    df = DataFrame({'name': names, 'code': codes, 'discount': discounts, 'max_usages': max_usagess, 'used': useds,
                    'enabled': enableds, 'created': createds})
    df.to_excel(f'data/export/{name}.xlsx', index=False)

    return f"data/export/{name}.xlsx"
