"""RN-011 — conversão cambial: TabelaCambio pura, com retrocesso de data
(spec.md, AMB-018/019), e a regra completa `rn_011_conversao_cambial`
(T-030): converte, arredonda uma única vez (AMB-020) e recusa preservando o
valor de origem quando não há cotação (AMB-019, AMB-023)."""
from datetime import date
from decimal import Decimal

from src.motor.cambio import TabelaCambio
from src.motor.calculadora import calcular
from src.motor.modelo import Despesa, Solicitacao, Status
from src.motor.regras import rn_011_conversao_cambial

from tests.fabricas import contexto, despesa, politica_padrao
from tests.fabricas import tabela_cambio as fabrica_cambio

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


def test_rn_011_moeda_brl_nao_decide():
    d = despesa(valor=Decimal("50.00"), moeda="BRL")

    assert rn_011_conversao_cambial(d, contexto()) is None


def test_rn_011_arredonda_valor_convertido():
    d = despesa(valor=Decimal("14.50"), moeda="EUR", data=date(2026, 7, 15))
    ctx = contexto(tabela_cambio=fabrica_cambio(taxas={date(2026, 7, 15): {"EUR": Decimal("5.88")}}))

    resultado = rn_011_conversao_cambial(d, ctx)

    assert isinstance(resultado, Despesa)
    assert resultado.valor == Decimal("85.26")  # 14.50 * 5.88, exato
    assert resultado.taxa_cambio == Decimal("5.88")
    assert resultado.data_taxa == date(2026, 7, 15)
    assert resultado.valor_origem == Decimal("14.50")


def test_rn_011_data_sem_cotacao_usa_a_ultima_anterior_na_conversao():
    # 18/07 e sabado; a conversao efetiva usa a taxa de 17/07 (AMB-018).
    d = despesa(valor=Decimal("30.00"), moeda="EUR", data=date(2026, 7, 18))
    ctx = contexto(tabela_cambio=fabrica_cambio(taxas={date(2026, 7, 17): {"EUR": Decimal("5.96")}}))

    resultado = rn_011_conversao_cambial(d, ctx)

    assert resultado.valor == Decimal("178.80")  # 30.00 * 5.96
    assert resultado.data_taxa == date(2026, 7, 17)


def test_rn_011_moeda_sem_cotacao_e_recusada():
    d = despesa(id="e-006", valor=Decimal("55.00"), moeda="GBP", data=date(2026, 7, 21))
    ctx = contexto(tabela_cambio=fabrica_cambio(taxas={}))  # GBP nunca aparece na tabela

    parecer = rn_011_conversao_cambial(d, ctx)

    assert parecer is not None
    assert parecer.status == Status.RECUSADA
    assert parecer.valor_reembolsavel == Decimal("0.00")
    assert "RN-011" in parecer.regras_aplicadas
    # origem preservada, mas o valor em BRL (o que entra nos totais) e zero.
    assert parecer.despesa.valor == Decimal("0.00")
    assert parecer.despesa.valor_origem == Decimal("55.00")
    assert parecer.despesa.moeda == "GBP"


def test_rn_011_item_nao_convertivel_nao_polui_total():
    # AMB-023 — pelo pipeline completo: o item recusado por falta de cotacao
    # contribui 0.00 tanto para o total lancado quanto para o reembolsavel.
    d = despesa(id="e-006", categoria="alimentacao", valor=Decimal("55.00"), moeda="GBP", data=date(2026, 7, 21))
    solicitacao = Solicitacao(
        colaborador={"id": "c-1", "nome": "Teste", "centro_custo": "CC"},
        competencia="2026-07",
        inicio=date(2026, 7, 1),
        fim=date(2026, 7, 31),
        despesas=(d,),
    )

    resultado = calcular(solicitacao, politica_padrao(), fabrica_cambio(taxas={}))

    assert resultado.total_lancado == Decimal("0.00")
    assert resultado.total_reembolsavel == Decimal("0.00")
    assert resultado.pareceres[0].status == Status.RECUSADA
