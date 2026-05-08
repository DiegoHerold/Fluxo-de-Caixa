from __future__ import annotations

import ast
from decimal import Decimal, DivisionByZero, InvalidOperation


class FormulaError(ValueError):
    pass


class FormulaEngine:
    allowed_functions = {"abs", "min", "max", "round", "safe_div", "pct", "clamp", "ifelse"}

    def evaluate(self, expression: str, variables: dict[str, Decimal]) -> Decimal:
        try:
            tree = ast.parse(expression, mode="eval")
            return self._eval(tree.body, variables)
        except FormulaError:
            raise
        except Exception as exc:
            raise FormulaError(f"Fórmula inválida: {exc}") from exc

    def _eval(self, node: ast.AST, variables: dict[str, Decimal]) -> Decimal | bool:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return node.value
            if isinstance(node.value, int | float):
                return Decimal(str(node.value))
            raise FormulaError("Use apenas números, variáveis e funções permitidas")

        if isinstance(node, ast.Name):
            if node.id not in variables:
                raise FormulaError(f"Variável desconhecida: {node.id}")
            return variables[node.id]

        if isinstance(node, ast.BinOp):
            left = self._decimal(self._eval(node.left, variables))
            right = self._decimal(self._eval(node.right, variables))
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return self._safe_div(left, right)
            if isinstance(node.op, ast.Pow):
                return Decimal(str(float(left) ** float(right)))
            raise FormulaError("Operador não permitido")

        if isinstance(node, ast.UnaryOp):
            value = self._decimal(self._eval(node.operand, variables))
            if isinstance(node.op, ast.USub):
                return -value
            if isinstance(node.op, ast.UAdd):
                return value
            raise FormulaError("Operador unário não permitido")

        if isinstance(node, ast.Compare):
            left = self._decimal(self._eval(node.left, variables))
            for op, comparator in zip(node.ops, node.comparators, strict=True):
                right = self._decimal(self._eval(comparator, variables))
                ok = (
                    isinstance(op, ast.Gt) and left > right
                    or isinstance(op, ast.GtE) and left >= right
                    or isinstance(op, ast.Lt) and left < right
                    or isinstance(op, ast.LtE) and left <= right
                    or isinstance(op, ast.Eq) and left == right
                    or isinstance(op, ast.NotEq) and left != right
                )
                if not ok:
                    return False
                left = right
            return True

        if isinstance(node, ast.IfExp):
            return self._eval(node.body if self._truthy(self._eval(node.test, variables)) else node.orelse, variables)

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in self.allowed_functions:
                raise FormulaError("Função não permitida")
            args = [self._eval(arg, variables) for arg in node.args]
            return self._call(node.func.id, args)

        raise FormulaError("Expressão não permitida")

    def _call(self, name: str, args: list[Decimal | bool]) -> Decimal:
        decimal_args = [self._decimal(arg) for arg in args]
        if name == "abs":
            return abs(decimal_args[0])
        if name == "min":
            return min(decimal_args)
        if name == "max":
            return max(decimal_args)
        if name == "round":
            places = int(decimal_args[1]) if len(decimal_args) > 1 else 2
            return decimal_args[0].quantize(Decimal(10) ** -places)
        if name == "safe_div":
            return self._safe_div(decimal_args[0], decimal_args[1])
        if name == "pct":
            return self._safe_div(decimal_args[0], decimal_args[1]) * Decimal("100")
        if name == "clamp":
            return min(max(decimal_args[0], decimal_args[1]), decimal_args[2])
        if name == "ifelse":
            return self._decimal(args[1] if self._truthy(args[0]) else args[2])
        raise FormulaError("Função não permitida")

    def _safe_div(self, left: Decimal, right: Decimal) -> Decimal:
        if right == 0:
            return Decimal("0")
        try:
            return left / right
        except (DivisionByZero, InvalidOperation):
            return Decimal("0")

    def _decimal(self, value: Decimal | bool) -> Decimal:
        if isinstance(value, bool):
            return Decimal("1") if value else Decimal("0")
        return value

    def _truthy(self, value: Decimal | bool) -> bool:
        if isinstance(value, bool):
            return value
        return value != 0
