import traceback
from typing import Any

import requests as req
import hashlib
import json

import data.db as db
import utils.Cache as Cache
import utils.Math as Math
from config import BOVAPAY
from utils.payment.PaymentSystemAPI import PaymentSystem


class Bovapay(PaymentSystem):
    def __init__(self, apikey, user_id, currency='RUB'):
        self.api = apikey
        self.user_id = user_id
        self.currency = currency

    def balance(self) -> int:
        url = 'https://bovatech.cc/v1/merchant/accounts'
        headers = {
            'Accept': 'application/json',
            'Authorization': f'{self.api}'
        }
        response_json = req.get(url, headers=headers, timeout=(15, 60)).json()['payload']

        return (int(float(response_json[0]['balance']) + float(response_json[1]['balance'])) + response_json['hold'] +
                response_json['refferal'] + response_json['hold'])

    def createOrder(self, user: int | db.User, amount: int) -> Any:
        if Cache.cachedMode("test"):
            return {"success": True, "id": f"{user.id}.{Math.current_milli_time() * Math.randInt(99, 9999)}",
                    "amount": amount, "url": "https://snowe.pw"}

        data = {}
        uniqID = str(Math.current_milli_time() * Math.randInt(99, 9999))

        def sign(params):
            return hashlib.sha1(f'{BOVAPAY.API_KEY}{params}'.encode('utf-8')).hexdigest()

        data_raw = json.dumps({"user_uuid": BOVAPAY.USER_ID, "amount": 500 if amount < 500 else amount,
                               "callback_url": "https://weebhook.site/wr0ngs1t3", "bank_name": "sberbank",
                               "payeer_identifier": f"{uniqID}",
                               "payeer_ip": "127.0.0.1", "payeer_type": "ftd"}, separators=(',', ':'))

        headers = {'Signature': sign(data_raw),
                   'Content-Type': 'application/json',
                   'Accept': 'application/json'}

        res = req.post('https://bovatech.cc/v1/p2p_transactions', data=data_raw, headers=headers).json()

        data["success"] = True
        data["id"] = res['payload']['id']
        data["amount"] = amount
        data["url"] = res['payload']['form_url']

        return data

    def createPaymentCard(self, user: int | db.User, amount: int, bank: str = None) -> Any:
        return self.createOrder(user, amount)

    def confirmPayment(self, Tid: str) -> bool:
        if Cache.cachedMode("test"):
            return True

        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json'}

        res = req.get(f'https://bovatech.cc/v1/p2p_transactions/{Tid}', headers=headers)

        try:
            return False if res.json()['payload']['state'] != 'successed' else True
        except:
            traceback.print_exc()
            print(res.content)
            return False

    def type(self) -> str:
        return "bovapay"
