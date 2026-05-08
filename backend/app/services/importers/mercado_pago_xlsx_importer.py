from io import BytesIO

import pandas as pd

from app.models.enums import TransactionSource
from app.services.importers.base_importer import BaseImporter
from app.utils.dates import parse_date


class MercadoPagoXLSXImporter(BaseImporter):
    source = TransactionSource.mercado_pago_xlsx

    def parse(self, content: bytes, filename: str, account_id: int) -> list[dict]:
        df = self._read_statement(content)
        date_col = self.find_column(
            df,
            ["release_date", "data", "data de liberacao", "data de liberação", "date", "data da operacao", "data da operação"],
        )
        description_col = self.find_column(
            df,
            ["transaction_type", "descricao", "descrição", "tipo de operacao", "tipo de operação", "detail"],
        )
        amount_col = self.find_column(
            df,
            [
                "transaction_net_amount",
                "valor liquido recebido",
                "valor líquido recebido",
                "valor",
                "amount",
                "valor da operacao",
                "valor da operação",
            ],
        )
        external_col = self.find_column(
            df,
            ["reference_id", "id", "codigo de operacao", "código de operação", "numero de operacao"],
            required=False,
        )

        payloads: list[dict] = []
        for _, row in df.iterrows():
            if pd.isna(row[date_col]) or pd.isna(row[amount_col]) or pd.isna(row[description_col]):
                continue
            payloads.append(
                self.build_payload(
                    account_id=account_id,
                    transaction_date=parse_date(row[date_col]),
                    description_original=str(row[description_col]),
                    amount=self.amount(row[amount_col]),
                    external_id=str(row[external_col]).strip() if external_col and pd.notna(row[external_col]) else None,
                )
            )
        return payloads

    def _read_statement(self, content: bytes) -> pd.DataFrame:
        raw = pd.read_excel(BytesIO(content), engine="openpyxl", header=None, dtype=str)
        raw = raw.dropna(how="all")
        header_index = self._find_header_index(raw)
        headers = ["" if pd.isna(value) else str(value).strip() for value in raw.iloc[header_index]]
        df = raw.iloc[header_index + 1 :].copy()
        df.columns = headers
        return df.dropna(how="all")

    def _find_header_index(self, raw: pd.DataFrame) -> int:
        required_markers = {"release_date", "transaction_type", "transaction_net_amount"}
        for position, (_, row) in enumerate(raw.iterrows()):
            values = {str(value).strip().lower() for value in row if pd.notna(value)}
            if required_markers.issubset(values):
                return position
        raise ValueError("Cabeçalho do extrato Mercado Pago não encontrado")
