import time
import random


def current_milli_time():
    return round(time.time() * 1000)


def randInt(start: int = 0, end: int = 1) -> int:
    return random.randint(start, end)


def randList(elements: list):
    return random.choice(elements)


def calculateDiscount(price: float, *discounts: float) -> float:
    calculated: float = price

    for discount in discounts:
        if discount is None:
            continue

        if discount <= 0:
            continue

        calculated *= discount / 100

    return price if calculated >= price else price - calculated


def calculateDiscountDisplay(price: float, *discounts: float) -> str:
    calculated: float = calculateDiscount(price, *discounts)

    return "{:.0f}".format(price) if price == calculated else "<s>{}</s> → {:.1f}".format(price, calculated)
