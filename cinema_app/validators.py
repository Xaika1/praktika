import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

PHONE_RE = re.compile(r"^\+?[0-9][0-9\s\-()]{9,17}$")
NAME_RE = re.compile(r"^[A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё\s.\-]*$")


class ValidationError(Exception):
    pass


def required(value, field):
    value = (value or "").strip()
    if not value:
        raise ValidationError(f"Поле «{field}» не заполнено.")
    return value


def text(value, field, max_len):
    value = required(value, field)
    if len(value) > max_len:
        raise ValidationError(f"Поле «{field}» длиннее {max_len} символов.")
    return value


def integer(value, field, min_value, max_value):
    value = required(value, field)
    try:
        number = int(value)
    except ValueError:
        raise ValidationError(f"В поле «{field}» должно быть целое число.") from None
    if not min_value <= number <= max_value:
        raise ValidationError(f"«{field}»: допустимо от {min_value} до {max_value}.")
    return number


def price(value, field="Цена"):
    value = required(value, field).replace(",", ".").replace(" ", "")
    try:
        number = Decimal(value)
    except InvalidOperation:
        raise ValidationError(f"«{field}» должна быть числом, например 350 или 420.50.") from None
    if number <= 0 or number > 100000:
        raise ValidationError(f"«{field}» должна быть больше 0 и не больше 100 000.")
    if number.as_tuple().exponent < -2:
        raise ValidationError(f"У поля «{field}» не может быть больше двух знаков после запятой.")
    return number


def date(value, field="Дата"):
    value = required(value, field)
    try:
        return datetime.strptime(value, "%d.%m.%Y").date()
    except ValueError:
        raise ValidationError(f"«{field}»: введите дату в формате ДД.ММ.ГГГГ.") from None


def date_time(value, field="Начало сеанса"):
    value = required(value, field)
    try:
        return datetime.strptime(value, "%d.%m.%Y %H:%M")
    except ValueError:
        raise ValidationError(f"«{field}»: введите дату и время в формате ДД.ММ.ГГГГ ЧЧ:ММ.") from None


def person_name(value, field="ФИО"):
    value = text(value, field, 100)
    if not NAME_RE.match(value):
        raise ValidationError(f"«{field}» может содержать только буквы, пробелы, точку и дефис.")
    return " ".join(value.split())


def phone(value, field="Телефон"):
    value = text(value, field, 20)
    digits = re.sub(r"\D", "", value)
    if not PHONE_RE.match(value) or not 10 <= len(digits) <= 12:
        raise ValidationError(f"«{field}» указан неверно. Пример: +7 912 345-67-89.")
    return value
