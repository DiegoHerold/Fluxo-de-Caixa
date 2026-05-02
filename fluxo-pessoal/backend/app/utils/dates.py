from datetime import date, datetime


def parse_date(value: object) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()

    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    return datetime.fromisoformat(text).date()


def month_bounds(period_month: str) -> tuple[date, date]:
    start = datetime.strptime(period_month, "%Y-%m").date().replace(day=1)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end


def month_key(value: date) -> str:
    return value.strftime("%Y-%m")
