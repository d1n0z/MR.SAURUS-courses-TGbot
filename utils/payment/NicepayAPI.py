from typing import Any

import requests

import data.db as db
import utils.Cache as Cache
import utils.Math as Math
from utils.payment.PaymentSystemAPI import PaymentSystem


class Nicepay(PaymentSystem):
    def __init__(self, secretkey, merchant_id, currency='RUB'):
        self.secret = secretkey
        self.merchant_id = merchant_id
        self.currency = currency

    def balance(self) -> str:
        return '?'

    def createOrder(self, user: int | db.User, amount: int) -> Any:
        if Cache.cachedMode("test"):
            return {"success": True, "id": f"{user.id}.{Math.current_milli_time() * Math.randInt(99, 9999)}",
                    "amount": amount, "url": "https://snowe.pw"}

        data = {}
        uniqID = str(Math.current_milli_time() * Math.randInt(99, 9999))
        params = {
            'merchant_id': self.merchant_id,
            'secret': self.secret,
            'order_id': uniqID,
            'customer': f"{user.id}",
            'amount': f"{amount}00",
            'currency': self.currency,
        }
        res = requests.post('https://nicepay.io/public/api/payment', data=params, timeout=(15, 60)).json()

        data["success"] = True
        data["id"] = uniqID
        data["amount"] = amount
        data["url"] = res["data"]["link"]

        return data

    def createPaymentCard(self, user: int | db.User, amount: int, bank: str = None) -> Any:
        return self.createOrder(user, amount)

    def confirmPayment(self, Tid: str) -> bool:
        if Cache.cachedMode("test"):
            return True

        try:
            res = db.NicepayPayments.get(db.NicepayPayments.order_id == Tid)
            return False if res.result != 'success' else True
        except:
            return False

    def type(self) -> str:
        return "nicepay"
