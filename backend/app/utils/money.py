from decimal import Decimal, ROUND_HALF_UP
from math import isnan


def to_decimal(value: object) -> Decimal:
    if value is None or value == "":
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if isinstance(value, float) and isnan(value):
        return Decimal("0.00")
    text = str(value).strip().replace("R$", "").replace(" ", "")
    text = text.replace("\u00a0", "").replace("+", "")
    if text.startswith("(") and text.endswith(")"):
        text = f"-{text[1:-1]}"
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    return Decimal(text).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def direction_from_amount(amount: Decimal) -> str:
    return "in" if amount >= 0 else "out"
