from typing import Any

import random
import traceback
import data.db as db
import utils.Math as Math
from utils.payment.PaymentSystemAPI import PaymentSystem


class Drop(PaymentSystem):
    payments = {}

    def balance(self) -> int:
        return -1

    def createPaymentForm(self, user: int | db.User, amount: int) -> Any:
        pass

    def createPaymentCard(self, user: int | db.User, amount: int, bank: str) -> Any:
        
        try:
            data = {}
            uniqID = str(Math.current_milli_time()*Math.randInt(99, 9999))
            
            data["success"] = True
            data["user"] = user
            data["id"] = uniqID
            data["amount"] = amount
            
            drop = None
            if bank == "sbp":
                sel = db.Drop.select().where(db.Drop.sbp is not None)
                if len(sel) == 0:
                    raise Exception('empty')
                drop = random.choice(sel)
                data["card"] = drop.sbp
            if bank == "tinkoff":
                sel = db.Drop.select().where(db.Drop.tinkoff is not None)
                if len(sel) == 0:
                    raise Exception('empty')
                drop = random.choice(sel)
                data["card"] = drop.tinkoff
            if bank == "sberbank":
                sel = db.Drop.select().where(db.Drop.sberbank is not None)
                if len(sel) == 0:
                    raise Exception('empty')
                drop = random.choice(sel)
                data["card"] = drop.sberbank
            if bank == "raiffeisenbank":
                sel = db.Drop.select().where(db.Drop.raiffeisenbank is not None)
                if len(sel) == 0:
                    raise Exception('empty')
                drop = random.choice(sel)
                data["card"] = drop.raiffeisenbank

            data["drop"] = drop
            self.payments[uniqID] = data
        except:
            print(traceback.format_exc())
            return {"success": False}

        return data

    def confirmPayment(self, Tid: str) -> bool:
        return False

    def type(self) -> str:
        return "drop"
