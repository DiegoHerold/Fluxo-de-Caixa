from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.classification_rule import ClassificationRule
from app.models.enums import ClassificationStatus
from app.models.transaction import Transaction
from app.schemas.classification_rule_schema import (
    ApplyRulesSummary,
    ClassificationRuleCreate,
    ClassificationRuleRead,
    ClassificationRuleUpdate,
)
from app.services.classifier_service import ClassifierService

router = APIRouter(prefix="/classification-rules", tags=["classification rules"])


@router.post("", response_model=ClassificationRuleRead, status_code=status.HTTP_201_CREATED)
def create_rule(payload: ClassificationRuleCreate, db: Session = Depends(get_db)):
    rule = ClassificationRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)

    # Aplica a nova regra às transações pendentes que coincidem
    if rule.active:
        classifier = ClassifierService(db)
        pending = list(db.scalars(select(Transaction).where(Transaction.classification_status == ClassificationStatus.pending)))
        for tx in pending:
            chart_account_id, transaction_type, status = classifier.classify(tx.description_clean)
            if status == ClassificationStatus.automatic and chart_account_id and transaction_type:
                tx.chart_account_id = chart_account_id
                tx.transaction_type = transaction_type
                tx.classification_status = status
        db.commit()

    return rule


@router.get("", response_model=list[ClassificationRuleRead])
def list_rules(active_only: bool = False, db: Session = Depends(get_db)):
    stmt = select(ClassificationRule).order_by(ClassificationRule.priority, ClassificationRule.keyword)
    if active_only:
        stmt = stmt.where(ClassificationRule.active.is_(True))
    return list(db.scalars(stmt))


@router.put("/{rule_id}", response_model=ClassificationRuleRead)
def update_rule(rule_id: int, payload: ClassificationRuleUpdate, db: Session = Depends(get_db)):
    rule = db.get(ClassificationRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Regra não encontrada")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}", response_model=ClassificationRuleRead)
def deactivate_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.get(ClassificationRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Regra não encontrada")
    rule.active = False
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule_permanent(rule_id: int, db: Session = Depends(get_db)):
    rule = db.get(ClassificationRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Regra não encontrada")
    db.delete(rule)
    db.commit()


@router.post("/apply-to-pending", response_model=ApplyRulesSummary)
def apply_rules_to_pending(db: Session = Depends(get_db)):
    classifier = ClassifierService(db)
    pending = list(db.scalars(select(Transaction).where(Transaction.classification_status == ClassificationStatus.pending)))
    updated = 0
    for tx in pending:
        chart_account_id, transaction_type, status = classifier.classify(tx.description_clean)
        if status == ClassificationStatus.automatic and chart_account_id and transaction_type:
            tx.chart_account_id = chart_account_id
            tx.transaction_type = transaction_type
            tx.classification_status = status
            updated += 1
    db.commit()
    remaining = db.scalar(
        select(func.count(Transaction.id)).where(Transaction.classification_status == ClassificationStatus.pending)
    ) or 0
    return ApplyRulesSummary(updated=updated, remaining_pending=remaining)
