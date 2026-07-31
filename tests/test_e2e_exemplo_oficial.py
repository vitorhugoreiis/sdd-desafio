"""T-022 — teste ponta a ponta sobre exemplos/despesas-exemplo.json (spec.md §9)."""
from decimal import Decimal
from pathlib import Path

from src.io.carregador import carregar
from src.motor.calculadora import calcular

from tests.fabricas import politica_padrao, tabela_cambio

CAMINHO_EXEMPLO = Path(__file__).resolve().parent.parent / "exemplos" / "despesas-exemplo.json"


def _por_id(resultado):
    return {parecer.despesa.id: parecer for parecer in resultado.pareceres}


def test_e2e_exemplo_oficial():
    # T-025: politica de teste (equivalente a v3) ate a Fase 7 (T-032)
    # trocar pela politica-v4.json real e os numeros de D-002 (703.43 -> 341.93).
    solicitacao = carregar(str(CAMINHO_EXEMPLO))
    resultado = calcular(solicitacao, politica_padrao(), tabela_cambio())

    assert resultado.total_lancado == Decimal("1816.84")
    assert resultado.total_reembolsavel == Decimal("703.43")
    assert len(resultado.pareceres) == 14

    pareceres = _por_id(resultado)

    assert pareceres["d-003"].valor_reembolsavel == Decimal("80.00")
    assert pareceres["d-004"].valor_reembolsavel == Decimal("0.00")
    assert pareceres["d-006"].valor_reembolsavel == Decimal("54.90")
    assert pareceres["d-007"].valor_reembolsavel == Decimal("0.00")
    assert pareceres["d-010"].valor_reembolsavel == Decimal("375.00")
    assert pareceres["d-011"].despesa.valor == Decimal("33.33")
    assert pareceres["d-011"].valor_reembolsavel == Decimal("33.33")
    assert pareceres["d-014"].despesa.categoria == "alimentacao"
    assert pareceres["d-014"].valor_reembolsavel == Decimal("60.00")


def test_e2e_soma_dos_itens_bate_com_o_resumo():
    solicitacao = carregar(str(CAMINHO_EXEMPLO))
    resultado = calcular(solicitacao, politica_padrao(), tabela_cambio())

    soma = sum((parecer.valor_reembolsavel for parecer in resultado.pareceres), Decimal("0.00"))
    assert soma == resultado.total_reembolsavel
