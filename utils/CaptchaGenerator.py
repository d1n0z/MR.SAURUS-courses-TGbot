import concurrent.futures
import os
import random
import string
import traceback
from itertools import permutations

from PIL import Image
from claptcha import Claptcha

smallCapital_chars = {'й': 'й', 'ц': 'ц', 'у': 'у', 'к': 'ᴋ', 'е': 'ᴇ', 'н': 'н', 'г': 'ᴦ', 'ш': 'ɯ', 'щ': 'щ',
                      'з': 'з', 'ф': 'ɸ', 'ы': 'ы', 'в': 'ʙ', 'а': 'ᴀ', 'п': 'П', 'р': 'ᴩ', 'о': 'о', 'л': 'ᴧ',
                      'д': 'д', 'я': 'я',
                      'ч': 'ч', 'с': 'ᴄ', 'м': 'ʍ', 'и': 'и', 'т': 'ᴛ', 'ь': 'ь', 'ъ': 'ъ', 'х': 'х'}

captchaWords = ["Яблоко", "Солнце", "Книга", "Шарик", "Мост", "Песок", "Кофе", "Звезда", "Ключ", "Дверь", "Ручка",
                "Гора", "Цветок", "Молоко", "Стол"
                #    "кофе", "книга", "музыка", "солнце", "дождь", "путешествие", "мечта", "творчество", "вдохновение",
                #    "улыбка",
                #    "приключение", "свобода", "природа", "вечер", "звезды", "облака", "океан", "горы", "цветы",
                #    "весна",
                #    "осень", "зима", "город", "ночь", "утро", "аромат", "чувства", "вкус", "красота", "магия",
                #    "технологии",
                #    "наука", "образование", "любовь", "дружба", "семья", "здоровье", "спорт", "еда", "искусство",
                #    "театр",
                #    "кино", "мода", "стиль", "инновации", "успех", "учеба", "работа", "отдых", "смех", "игра",
                #    "тишина",
                #    "радость", "волнение", "эмоции", "фантазия", "реальность", "будущее", "прошлое", "настоящее",
                #    "тайна",
                #    "загадка", "удивление", "рассвет", "закат", "молодость", "старость", "забота", "покой",
                #    "изменение",
                #    "энергия", "стремление", "цель", "план", "судьба", "свершения", "действие", "терпение", "надежда",
                #    "вера", "разнообразие", "традиция", "общество", "культура", "история", "образы", "фразы", "мысли",
                #    "идеи",
                #    "слова"
                ]


def smallCapital(text: str) -> str:
    output_string = ''

    for char in text:
        lower_char = char.lower()

        if lower_char in smallCapital_chars:
            output_string += smallCapital_chars[lower_char]
        else:
            output_string += char

    return output_string


def randomText(length: int = 16) -> str:
    return ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + "_") for _ in range(length))


def generateCaptcha() -> str:
    cap = [i for i in os.listdir('data/captcha') if not ('ttf' in i)]
    random.shuffle(cap)
    return f'{cap[0][:-4]}'


def saveCaptcha(text: str, name: str) -> str:
    file = f"data/captcha/{name}.jpg"

    if os.path.exists(file):
        return file

    print(text, type(text))
    c = Claptcha(f'{text}', "data/captcha/font.ttf", (1500, 200), resample=Image.BICUBIC, noise=0.3)
    c.write(file)

    return file


def deleteCaptcha(name: str) -> bool:
    file = f"data/captcha/{name}.jpg"

    if not os.path.exists(file):
        return False

    os.remove(file)
    return True


def generate(captcha: str):
    saveCaptcha(captcha, captcha)


async def pre_generate_and_save_captcha():
    captchas = [os.path.splitext(file)[0] for file in os.listdir("data/captcha")]
    generated = 0
    tasks = []

    for arr_captcha in list(permutations(captchaWords, 2)):
        captcha: str = (' '.join(arr_captcha)).lower()

        if captcha in captchas:
            pass

        tasks.append(captcha)

    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        while len(tasks) - generated > 0:
            catch = []

            for captcha in range(min(len(tasks) - generated, 25)):
                catch.append(executor.submit(generate, captcha))

            concurrent.futures.wait(catch)

            generated += len(catch)
            print("  ... {:.0f}%".format(generated / len(tasks) * 100))

    print(f"  ... Пре-сгенерировано {generated} капч")
    return catch
