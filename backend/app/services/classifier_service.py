import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.classification_rule import ClassificationRule
from app.models.enums import ClassificationStatus, MatchType, TransactionType
from app.utils.text_normalizer import normalize_text


class ClassifierService:
    def __init__(self, db: Session):
        self.db = db

    def classify(self, description: str) -> tuple[int | None, TransactionType | None, ClassificationStatus]:
        description_clean = normalize_text(description)
        rules = self.db.scalars(
            select(ClassificationRule)
            .where(ClassificationRule.active.is_(True))
            .order_by(ClassificationRule.priority.asc(), ClassificationRule.id.asc())
        ).all()

        for rule in rules:
            if self._matches(description_clean, rule):
                return rule.chart_account_id, rule.transaction_type, ClassificationStatus.automatic

        return None, None, ClassificationStatus.pending

    def apply_to_payload(self, payload: dict) -> dict:
        chart_account_id, transaction_type, status = self.classify(payload["description_clean"])
        amount = payload["amount"]
        payload["chart_account_id"] = chart_account_id
        payload["transaction_type"] = transaction_type or (
            TransactionType.income if amount >= 0 else TransactionType.expense
        )
        payload["classification_status"] = status
        if transaction_type in {TransactionType.transfer, TransactionType.reserve}:
            payload["is_internal_transfer"] = True
        return payload

    def _matches(self, description_clean: str, rule: ClassificationRule) -> bool:
        keyword = normalize_text(rule.keyword)
        if rule.match_type == MatchType.equals:
            return description_clean == keyword
        if rule.match_type == MatchType.starts_with:
            return description_clean.startswith(keyword)
        if rule.match_type == MatchType.regex:
            try:
                return re.search(rule.keyword, description_clean, re.IGNORECASE) is not None
            except re.error:
                return False
        return keyword in description_clean
