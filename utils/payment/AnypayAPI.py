from typing import Any
from urllib.parse import urlencode

import requests as req
import hashlib
import data.db as db
import utils.Cache as Cache
import utils.Math as Math
from utils.payment.PaymentSystemAPI import PaymentSystem


class Anypay(PaymentSystem):
    def __init__(self, secret, api_id, apikey, merchant_id, currency='RUB'):
        self.secret = secret
        self.api_id = api_id
        self.api = apikey
        self.merchant_id = merchant_id
        self.currency = currency

    def balance(self) -> int:
        url = f'https://anypay.io/api/balance/{self.api_id}'
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'multipart/form-data',
        }

        sign = f'balance[{self.api_id}][{self.api}]'
        params = {
            'sign': hashlib.sha256(sign.encode('utf-8')).hexdigest()
        }

        response = req.post(url, params=params, headers=headers, timeout=(15, 60))
        return response.json()['result']['balance']

    def createOrder(self, user: int | db.User, amount: int) -> Any:
        if Cache.cachedMode("test"):
            return {"success": True, "id": f"{user.id}.{Math.current_milli_time() * Math.randInt(99, 9999)}",
                    "amount": amount, "url": "https://snowe.pw"}

        data = {}
        uniqID = str(Math.current_milli_time() * Math.randInt(99, 9999))[:15]
        sign = f':'.join([
            str(self.merchant_id),
            str(uniqID),
            str(amount),
            str(self.currency),
            'Покупка курсов',
            'https://t.me/SaurusShopsbot',
            'https://t.me/SaurusShopsbot',
            str(self.secret),
        ])
        params = {
            'merchant_id': self.merchant_id,
            'pay_id': uniqID,
            'amount': amount,
            'currency': self.currency,
            'desc': 'Покупка курсов',
            'success_url': 'https://t.me/SaurusShopsbot',
            'fail_url': 'https://t.me/SaurusShopsbot',
            'sign': hashlib.sha256(sign.encode('utf-8')).hexdigest()
        }
        url = "https://anypay.io/merchant?" + urlencode(params)
        print(f'AnyPay new order: pay_id={uniqID} , amount={amount} , sign={sign}')

        data["success"] = True
        data["id"] = uniqID
        data["amount"] = amount
        data["url"] = url

        return data

    def createPaymentCard(self, user: int | db.User, amount: int, bank: None = None) -> Any:
        return self.createOrder(user, amount)

    def confirmPayment(self, Tid: str) -> bool:
        if Cache.cachedMode("test"):
            return True

        print(f'AnyPay confirm order: pay_id={Tid}, response=', end='')
        url = f'https://anypay.io/api/payments/{self.api_id}'
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'multipart/form-data',
        }
        sign = f'payments{self.api_id}{self.merchant_id}{self.api}'
        params = {
            'project_id': self.merchant_id,
            'pay_id': Tid,
            'sign': hashlib.sha256(sign.encode('utf-8')).hexdigest()
        }
        response = req.post(url, params=params, headers=headers, timeout=(15, 60)).json()['result']['payments']
        print(response)

        if response is not None:
            if len(list(response.keys())) > 0:
                if list(response.values())[0]['status'] == 'paid':
                    return True
        return False

    def type(self) -> str:
        return "anypay"
