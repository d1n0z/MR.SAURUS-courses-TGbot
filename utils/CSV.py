import csv
import data.db as db


def export_users(name: str) -> str:
    with open(f'data/export/{name}.csv', 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["id", "username", "admin", "banned", "blocked", "captcha",
                                                  "from_referral", "referrals", "purchases", "balance", "registered"])

        writer.writeheader()
        for user in db.User.select():
            writer.writerow({
                "id": user.id,
                "username": user.username,
                "admin": "yes" if user.admin else "no",
                "banned": "yes" if user.banned else "no",
                "blocked": "yes" if user.blocked_bot else "no",
                "captcha": user.captcha if user.captcha else "",
                "from_referral": user.from_referral if user.from_referral else "",
                "referrals": user.referrals,
                "purchases": user.purchases,
                "balance": user.balance,
                "registered": user.registered.strftime('%Y-%m-%d %H:%M:%S')
            })

    return f"data/export/{name}.csv"


def export_balance_history(name: str) -> str:
    with open(f'data/export/{name}.csv', 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["id", "amount", "date"])

        writer.writeheader()
        for history in db.BalanceHistory.select():
            writer.writerow({
                "id": history.id,
                "amount": history.amount,
                "date": history.date.strftime('%Y-%m-%d %H:%M:%S')
            })

    return f"data/export/{name}.csv"


def export_purchases_history(name: str) -> str:
    with open(f'data/export/{name}.csv', 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["course", "id", "price", "discount", "date"])

        writer.writeheader()
        for purchase in db.Purchase.select():
            writer.writerow({
                "course": purchase.courseName,
                "id": purchase.id,
                "price": purchase.price,
                "discount": purchase.discount,
                "date": purchase.date.strftime('%Y-%m-%d %H:%M:%S')
            })

    return f"data/export/{name}.csv"


def export_promocode(name: str) -> str:
    with open(f'data/export/{name}.csv', 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["name", "code", "discount", "max_usages", "used", "enabled",
                                                  "created", "updated"])

        writer.writeheader()
        for promocode in db.PromoCode.select():
            writer.writerow({
                "name": promocode.name,
                "code": promocode.code,
                "discount": promocode.discount,
                "max_usages": promocode.max_usages,
                "used": promocode.used,
                "enabled": "yes" if promocode.enabled else "no",
                "created": promocode.created.strftime('%Y-%m-%d %H:%M:%S'),
                "updated": promocode.updated.strftime('%Y-%m-%d %H:%M:%S')
            })

    return f"data/export/{name}.csv"
