from io import BytesIO
import re
from datetime import date

try:
    from ofxparse import OfxParser
except ImportError:  # pragma: no cover - dependência instalada no container
    OfxParser = None

from app.models.enums import TransactionSource
from app.services.importers.base_importer import BaseImporter
from app.utils.money import to_decimal
from app.utils.text_normalizer import repair_mojibake


class NubankOFXImporter(BaseImporter):
    source = TransactionSource.nubank_ofx

    def parse(self, content: bytes, filename: str, account_id: int) -> list[dict]:
        if OfxParser is None:
            return self._parse_fallback(content, account_id)

        try:
            ofx = OfxParser.parse(BytesIO(content))
        except Exception:
            return self._parse_fallback(content, account_id)

        payloads: list[dict] = []
        for account in ofx.accounts:
            if not account.statement:
                continue
            for transaction in account.statement.transactions:
                description = repair_mojibake(transaction.memo or transaction.payee or transaction.type or "Movimentação OFX")
                payloads.append(
                    self.build_payload(
                        account_id=account_id,
                        transaction_date=transaction.date.date(),
                        description_original=description,
                        amount=to_decimal(transaction.amount),
                        external_id=transaction.id,
                    )
                )
        return payloads

    def _parse_fallback(self, content: bytes, account_id: int) -> list[dict]:
        text = repair_mojibake(content.decode("utf-8-sig", errors="replace"))
        blocks = re.findall(r"<STMTTRN>(.*?)(?=</STMTTRN>|<STMTTRN>|</BANKTRANLIST>)", text, flags=re.DOTALL | re.IGNORECASE)
        payloads: list[dict] = []
        for block in blocks:
            posted = self._tag(block, "DTPOSTED")
            amount = self._tag(block, "TRNAMT")
            if not posted or not amount:
                continue
            description = self._tag(block, "MEMO") or self._tag(block, "NAME") or self._tag(block, "TRNTYPE") or "Movimentação OFX"
            payloads.append(
                self.build_payload(
                    account_id=account_id,
                    transaction_date=self._ofx_date(posted),
                    description_original=description,
                    amount=to_decimal(amount),
                    external_id=self._tag(block, "FITID"),
                )
            )
        return payloads

    def _tag(self, block: str, tag: str) -> str | None:
        match = re.search(rf"<{tag}>(.*?)(?:</{tag}>|<|\r?\n)", block, flags=re.DOTALL | re.IGNORECASE)
        if not match:
            return None
        return repair_mojibake(match.group(1).strip())

    def _ofx_date(self, value: str) -> date:
        compact = value.strip()[:8]
        return date(int(compact[:4]), int(compact[4:6]), int(compact[6:8]))
