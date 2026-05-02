import re
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.reserve_box import ReserveBox
from app.models.transaction import Transaction
from app.utils.text_normalizer import normalize_text


RESERVED_RE = re.compile(r"^dinheiro reservado\s+(.+)$")
WITHDRAWN_RE = re.compile(r"^dinheiro retirado\s+(.+)$")


def extract_reserve_movement(description: str, amount: Decimal) -> tuple[str, Decimal] | None:
    clean = normalize_text(description)
    reserved = RESERVED_RE.match(clean)
    if reserved:
        return _display_name(reserved.group(1)), abs(Decimal(amount))

    withdrawn = WITHDRAWN_RE.match(clean)
    if withdrawn:
        return _display_name(withdrawn.group(1)), -abs(Decimal(amount))

    return None


def _display_name(value: str) -> str:
    return " ".join(part.capitalize() for part in value.strip().split())


class ReserveService:
    def __init__(self, db: Session):
        self.db = db

    def calculate_reserves(self, account_id: int | None = None) -> list[dict]:
        manual_stmt = select(ReserveBox).where(ReserveBox.is_active.is_(True)).order_by(ReserveBox.name)
        if account_id:
            manual_stmt = manual_stmt.where(ReserveBox.account_id == account_id)
        manual_boxes = list(self.db.scalars(manual_stmt))
        manual_keys = {(box.account_id, normalize_text(box.name)) for box in manual_boxes}
        items = [
            {
                "account_id": box.account_id,
                "name": box.name,
                "balance": box.current_balance,
                "source": "manual",
            }
            for box in manual_boxes
        ]

        stmt = select(Transaction)
        if account_id:
            stmt = stmt.where(Transaction.account_id == account_id)

        totals: dict[tuple[int, str], Decimal] = {}
        for tx in self.db.scalars(stmt):
            movement = extract_reserve_movement(tx.description_clean, tx.amount)
            if movement is None:
                continue
            reserve_name, delta = movement
            if (tx.account_id, normalize_text(reserve_name)) in manual_keys:
                continue
            key = (tx.account_id, reserve_name)
            totals[key] = totals.get(key, Decimal("0.00")) + delta

        items.extend(
            {
                "account_id": account_id,
                "name": name,
                "balance": balance,
                "source": "detected",
            }
            for (account_id, name), balance in sorted(totals.items(), key=lambda item: (item[0][0], item[0][1]))
            if balance != 0
        )
        return items

    def calculate_account_reserve_balance(self, account_id: int) -> Decimal:
        return sum((max(item["balance"], Decimal("0.00")) for item in self.calculate_reserves(account_id)), Decimal("0.00"))
