"""Herramientas sin LLM: acotadas, testeables y con errores controlados."""

from __future__ import annotations

import ast
import operator
import re
from typing import Any


def web_search(query: str, max_results: int = 4) -> list[dict[str, str]]:
    """Busca fuentes públicas con DuckDuckGo y devuelve título, URL y extracto."""
    try:
        from ddgs import DDGS

        raw = DDGS().text(query, max_results=max_results)
        return [
            {
                "title": str(item.get("title", "Sin título")),
                "url": str(item.get("href", "")),
                "snippet": str(item.get("body", "")),
            }
            for item in raw
        ]
    except Exception as exc:  # La demo debe responder aun sin conexión.
        return [{"title": "Búsqueda no disponible", "url": "", "snippet": f"Error: {exc}"}]


_BINARY: dict[type[ast.operator], Any] = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
}
_UNARY: dict[type[ast.unaryop], Any] = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def safe_calculate(expression: str) -> str:
    """Evalúa únicamente aritmética básica; nunca ejecuta código Python arbitrario."""
    if len(expression) > 120:
        return "Expresión demasiado extensa."
    try:
        tree = ast.parse(expression.replace(",", "."), mode="eval")
        value = _evaluate(tree.body)
        return str(round(value, 6))
    except (SyntaxError, ValueError, TypeError, ZeroDivisionError, OverflowError):
        return "No pude calcular esa expresión de forma segura."


def _evaluate(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
        left, right = _evaluate(node.left), _evaluate(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 10:
            raise ValueError("Potencia fuera de rango")
        return float(_BINARY[type(node.op)](left, right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return float(_UNARY[type(node.op)](_evaluate(node.operand)))
    raise ValueError("Operación no permitida")


_POSITIVE = {"bueno", "excelente", "genial", "me encanta", "positivo", "feliz", "éxito"}
_NEGATIVE = {"malo", "terrible", "preocupa", "riesgo", "fracaso", "odio", "negativo"}


def sentiment_analysis(text: str) -> dict[str, str]:
    """Clasificador transparente por léxico para una primera señal de sentimiento."""
    tokens = set(re.findall(r"[a-záéíóúñ]+", text.lower()))
    positive = sum(word in text.lower() or word in tokens for word in _POSITIVE)
    negative = sum(word in text.lower() or word in tokens for word in _NEGATIVE)
    label = "positivo" if positive > negative else "negativo" if negative > positive else "neutral"
    return {"sentiment": label, "positive_hits": str(positive), "negative_hits": str(negative)}
