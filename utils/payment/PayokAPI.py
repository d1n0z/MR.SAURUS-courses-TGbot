from typing import Any

import requests as req
import hashlib
import json
import data.db as db
import utils.Cache as Cache
import utils.Math as Math
from utils.payment.PaymentSystemAPI import PaymentSystem


class Payok(PaymentSystem):
    def __init__(self, apiId, key, site, secretkey):
        self.apiId = apiId
        self.key = key
        self.site = site
        self.secret = secretkey

    def balance(self) -> int:
        data = json.loads(
            req.post("https://payok.io/api/balance",
                     data={"API_ID": self.apiId, "API_KEY": self.key}).text)
        return int(data["balance"]) + int(data["ref_balance"])


    def createPaymentForm(self, user: int | db.User, amount: int) -> Any:
        if Cache.cachedMode("test"):
            return {"success": True, "id": f"{user.id}.{Math.current_milli_time()*Math.randInt(99, 9999)}", "amount": amount, "url": "https://snowe.pw"}

        data = {}
        uniqID = str(Math.current_milli_time()*Math.randInt(99, 9999))
        sign = hashlib.md5(f"{amount}|{uniqID}|{self.site}|RUB|shop|{self.secret}".encode('utf-8')).hexdigest()
        url = f"https://payok.io/pay?shop={self.site}&payment={uniqID}&amount={amount}&desc=shop&currency=RUB&sign={sign}"
        
        try:
            Rid: int = int(req.post(url).text.split("&trpgf_transaction_id=")[1].split("',")[0])
        except:
            return {"success": False}
            print(f"Не удалось получить айди оплаты по ссылке: \"{url}\"")
        data["success"] = True
        data["id"] = Rid
        data["amount"] = amount
        data["url"] = url

        return data

    def createPaymentCard(self, user: int | db.User, amount: int, bank: str) -> Any:
        return self.createPaymentForm(user, amount)

    def confirmPayment(self, Tid: str) -> bool:
        if Cache.cachedMode("test"):
            return True

        data = json.loads(
            req.post("https://payok.io/api/transaction",
                     data={
                         "API_ID": self.apiId,
                         "API_KEY": self.key,
                         "shop": self.site,
                         "payment": Tid
                     }).text
        )

        return False if not data["status"] or data[0]["1"]["transaction_status"] == '0' else True

    def type(self) -> str:
        return "payok"
