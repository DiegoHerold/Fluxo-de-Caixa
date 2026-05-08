from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.chart_account import ChartAccount
from app.models.enums import FormulaOperation, FormulaValueMode
from app.models.report_indicator import ReportIndicator, ReportIndicatorTerm
from app.models.transaction import Transaction
from app.schemas.report_indicator_schema import (
    ReportIndicatorCreate,
    ReportIndicatorEvaluation,
    ReportIndicatorRead,
    ReportIndicatorTermCreate,
    ReportIndicatorTermEvaluation,
    ReportIndicatorTermRead,
    ReportIndicatorUpdate,
)
from app.services.formula_engine import FormulaEngine, FormulaError
from app.services.chart_account_seed import seed_default_chart_accounts
from app.utils.dates import month_bounds
from app.utils.text_normalizer import normalize_text


class ReportIndicatorService:
    def __init__(self, db: Session):
        self.db = db
        self.formula_engine = FormulaEngine()

    def list(self, include_inactive: bool = False) -> list[ReportIndicatorRead]:
        stmt = (
            select(ReportIndicator)
            .options(selectinload(ReportIndicator.terms).selectinload(ReportIndicatorTerm.chart_account))
            .order_by(ReportIndicator.display_order, ReportIndicator.name)
        )
        if not include_inactive:
            stmt = stmt.where(ReportIndicator.is_active.is_(True))
        return [self._to_read(item) for item in self.db.scalars(stmt)]

    def get(self, indicator_id: int) -> ReportIndicator:
        item = self.db.scalar(
            select(ReportIndicator)
            .options(selectinload(ReportIndicator.terms).selectinload(ReportIndicatorTerm.chart_account))
            .where(ReportIndicator.id == indicator_id)
        )
        if not item:
            raise HTTPException(status_code=404, detail="Indicador não encontrado")
        return item

    def create(self, payload: ReportIndicatorCreate) -> ReportIndicatorRead:
        item = ReportIndicator(**payload.model_dump(exclude={"terms"}))
        self.db.add(item)
        self.db.flush()
        self._replace_terms(item, payload.terms)
        self.db.commit()
        self.db.refresh(item)
        return self._to_read(self.get(item.id))

    def update(self, indicator_id: int, payload: ReportIndicatorUpdate) -> ReportIndicatorRead:
        item = self.get(indicator_id)
        data = payload.model_dump(exclude_unset=True, exclude={"terms"})
        for field, value in data.items():
            setattr(item, field, value)
        if payload.terms is not None:
            self._replace_terms(item, payload.terms)
        self.db.commit()
        return self._to_read(self.get(item.id))

    def delete(self, indicator_id: int) -> ReportIndicatorRead:
        item = self.get(indicator_id)
        deleted = self._to_read(item)
        self.db.delete(item)
        self.db.commit()
        return deleted

    def evaluate(self, month: str, surface: str | None = None) -> list[ReportIndicatorEvaluation]:
        stmt = (
            select(ReportIndicator)
            .options(selectinload(ReportIndicator.terms).selectinload(ReportIndicatorTerm.chart_account))
            .where(ReportIndicator.is_active.is_(True))
            .order_by(ReportIndicator.display_order, ReportIndicator.name)
        )
        if surface == "dashboard":
            stmt = stmt.where(ReportIndicator.show_on_dashboard.is_(True))
        if surface == "reports":
            stmt = stmt.where(ReportIndicator.show_on_reports.is_(True))
        return [self._evaluate_indicator(item, month) for item in self.db.scalars(stmt)]

    def seed_defaults(self) -> list[ReportIndicatorRead]:
        seed_default_chart_accounts(self.db)

        defaults = [
            {
                "name": "Sobra/Falta do mês",
                "description": "Receita menos despesas fixas, variáveis e obrigações. É o principal termômetro do mês.",
                "result_label": "Sobrou/Faltou",
                "positive_is_good": True,
                "display_order": 1,
                "terms": [
                    ("1", FormulaOperation.add, FormulaValueMode.inflow, "Receita"),
                    ("2", FormulaOperation.subtract, FormulaValueMode.outflow, "Despesas fixas"),
                    ("3", FormulaOperation.subtract, FormulaValueMode.outflow, "Despesas variáveis"),
                    ("4", FormulaOperation.subtract, FormulaValueMode.outflow, "Dívidas e obrigações"),
                ],
            },
            {
                "name": "Custo de vida",
                "description": "Quanto o mês custou sem considerar transferências, ajustes e movimentações de reserva.",
                "result_label": "Custo",
                "positive_is_good": False,
                "display_order": 2,
                "terms": [
                    ("2", FormulaOperation.add, FormulaValueMode.outflow, "Fixas"),
                    ("3", FormulaOperation.add, FormulaValueMode.outflow, "Variáveis"),
                    ("4", FormulaOperation.add, FormulaValueMode.outflow, "Obrigações"),
                ],
            },
            {
                "name": "Capacidade de guardar",
                "description": "Receita menos gastos reais e movimentações para objetivos/reservas.",
                "result_label": "Livre após reservas",
                "positive_is_good": True,
                "display_order": 3,
                "terms": [
                    ("1", FormulaOperation.add, FormulaValueMode.inflow, "Receita"),
                    ("2", FormulaOperation.subtract, FormulaValueMode.outflow, "Fixas"),
                    ("3", FormulaOperation.subtract, FormulaValueMode.outflow, "Variáveis"),
                    ("4", FormulaOperation.subtract, FormulaValueMode.outflow, "Obrigações"),
                    ("8", FormulaOperation.subtract, FormulaValueMode.outflow, "Reservas e objetivos"),
                ],
            },
            {
                "name": "Margem após essenciais",
                "description": "Quanto sobra depois de pagar contas fixas, obrigações e gastos básicos de sobrevivência.",
                "result_label": "Livre após essenciais",
                "positive_is_good": True,
                "display_order": 4,
                "terms": [
                    ("1", FormulaOperation.add, FormulaValueMode.inflow, "Receita"),
                    ("2", FormulaOperation.subtract, FormulaValueMode.outflow, "Fixas"),
                    ("4", FormulaOperation.subtract, FormulaValueMode.outflow, "Obrigações"),
                    ("3.1", FormulaOperation.subtract, FormulaValueMode.outflow, "Alimentação"),
                    ("3.2", FormulaOperation.subtract, FormulaValueMode.outflow, "Transporte"),
                    ("3.3", FormulaOperation.subtract, FormulaValueMode.outflow, "Saúde"),
                ],
            },
            {
                "name": "Gasto essencial",
                "description": "Contas fixas, obrigações e categorias básicas que sustentam o mês.",
                "result_label": "Essenciais",
                "positive_is_good": False,
                "display_order": 5,
                "terms": [
                    ("2", FormulaOperation.add, FormulaValueMode.outflow, "Despesas fixas"),
                    ("4", FormulaOperation.add, FormulaValueMode.outflow, "Obrigações"),
                    ("3.1", FormulaOperation.add, FormulaValueMode.outflow, "Alimentação"),
                    ("3.2", FormulaOperation.add, FormulaValueMode.outflow, "Transporte"),
                    ("3.3", FormulaOperation.add, FormulaValueMode.outflow, "Saúde"),
                ],
            },
            {
                "name": "Vida flexível",
                "description": "Gastos que costumam variar mais e são bons candidatos para ajuste rápido.",
                "result_label": "Flexível",
                "positive_is_good": False,
                "display_order": 6,
                "terms": [
                    ("3.1.2", FormulaOperation.add, FormulaValueMode.outflow, "Restaurante/Lanche"),
                    ("3.4.1", FormulaOperation.add, FormulaValueMode.outflow, "Roupas"),
                    ("3.5", FormulaOperation.add, FormulaValueMode.outflow, "Lazer"),
                    ("3.4.3", FormulaOperation.add, FormulaValueMode.outflow, "Compras pessoais"),
                ],
            },
            {
                "name": "Dívidas e obrigações",
                "description": "Tudo que pesa como dívida, cartão, empréstimos, parcelamentos e contas em atraso.",
                "result_label": "Obrigatório",
                "positive_is_good": False,
                "display_order": 7,
                "terms": [
                    ("4", FormulaOperation.add, FormulaValueMode.outflow, "Dívidas e obrigações"),
                ],
            },
            {
                "name": "Impacto do cartão",
                "description": "Quanto o cartão de crédito consumiu no mês.",
                "result_label": "Cartão",
                "positive_is_good": False,
                "display_order": 8,
                "terms": [
                    ("4.1", FormulaOperation.add, FormulaValueMode.outflow, "Cartão de crédito"),
                ],
            },
            {
                "name": "Reservas enviadas",
                "description": "Valor direcionado para caixinhas, reservas e objetivos.",
                "result_label": "Guardado",
                "positive_is_good": True,
                "display_order": 9,
                "terms": [
                    ("8", FormulaOperation.add, FormulaValueMode.outflow, "Reservas e objetivos"),
                ],
            },
            {
                "name": "Retiradas de reservas",
                "description": "Entradas vindas de reservas e objetivos, útil para ver quando você precisou desfazer caixinhas.",
                "result_label": "Retirado",
                "positive_is_good": False,
                "display_order": 10,
                "terms": [
                    ("8", FormulaOperation.add, FormulaValueMode.inflow, "Retiradas de reservas"),
                ],
            },
            {
                "name": "Renda recorrente",
                "description": "Receitas previsíveis, como salário e adiantamentos.",
                "result_label": "Recorrente",
                "positive_is_good": True,
                "display_order": 11,
                "terms": [
                    ("1.1", FormulaOperation.add, FormulaValueMode.inflow, "Salário"),
                    ("1.2", FormulaOperation.add, FormulaValueMode.inflow, "Extra/Bicos"),
                ],
            },
            {
                "name": "Receitas extras",
                "description": "Entradas fora da renda principal: vendas, outros recebimentos.",
                "result_label": "Extras",
                "positive_is_good": True,
                "display_order": 12,
                "terms": [
                    ("1.3", FormulaOperation.add, FormulaValueMode.inflow, "Vendas"),
                    ("1.4", FormulaOperation.add, FormulaValueMode.inflow, "Outros recebimentos"),
                ],
            },
            {
                "name": "Moradia e serviços",
                "description": "Aluguel, água, luz, internet, telefone e assinaturas.",
                "result_label": "Moradia/serviços",
                "positive_is_good": False,
                "display_order": 13,
                "show_on_dashboard": False,
                "terms": [
                    ("2.1", FormulaOperation.add, FormulaValueMode.outflow, "Moradia"),
                    ("2.1.2", FormulaOperation.add, FormulaValueMode.outflow, "Água"),
                    ("2.1.3", FormulaOperation.add, FormulaValueMode.outflow, "Luz"),
                    ("2.1.4", FormulaOperation.add, FormulaValueMode.outflow, "Internet"),
                    ("2.2.1", FormulaOperation.add, FormulaValueMode.outflow, "Telefone"),
                    ("2.2.3", FormulaOperation.add, FormulaValueMode.outflow, "Assinaturas"),
                ],
            },
            {
                "name": "Saúde e farmácia",
                "description": "Gastos com saúde e farmácia destacados para acompanhar cuidado recorrente.",
                "result_label": "Saúde",
                "positive_is_good": False,
                "display_order": 14,
                "show_on_dashboard": False,
                "terms": [
                    ("3.3", FormulaOperation.add, FormulaValueMode.outflow, "Saúde"),
                ],
            },
            {
                "name": "Transporte e combustível",
                "description": "Deslocamento do mês separado para comparar com trabalho, rotina e lazer.",
                "result_label": "Transporte",
                "positive_is_good": False,
                "display_order": 15,
                "show_on_dashboard": False,
                "terms": [
                    ("3.2", FormulaOperation.add, FormulaValueMode.outflow, "Transporte"),
                ],
            },
            {
                "name": "Lazer e compras pessoais",
                "description": "Lazer, roupas, restaurantes e compras pessoais em um único bloco de consumo discricionário.",
                "result_label": "Consumo livre",
                "positive_is_good": False,
                "display_order": 16,
                "show_on_dashboard": False,
                "terms": [
                    ("3.1.2", FormulaOperation.add, FormulaValueMode.outflow, "Restaurante/Lanche"),
                    ("3.4.1", FormulaOperation.add, FormulaValueMode.outflow, "Roupas"),
                    ("3.5", FormulaOperation.add, FormulaValueMode.outflow, "Lazer"),
                    ("3.4.3", FormulaOperation.add, FormulaValueMode.outflow, "Compras pessoais"),
                ],
            },
            {
                "name": "Ajustes e correções",
                "description": "Volume de ajustes manuais, estornos e correções. Ajuda a perceber quando a base está exigindo manutenção.",
                "result_label": "Ajustes",
                "positive_is_good": False,
                "display_order": 17,
                "show_on_dashboard": False,
                "terms": [
                    ("6", FormulaOperation.add, FormulaValueMode.absolute, "Ajustes"),
                ],
            },
            {
                "name": "Transferências internas movimentadas",
                "description": "Total movimentado entre contas próprias. Não mede gasto real, mas ajuda a auditar fluxo entre contas e caixinhas.",
                "result_label": "Movimentado",
                "positive_is_good": False,
                "include_internal_transfers": True,
                "display_order": 18,
                "show_on_dashboard": False,
                "terms": [
                    ("5", FormulaOperation.add, FormulaValueMode.absolute, "Transferências internas"),
                ],
            },
            {
                "name": "Índice de comprometimento da renda",
                "description": "Percentual da receita consumido por fixas, variáveis e obrigações.",
                "result_label": "% comprometido",
                "result_format": "percent",
                "positive_is_good": False,
                "display_order": 19,
                "show_on_dashboard": False,
                "terms": [
                    ("1", FormulaOperation.add, FormulaValueMode.inflow, "Receita", "receita"),
                    ("2", FormulaOperation.add, FormulaValueMode.outflow, "Fixas", "fixas"),
                    ("3", FormulaOperation.add, FormulaValueMode.outflow, "Variáveis", "variaveis"),
                    ("4", FormulaOperation.add, FormulaValueMode.outflow, "Obrigações", "obrigacoes"),
                ],
                "formula_expression": "pct(fixas + variaveis + obrigacoes, receita)",
            },
            {
                "name": "Folga percentual da renda",
                "description": "Percentual da receita que sobra depois dos gastos reais principais.",
                "result_label": "% livre",
                "result_format": "percent",
                "positive_is_good": True,
                "display_order": 20,
                "show_on_dashboard": False,
                "terms": [
                    ("1", FormulaOperation.add, FormulaValueMode.inflow, "Receita", "receita"),
                    ("2", FormulaOperation.add, FormulaValueMode.outflow, "Fixas", "fixas"),
                    ("3", FormulaOperation.add, FormulaValueMode.outflow, "Variáveis", "variaveis"),
                    ("4", FormulaOperation.add, FormulaValueMode.outflow, "Obrigações", "obrigacoes"),
                ],
                "formula_expression": "pct(receita - fixas - variaveis - obrigacoes, receita)",
            },
            {
                "name": "Cenário conservador",
                "description": "Simula uma sobra/falta com variáveis 15% maiores e consumo flexível 20% maior.",
                "result_label": "Cenário prudente",
                "positive_is_good": True,
                "display_order": 21,
                "show_on_dashboard": False,
                "terms": [
                    ("1", FormulaOperation.add, FormulaValueMode.inflow, "Receita", "receita"),
                    ("2", FormulaOperation.add, FormulaValueMode.outflow, "Fixas", "fixas"),
                    ("4", FormulaOperation.add, FormulaValueMode.outflow, "Obrigações", "obrigacoes"),
                    ("3", FormulaOperation.add, FormulaValueMode.outflow, "Variáveis", "variaveis"),
                    ("3.1.2", FormulaOperation.add, FormulaValueMode.outflow, "Restaurante/Lanche", "lanche"),
                    ("3.4.1", FormulaOperation.add, FormulaValueMode.outflow, "Roupas", "roupas"),
                    ("3.5", FormulaOperation.add, FormulaValueMode.outflow, "Lazer", "lazer"),
                    ("3.4.3", FormulaOperation.add, FormulaValueMode.outflow, "Compras pessoais", "compras"),
                ],
                "formula_expression": "receita - fixas - obrigacoes - (variaveis * 1.15) - ((lanche + roupas + lazer + compras) * 0.20)",
            },
            {
                "name": "Projeção provável",
                "description": "Usa probabilidades nos termos para estimar uma sobra esperada do mês.",
                "result_label": "Sobra esperada",
                "positive_is_good": True,
                "display_order": 22,
                "show_on_dashboard": False,
                "terms": [
                    ("1.1", FormulaOperation.add, FormulaValueMode.inflow, "Salário provável", "salario", 1, 1),
                    ("1.3", FormulaOperation.add, FormulaValueMode.inflow, "Vendas prováveis", "vendas", 1, 0.5),
                    ("1.4", FormulaOperation.add, FormulaValueMode.inflow, "Outros prováveis", "outros", 1, 0.4),
                    ("2", FormulaOperation.add, FormulaValueMode.outflow, "Fixas", "fixas", 1, 1),
                    ("3", FormulaOperation.add, FormulaValueMode.outflow, "Variáveis", "variaveis", 1, 0.9),
                    ("4", FormulaOperation.add, FormulaValueMode.outflow, "Obrigações", "obrigacoes", 1, 1),
                ],
                "formula_expression": "salario + vendas + outros - fixas - variaveis - obrigacoes",
            },
            {
                "name": "Pressão de ficar negativo",
                "description": "Estimativa percentual de pressão financeira quando gastos prováveis passam da receita.",
                "result_label": "Pressão",
                "result_format": "percent",
                "positive_is_good": False,
                "display_order": 23,
                "show_on_dashboard": False,
                "terms": [
                    ("1", FormulaOperation.add, FormulaValueMode.inflow, "Receita", "receita"),
                    ("2", FormulaOperation.add, FormulaValueMode.outflow, "Fixas", "fixas"),
                    ("3", FormulaOperation.add, FormulaValueMode.outflow, "Variáveis prováveis", "variaveis", 1, 0.9),
                    ("4", FormulaOperation.add, FormulaValueMode.outflow, "Obrigações", "obrigacoes"),
                ],
                "formula_expression": "clamp(pct(max((fixas + variaveis + obrigacoes) - receita, 0), receita), 0, 100)",
            },
            {
                "name": "Taxa de poupanca potencial",
                "description": "Percentual da receita que poderia virar sobra depois de fixas, variaveis e obrigacoes.",
                "result_label": "% potencial",
                "result_format": "percent",
                "positive_is_good": True,
                "display_order": 24,
                "show_on_dashboard": False,
                "terms": [
                    ("1", FormulaOperation.add, FormulaValueMode.inflow, "Receita", "receita"),
                    ("2", FormulaOperation.add, FormulaValueMode.outflow, "Fixas", "fixas"),
                    ("3", FormulaOperation.add, FormulaValueMode.outflow, "Variaveis", "variaveis"),
                    ("4", FormulaOperation.add, FormulaValueMode.outflow, "Obrigacoes", "obrigacoes"),
                ],
                "formula_expression": "pct(max(receita - fixas - variaveis - obrigacoes, 0), receita)",
            },
            {
                "name": "Comprometimento fixo da renda",
                "description": "Mostra quanto da receita ja nasce comprometida com despesas fixas e obrigacoes.",
                "result_label": "% fixo",
                "result_format": "percent",
                "positive_is_good": False,
                "display_order": 25,
                "show_on_dashboard": False,
                "terms": [
                    ("1", FormulaOperation.add, FormulaValueMode.inflow, "Receita", "receita"),
                    ("2", FormulaOperation.add, FormulaValueMode.outflow, "Fixas", "fixas"),
                    ("4", FormulaOperation.add, FormulaValueMode.outflow, "Obrigacoes", "obrigacoes"),
                ],
                "formula_expression": "pct(fixas + obrigacoes, receita)",
            },
            {
                "name": "Pressao variavel da renda",
                "description": "Percentual da receita consumido por despesas variaveis.",
                "result_label": "% variavel",
                "result_format": "percent",
                "positive_is_good": False,
                "display_order": 26,
                "show_on_dashboard": False,
                "terms": [
                    ("1", FormulaOperation.add, FormulaValueMode.inflow, "Receita", "receita"),
                    ("3", FormulaOperation.add, FormulaValueMode.outflow, "Variaveis", "variaveis"),
                ],
                "formula_expression": "pct(variaveis, receita)",
            },
            {
                "name": "Gasto medio diario real",
                "description": "Custo medio diario aproximado do mes considerando fixas, variaveis e obrigacoes.",
                "result_label": "Media diaria",
                "positive_is_good": False,
                "display_order": 27,
                "show_on_dashboard": False,
                "terms": [
                    ("2", FormulaOperation.add, FormulaValueMode.outflow, "Fixas", "fixas"),
                    ("3", FormulaOperation.add, FormulaValueMode.outflow, "Variaveis", "variaveis"),
                    ("4", FormulaOperation.add, FormulaValueMode.outflow, "Obrigacoes", "obrigacoes"),
                ],
                "formula_expression": "(fixas + variaveis + obrigacoes) / 30",
            },
            {
                "name": "Resultado recorrente",
                "description": "Renda recorrente menos o custo de vida real. Ajuda a saber se a rotina se paga sem receitas extras.",
                "result_label": "Recorrente livre",
                "positive_is_good": True,
                "display_order": 28,
                "show_on_dashboard": False,
                "terms": [
                    ("1.1", FormulaOperation.add, FormulaValueMode.inflow, "Salario", "salario"),
                    ("1.2", FormulaOperation.add, FormulaValueMode.inflow, "Extra/Bicos", "extra"),
                    ("2", FormulaOperation.add, FormulaValueMode.outflow, "Fixas", "fixas"),
                    ("3", FormulaOperation.add, FormulaValueMode.outflow, "Variaveis", "variaveis"),
                    ("4", FormulaOperation.add, FormulaValueMode.outflow, "Obrigacoes", "obrigacoes"),
                ],
                "formula_expression": "salario + extra - fixas - variaveis - obrigacoes",
            },
            {
                "name": "Dependencia de renda extra",
                "description": "Percentual da receita vindo de vendas e outros recebimentos.",
                "result_label": "% extra",
                "result_format": "percent",
                "positive_is_good": False,
                "display_order": 29,
                "show_on_dashboard": False,
                "terms": [
                    ("1", FormulaOperation.add, FormulaValueMode.inflow, "Receita", "receita"),
                    ("1.3", FormulaOperation.add, FormulaValueMode.inflow, "Vendas", "vendas"),
                    ("1.4", FormulaOperation.add, FormulaValueMode.inflow, "Outros recebimentos", "outros"),
                ],
                "formula_expression": "pct(vendas + outros, receita)",
            },
            {
                "name": "Peso do cartao na renda",
                "description": "Percentual da receita comprometido com pagamento de cartao.",
                "result_label": "% cartao",
                "result_format": "percent",
                "positive_is_good": False,
                "display_order": 30,
                "show_on_dashboard": False,
                "terms": [
                    ("1", FormulaOperation.add, FormulaValueMode.inflow, "Receita", "receita"),
                    ("4.1", FormulaOperation.add, FormulaValueMode.outflow, "Cartao", "cartao"),
                ],
                "formula_expression": "pct(cartao, receita)",
            },
            {
                "name": "Reservas sobre renda",
                "description": "Percentual da receita enviado para caixinhas, reservas e objetivos.",
                "result_label": "% reservado",
                "result_format": "percent",
                "positive_is_good": True,
                "display_order": 31,
                "show_on_dashboard": False,
                "terms": [
                    ("1", FormulaOperation.add, FormulaValueMode.inflow, "Receita", "receita"),
                    ("8", FormulaOperation.add, FormulaValueMode.outflow, "Reservas", "reservas"),
                ],
                "formula_expression": "pct(reservas, receita)",
            },
            {
                "name": "Folga antes das reservas",
                "description": "Sobra real antes de considerar envios para caixinhas e objetivos.",
                "result_label": "Folga operacional",
                "positive_is_good": True,
                "display_order": 32,
                "show_on_dashboard": False,
                "terms": [
                    ("1", FormulaOperation.add, FormulaValueMode.inflow, "Receita", "receita"),
                    ("2", FormulaOperation.add, FormulaValueMode.outflow, "Fixas", "fixas"),
                    ("3", FormulaOperation.add, FormulaValueMode.outflow, "Variaveis", "variaveis"),
                    ("4", FormulaOperation.add, FormulaValueMode.outflow, "Obrigacoes", "obrigacoes"),
                ],
                "formula_expression": "receita - fixas - variaveis - obrigacoes",
            },
            {
                "name": "Alerta de caixa negativo",
                "description": "Retorna 1 quando o mes fecha negativo contra receitas, ou 0 quando fecha positivo.",
                "result_label": "0 ok / 1 alerta",
                "result_format": "number",
                "positive_is_good": False,
                "display_order": 33,
                "show_on_dashboard": False,
                "terms": [
                    ("1", FormulaOperation.add, FormulaValueMode.inflow, "Receita", "receita"),
                    ("2", FormulaOperation.add, FormulaValueMode.outflow, "Fixas", "fixas"),
                    ("3", FormulaOperation.add, FormulaValueMode.outflow, "Variaveis", "variaveis"),
                    ("4", FormulaOperation.add, FormulaValueMode.outflow, "Obrigacoes", "obrigacoes"),
                ],
                "formula_expression": "ifelse(receita - fixas - variaveis - obrigacoes < 0, 1, 0)",
            },
        ]
        default_names = [indicator_data["name"] for indicator_data in defaults]
        existing_by_name = {
            item.name: item
            for item in self.db.scalars(
                select(ReportIndicator)
                .options(selectinload(ReportIndicator.terms).selectinload(ReportIndicatorTerm.chart_account))
                .where(ReportIndicator.name.in_(default_names))
            )
        }
        code_to_account = {item.code: item for item in self.db.scalars(select(ChartAccount))}

        for indicator_data in defaults:
            data = dict(indicator_data)
            term_configs = data.pop("terms")
            terms: list[ReportIndicatorTermCreate] = []
            for position, term_config in enumerate(term_configs):
                code, operation, value_mode, label, variable_key, weight, probability = self._parse_seed_term(term_config)
                account = code_to_account.get(code)
                if not account:
                    continue
                terms.append(
                    ReportIndicatorTermCreate(
                        chart_account_id=account.id,
                        operation=operation,
                        value_mode=value_mode,
                        variable_key=variable_key,
                        weight=weight,
                        probability=probability,
                        include_children=True,
                        label=label,
                        position=position,
                    )
                )
            if not terms:
                continue

            payload = ReportIndicatorCreate(**data, terms=terms)
            item = existing_by_name.get(payload.name)
            if item:
                for field, value in payload.model_dump(exclude={"terms"}).items():
                    setattr(item, field, value)
                if not item.terms:
                    self._replace_terms(item, payload.terms)
                continue

            item = ReportIndicator(**payload.model_dump(exclude={"terms"}))
            self.db.add(item)
            self.db.flush()
            self._replace_terms(item, payload.terms)
            existing_by_name[item.name] = item

        self.db.commit()
        stmt = (
            select(ReportIndicator)
            .options(selectinload(ReportIndicator.terms).selectinload(ReportIndicatorTerm.chart_account))
            .where(ReportIndicator.name.in_(default_names))
            .order_by(ReportIndicator.display_order, ReportIndicator.name)
        )
        return [self._to_read(item) for item in self.db.scalars(stmt)]

    def _parse_seed_term(self, term_config) -> tuple[str, FormulaOperation, FormulaValueMode, str, str | None, Decimal, Decimal]:
        if isinstance(term_config, dict):
            return (
                term_config["code"],
                term_config["operation"],
                term_config["value_mode"],
                term_config["label"],
                term_config.get("variable_key"),
                Decimal(str(term_config.get("weight", "1"))),
                Decimal(str(term_config.get("probability", "1"))),
            )
        values = list(term_config)
        return (
            values[0],
            values[1],
            values[2],
            values[3],
            values[4] if len(values) > 4 else None,
            Decimal(str(values[5])) if len(values) > 5 else Decimal("1"),
            Decimal(str(values[6])) if len(values) > 6 else Decimal("1"),
        )

    def _replace_terms(self, item: ReportIndicator, terms) -> None:
        item.terms.clear()
        for position, term in enumerate(terms):
            data = term.model_dump()
            data["position"] = data.get("position", position)
            item.terms.append(ReportIndicatorTerm(**data))

    def _evaluate_indicator(self, indicator: ReportIndicator, month: str) -> ReportIndicatorEvaluation:
        terms: list[ReportIndicatorTermEvaluation] = []
        result = Decimal("0.00")
        variables: dict[str, Decimal] = {}
        for term in indicator.terms:
            amount = self._term_amount(indicator, term, month)
            adjusted_amount = amount * term.weight * term.probability
            contribution = adjusted_amount if term.operation == FormulaOperation.add else -adjusted_amount
            result += contribution
            chart_account = term.chart_account
            variable_key = term.variable_key or self._variable_key(term.label or chart_account.name)
            variables[variable_key] = adjusted_amount
            variables[f"raw_{variable_key}"] = amount
            variables[f"p_{variable_key}"] = term.probability
            variables[f"peso_{variable_key}"] = term.weight
            terms.append(
                ReportIndicatorTermEvaluation(
                    label=term.label or chart_account.name,
                    chart_account_id=chart_account.id,
                    chart_account_code=chart_account.code,
                    chart_account_name=chart_account.name,
                    operation=term.operation,
                    value_mode=term.value_mode,
                    include_children=term.include_children,
                    variable_key=variable_key,
                    weight=term.weight,
                    probability=term.probability,
                    amount=amount,
                    adjusted_amount=adjusted_amount,
                    contribution=contribution,
                )
            )
        if indicator.formula_expression:
            try:
                result = self.formula_engine.evaluate(indicator.formula_expression, variables)
            except FormulaError:
                result = Decimal("0.00")
        return ReportIndicatorEvaluation(
            id=indicator.id,
            name=indicator.name,
            description=indicator.description,
            result_label=indicator.result_label,
            result_format=indicator.result_format,
            formula_expression=indicator.formula_expression,
            positive_is_good=indicator.positive_is_good,
            include_internal_transfers=indicator.include_internal_transfers,
            show_on_dashboard=indicator.show_on_dashboard,
            show_on_reports=indicator.show_on_reports,
            display_order=indicator.display_order,
            result=result,
            terms=terms,
        )

    def _term_amount(self, indicator: ReportIndicator, term: ReportIndicatorTerm, month: str) -> Decimal:
        start, end = month_bounds(month)
        value_expr = self._value_expression(term.value_mode)
        stmt = (
            select(func.coalesce(func.sum(value_expr), 0))
            .select_from(Transaction)
            .join(ChartAccount, ChartAccount.id == Transaction.chart_account_id)
            .where(
                Transaction.transaction_date >= start,
                Transaction.transaction_date < end,
                self._chart_account_condition(term),
            )
        )
        if not indicator.include_internal_transfers:
            stmt = stmt.where(Transaction.is_internal_transfer.is_(False))
        return self.db.scalar(stmt) or Decimal("0.00")

    def _value_expression(self, value_mode: FormulaValueMode):
        if value_mode == FormulaValueMode.inflow:
            return func.greatest(Transaction.amount, 0)
        if value_mode == FormulaValueMode.outflow:
            return func.abs(func.least(Transaction.amount, 0))
        if value_mode == FormulaValueMode.absolute:
            return func.abs(Transaction.amount)
        return Transaction.amount

    def _chart_account_condition(self, term: ReportIndicatorTerm):
        if not term.include_children:
            return ChartAccount.id == term.chart_account_id
        code = term.chart_account.code
        return or_(ChartAccount.id == term.chart_account_id, ChartAccount.code.like(f"{code}.%"))

    def _to_read(self, item: ReportIndicator) -> ReportIndicatorRead:
        return ReportIndicatorRead(
            id=item.id,
            name=item.name,
            description=item.description,
            result_label=item.result_label,
            result_format=item.result_format,
            formula_expression=item.formula_expression,
            positive_is_good=item.positive_is_good,
            include_internal_transfers=item.include_internal_transfers,
            show_on_dashboard=item.show_on_dashboard,
            show_on_reports=item.show_on_reports,
            display_order=item.display_order,
            is_active=item.is_active,
            created_at=item.created_at,
            updated_at=item.updated_at,
            terms=[
                ReportIndicatorTermRead(
                    id=term.id,
                    chart_account_id=term.chart_account_id,
                    chart_account_code=term.chart_account.code if term.chart_account else None,
                    chart_account_name=term.chart_account.name if term.chart_account else None,
                    operation=term.operation,
                    value_mode=term.value_mode,
                    variable_key=term.variable_key,
                    weight=term.weight,
                    probability=term.probability,
                    include_children=term.include_children,
                    label=term.label,
                    position=term.position,
                )
                for term in item.terms
            ],
        )

    def _variable_key(self, label: str) -> str:
        normalized = normalize_text(label).replace(" ", "_")
        key = "".join(char for char in normalized if char.isalnum() or char == "_").strip("_")
        return key or "valor"
