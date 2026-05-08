import hashlib
from datetime import date
from decimal import Decimal


def make_fingerprint(
    account_id: int,
    transaction_date: date,
    amount: Decimal,
    description_clean: str,
    external_id: str | None = None,
) -> str:
    parts = [
        str(account_id),
        transaction_date.isoformat(),
        f"{amount:.2f}",
        description_clean.strip(),
        external_id or "",
    ]
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
