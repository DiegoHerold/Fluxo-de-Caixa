from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal

import pandas as pd

from app.models.enums import Direction, TransactionSource
from app.utils.fingerprint import make_fingerprint
from app.utils.money import to_decimal
from app.utils.text_normalizer import normalize_text, repair_mojibake


class BaseImporter(ABC):
    source: TransactionSource

    @abstractmethod
    def parse(self, content: bytes, filename: str, account_id: int) -> list[dict]:
        raise NotImplementedError

    def build_payload(
        self,
        *,
        account_id: int,
        transaction_date: date,
        description_original: str,
        amount: Decimal,
        external_id: str | None = None,
    ) -> dict:
        description_original = repair_mojibake(description_original).strip()
        description_clean = normalize_text(description_original)
        fingerprint = make_fingerprint(account_id, transaction_date, amount, description_clean, external_id)
        return {
            "account_id": account_id,
            "transaction_date": transaction_date,
            "description_original": description_original,
            "description_clean": description_clean,
            "amount": amount,
            "direction": Direction.in_ if amount >= 0 else Direction.out,
            "source": self.source,
            "external_id": external_id,
            "fingerprint": fingerprint,
        }

    def find_column(self, df: pd.DataFrame, candidates: list[str], required: bool = True) -> str | None:
        normalized = {normalize_text(str(column)): column for column in df.columns}
        candidate_keys = [normalize_text(candidate) for candidate in candidates]
        for key in candidate_keys:
            if key in normalized:
                return normalized[key]
        for key, original in normalized.items():
            if any(candidate in key for candidate in candidate_keys):
                return original
        if required:
            raise ValueError(f"Coluna obrigatória não encontrada. Tentativas: {', '.join(candidates)}")
        return None

    def amount(self, value: object) -> Decimal:
        return to_decimal(value)
