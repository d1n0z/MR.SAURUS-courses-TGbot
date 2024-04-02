from typing import Any
from urllib.parse import urlencode

import requests as req
import hashlib
import data.db as db
import utils.Cache as Cache
import utils.Math as Math
from utils.payment.PaymentSystemAPI import PaymentSystem


class Aaio(PaymentSystem):
    def __init__(self, secretkey, apikey, merchant_id, currency='RUB'):
        self.secret = secretkey
        self.api = apikey
        self.merchant_id = merchant_id
        self.currency = currency

    def balance(self) -> int:
        url = 'https://aaio.so/api/balance'
        headers = {
            'Accept': 'application/json',
            'X-Api-Key': self.secret
        }

        response = req.post(url, headers=headers, timeout=(15, 60))
        response_json = response.json()
        return response_json['balance'] + response_json['refferal'] + response_json['hold']

    def createOrder(self, user: int | db.User, amount: int) -> Any:
        if Cache.cachedMode("test"):
            return {"success": True, "id": f"{user.id}.{Math.current_milli_time() * Math.randInt(99, 9999)}",
                    "amount": amount, "url": "https://snowe.pw"}

        data = {}
        uniqID = str(Math.current_milli_time() * Math.randInt(99, 9999))
        sign = f':'.join([
            str(self.merchant_id),
            str(amount),
            str(self.currency),
            str(self.secret),
            str(uniqID)
        ])
        params = {
            'merchant_id': self.merchant_id,
            'amount': amount,
            'currency': self.currency,
            'order_id': uniqID,
            'sign': hashlib.sha256(sign.encode('utf-8')).hexdigest(),
            'desc': 'Покупка курсов',
            'lang': 'ru'
        }
        url = "https://aaio.so/merchant/pay?" + urlencode(params)

        data["success"] = True
        data["id"] = uniqID
        data["amount"] = amount
        data["url"] = url

        return data

    def createPaymentCard(self, user: int | db.User, amount: int, bank: str = None) -> Any:
        return self.createOrder(user, amount)

    def confirmPayment(self, Tid: str) -> bool:
        if Cache.cachedMode("test"):
            return True

        url = 'https://aaio.so/api/info-pay'
        params = {
            'merchant_id': self.merchant_id,
            'order_id': Tid
        }
        headers = {
            'Accept': 'application/json',
            'X-Api-Key': self.api
        }
        response = req.post(url, data=params, headers=headers, timeout=(15, 60)).json()
        print(response)

        try:
            return False if response["type"] != 'success' or response["status"] != 'success' else True
        except:
            return False

    def type(self) -> str:
        return "payok"
