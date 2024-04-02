from typing import Any
import data.db as db


class PaymentSystem:
    def balance(self) -> int:
        pass

    def createPaymentForm(self, user: int | db.User, amount: int) -> Any:
        pass

    def createPaymentCard(self, user: int | db.User, amount: int, bank: str = None) -> Any:
        pass

    def confirmPayment(self, id: str) -> bool:
        pass

    def type(self) -> str:
        pass
