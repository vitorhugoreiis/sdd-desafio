"""RN-011 — conversão cambial: TabelaCambio pura, com retrocesso de data
(spec.md, AMB-018/019). A tradução para recusa efetiva (Parecer) é T-030;
aqui o contrato é só a consulta: par (taxa, data_da_cotacao) ou None."""
from datetime import date
from decimal import Decimal

from src.motor.cambio import TabelaCambio

TAXAS = {
    date(2026, 7, 14): {"USD": Decimal("5.44"), "EUR": Decimal("5.93")},
    date(2026, 7, 15): {"USD": Decimal("5.39"), "EUR": Decimal("5.88")},
    date(2026, 7, 17): {"USD": Decimal("5.47"), "EUR": Decimal("5.96")},
}


def test_rn_011_taxa_da_data_exata():
    tabela = TabelaCambio(taxas=TAXAS)

    assert tabela.taxa("EUR", date(2026, 7, 15)) == (Decimal("5.88"), date(2026, 7, 15))


def test_rn_011_data_sem_cotacao_usa_ultima_anterior():
    # 18/07 e sabado, sem cotacao publicada — retrocede ate 17/07 (AMB-018).
    tabela = TabelaCambio(taxas=TAXAS)

    assert tabela.taxa("EUR", date(2026, 7, 18)) == (Decimal("5.96"), date(2026, 7, 17))


def test_rn_011_sem_cotacao_anterior_recusa():
    tabela = TabelaCambio(taxas=TAXAS)

    assert tabela.taxa("EUR", date(2026, 7, 13)) is None


def test_rn_011_moeda_ausente_de_toda_tabela_recusa():
    # AMB-019 — GBP nunca aparece em nenhuma data desta tabela.
    tabela = TabelaCambio(taxas=TAXAS)

    assert tabela.taxa("GBP", date(2026, 7, 21)) is None


def test_rn_011_retrocede_so_ate_a_data_com_a_moeda_pedida():
    # USD tem cotacao em 14, 15 e 17; se eu pedir EUR em 16, tem que cair em
    # 15 (ultima data que tem EUR), nao em 17 so porque a tabela tem alguma
    # cotacao la.
    tabela = TabelaCambio(taxas=TAXAS)

    assert tabela.taxa("EUR", date(2026, 7, 16)) == (Decimal("5.88"), date(2026, 7, 15))
