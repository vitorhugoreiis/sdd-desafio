"""Tabela de câmbio, consultável por moeda e data (plan.md §4, RN-011).

Núcleo puro: não sabe ler arquivo. Quem lê o documento externo e monta uma
`TabelaCambio` é `io/carregador_cambio.py` (DT-008).
"""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class TabelaCambio:
    taxas: dict[date, dict[str, Decimal]]

    def taxa(self, moeda: str, data: date) -> tuple[Decimal, date] | None:
        """RN-011 — taxa da própria data; sem cotação publicada nela,
        retrocede para a última data anterior que tenha aquela moeda
        (AMB-018). `None` quando não há nenhuma cotação anterior, ou a
        moeda está inteiramente ausente da tabela (AMB-019)."""
        datas_com_a_moeda = sorted(d for d, cotacoes in self.taxas.items() if d <= data and moeda in cotacoes)
        if not datas_com_a_moeda:
            return None
        data_da_cotacao = datas_com_a_moeda[-1]
        return self.taxas[data_da_cotacao][moeda], data_da_cotacao
