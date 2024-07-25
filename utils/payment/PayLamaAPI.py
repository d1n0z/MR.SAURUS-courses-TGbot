from typing import Any

import requests as req
import json
import data.db as db
import utils.Cache as Cache
import utils.Math as Math
from utils.payment.PaymentSystemAPI import PaymentSystem


class PayLama(PaymentSystem):
    def __init__(self, key):
        self.header = {"Content-Type": "application/json", "API-Key": key}

    def balance(self) -> int:
        return json.loads(
            req.post("https://admin.paylama.io/api/api/payment/get_balance",
                     headers=self.header).text)["balances"][0]["balance"]

    def createPaymentForm(self, user: int | db.User, amount: int) -> Any:
        if Cache.cachedMode("test"):
            return {"success": True, "id": f"{user.id}.{Math.current_milli_time()*Math.randInt(99, 9999)}",
                    "url": "https://test.snowe.pw/"}

        data = {}
        collected = json.loads(
            req.post("https://admin.paylama.io/api/api/payment/p2p_form",
                     headers=self.header,
                     json={
                         "payerID": str(user.id if isinstance(user, db.User) else user),
                         "amount": amount,
                         "expireAt": 216000,  # 1 hour
                         "currencyID": 1,
                         "comment": "shop"
                     }).text)

        data["success"] = collected["success"]

        if data["success"]:
            data["id"] = collected["externalID"]
            data["url"] = collected["formURL"]

        return data

    def createPaymentCard(self, user: int | db.User, amount: int, bank: str) -> Any:
        if Cache.cachedMode("test"):
            return {"success": True, "id": f"{user.id}.{Math.current_milli_time()*Math.randInt(99, 9999)}",
                    "amount": amount, "card": 5555555555555555}

        data = {}
        collected = json.loads(
            req.post("https://admin.paylama.io/api/api/payment/generate_invoice_card_transfer",
                     headers=self.header,
                     json={
                         "payerID": str(user.id if isinstance(user, db.User) else user),
                         "amount": amount,
                         "currencyID": 1,
                         "bankName": bank,
                         "comment": "shop"
                     }).text)

        data["success"] = collected["success"]

        if data["success"]:
            data["id"] = collected["externalID"]
            data["amount"] = collected["amount"]
            data["card"] = collected["card"]

        return data

    def confirmPayment(self, id: str) -> bool:
        if Cache.cachedMode("test"):
            return True

        return json.loads(
            req.post("https://admin.paylama.io/api/api/payment/confirm_invoice_card_transfer",
                     headers=self.header,
                     json={
                         "externalID": id
                     }).text
        )["success"]

    def type(self) -> str:
        return "paylama"
