"""T-015 — calculadora encadeia as regras na ordem da spec.md §8.

T-029 (DT-007): a partir da v1.2 os passos formam uma lista única
(`construir_passos`), cada um podendo devolver `Parecer | Despesa | None`, e
a conversão cambial (RN-011) entra como passo 6 — antes da nota fiscal.
"""
from datetime import date
from decimal import Decimal

from src.motor.calculadora import calcular, construir_passos
from src.motor.modelo import Solicitacao, Status

from tests.fabricas import despesa, politica_padrao
from tests.fabricas import tabela_cambio as fabrica_cambio


def _solicitacao(despesas, competencia="2026-07"):
    return Solicitacao(
        colaborador={"id": "c-1", "nome": "Teste", "centro_custo": "CC"},
        competencia=competencia,
        inicio=date(2026, 7, 1),
        fim=date(2026, 7, 31),
        despesas=tuple(despesas),
    )


def _calcular(despesas, competencia="2026-07", cambio=None):
    return calcular(_solicitacao(despesas, competencia), politica_padrao(), cambio or fabrica_cambio())


def test_ordem_nota_fiscal_antes_do_teto():
    d = despesa(id="d-004", categoria="transporte_urbano", valor=Decimal("100.01"), tem_nota_fiscal=False)
    resultado = _calcular([d])

    parecer = resultado.pareceres[0]
    assert parecer.valor_reembolsavel == Decimal("0.00")
    assert parecer.status == Status.RECUSADA
    assert "RN-006" in parecer.regras_aplicadas


def test_calculadora_produz_um_parecer_por_despesa_na_mesma_ordem():
    d1 = despesa(id="d-1", valor=Decimal("10.00"))
    d2 = despesa(id="d-2", valor=Decimal("20.00"))
    resultado = _calcular([d1, d2])

    assert [p.despesa.id for p in resultado.pareceres] == ["d-1", "d-2"]


def test_calculadora_normaliza_categoria_antes_de_decidir():
    d = despesa(id="d-014", categoria="ALIMENTACAO", valor=Decimal("61.00"))
    resultado = _calcular([d])

    parecer = resultado.pareceres[0]
    assert parecer.despesa.categoria == "alimentacao"
    assert parecer.valor_reembolsavel == Decimal("60.00")


def test_calculadora_aplica_duplicata_entre_despesas_da_mesma_solicitacao():
    primeira = despesa(id="d-006", data=date(2026, 7, 9), fornecedor="Bistro Central", valor=Decimal("54.90"))
    segunda = despesa(id="d-007", data=date(2026, 7, 9), fornecedor="Bistro Central", valor=Decimal("54.90"))
    resultado = _calcular([primeira, segunda])

    assert resultado.pareceres[0].valor_reembolsavel == Decimal("54.90")
    assert resultado.pareceres[1].valor_reembolsavel == Decimal("0.00")
    assert resultado.pareceres[1].status == Status.RECUSADA


def test_calculadora_amplia_teto_em_data_de_viagem():
    hospedagem = despesa(id="d-010", data=date(2026, 7, 14), categoria="hospedagem", valor=Decimal("480.00"))
    resultado = _calcular([hospedagem])

    assert resultado.pareceres[0].valor_reembolsavel == Decimal("375.00")


def test_calculadora_estorno_nao_e_afetado_por_teto():
    estorno = despesa(id="d-009", categoria="transporte_urbano", valor=Decimal("-500.00"))
    resultado = _calcular([estorno])

    assert resultado.pareceres[0].valor_reembolsavel == Decimal("-500.00")
    assert resultado.pareceres[0].status == Status.ESTORNO


def test_ordem_conversao_antes_da_nota_fiscal():
    # 40 USD a 5.50 = 220.00 BRL — acima do piso de 100. Se a nota fiscal
    # fosse avaliada sobre o valor de origem (40.00), o item passaria; a
    # conversao (passo 6) precisa rodar antes da nota fiscal (passo 8).
    d = despesa(
        id="e-005",
        data=date(2026, 7, 20),
        categoria="transporte_urbano",
        valor=Decimal("40.00"),
        tem_nota_fiscal=False,
        moeda="USD",
    )
    cambio = fabrica_cambio(taxas={date(2026, 7, 20): {"USD": Decimal("5.50")}})

    resultado = _calcular([d], cambio=cambio)

    parecer = resultado.pareceres[0]
    assert parecer.status == Status.RECUSADA
    assert "RN-006" in parecer.regras_aplicadas


def test_pipeline_e_uma_lista_unica():
    # DT-007 — normalizar_categoria (RN-002) e a conversao cambial (RN-011)
    # sao passos declarados na MESMA lista das demais regras, nao chamadas
    # a parte antes ou depois do laco.
    passos = construir_passos()
    nomes = [getattr(passo, "__name__", type(passo).__name__) for passo in passos]

    assert "normalizar_categoria" in nomes
    assert "rn_011_conversao_cambial" in nomes
    assert nomes.index("normalizar_categoria") < nomes.index("rn_003_competencia")
    assert nomes.index("rn_011_conversao_cambial") < nomes.index("rn_006_nota_fiscal")
    assert nomes.index("rn_011_conversao_cambial") < nomes.index("rn_007_teto_categoria")
