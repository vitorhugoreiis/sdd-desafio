"""Documento de câmbio → TabelaCambio (plan.md §2, DT-008).

Núcleo puro não sabe ler arquivo (DT-003); esta é a fronteira de I/O que lê
o documento de câmbio e monta a estrutura que `motor/cambio.py` consulta.
"""
import json
from datetime import date
from decimal import Decimal, InvalidOperation

from src.io.erros import ErroDeEntrada, exigir
from src.motor.cambio import TabelaCambio


def carregar(caminho: str) -> TabelaCambio:
    with open(caminho, "r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo, parse_float=Decimal)
    return _para_tabela(dados)


def _para_cotacoes(mapa: dict, rotulo_base: str) -> dict[str, Decimal]:
    cotacoes = {}
    for moeda, valor in mapa.items():
        try:
            cotacoes[moeda.strip().upper()] = Decimal(valor)
        except (InvalidOperation, TypeError, ValueError):
            raise ErroDeEntrada(f"Campo invalido: {rotulo_base}.{moeda}") from None
    return cotacoes


def _para_tabela(dados: dict) -> TabelaCambio:
    taxas_bruto = exigir(dados, "taxas", "taxas")
    taxas: dict[date, dict[str, Decimal]] = {}
    for data_str, cotacoes in taxas_bruto.items():
        try:
            data_convertida = date.fromisoformat(data_str)
        except (TypeError, ValueError):
            raise ErroDeEntrada(f"Campo invalido: taxas.{data_str}") from None
        taxas[data_convertida] = _para_cotacoes(cotacoes, f"taxas.{data_str}")
    return TabelaCambio(taxas=taxas)
