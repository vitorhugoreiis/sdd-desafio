"""T-022 → T-032 — teste ponta a ponta sobre exemplos/despesas-exemplo.json
(spec.md §9, D-002).

A partir da v1.2, a política vem do documento real do envelope
(`exemplos/envelope/politica-v4.json`), não mais de uma fábrica de teste
equivalente à v3. O total cai de R$ 703,43 (v1.1) para R$ 341,93 — D-002 em
`DECISIONS.md` explica por quê: o centro de custo CC-ENG-PLATAFORMA passou a
ter tabela própria (alimentação R$ 75, hospedagem não reembolsável), sem
nenhuma mudança na lógica de cálculo em si.
"""
from decimal import Decimal
from pathlib import Path

from src.io.carregador import carregar
from src.io.carregador_cambio import carregar as carregar_cambio
from src.io.carregador_politica import carregar as carregar_politica
from src.motor.calculadora import calcular

RAIZ = Path(__file__).resolve().parent.parent
CAMINHO_EXEMPLO = RAIZ / "exemplos" / "despesas-exemplo.json"
CAMINHO_POLITICA = RAIZ / "exemplos" / "envelope" / "politica-v4.json"
CAMINHO_CAMBIO = RAIZ / "exemplos" / "envelope" / "cambio.json"


def _por_id(resultado):
    return {parecer.despesa.id: parecer for parecer in resultado.pareceres}


def _calcular():
    solicitacao = carregar(str(CAMINHO_EXEMPLO))
    politica = carregar_politica(str(CAMINHO_POLITICA))
    tabela_cambio = carregar_cambio(str(CAMINHO_CAMBIO))
    return calcular(solicitacao, politica, tabela_cambio)


def test_e2e_exemplo_oficial():
    resultado = _calcular()

    assert resultado.total_lancado == Decimal("1816.84")
    assert resultado.total_reembolsavel == Decimal("341.93")
    assert len(resultado.pareceres) == 14

    pareceres = _por_id(resultado)

    assert pareceres["d-001"].valor_reembolsavel == Decimal("72.50")  # teto 75 (era 60 na v3): integral agora
    assert pareceres["d-002"].valor_reembolsavel == Decimal("38.00")
    assert pareceres["d-003"].valor_reembolsavel == Decimal("80.00")
    assert pareceres["d-004"].valor_reembolsavel == Decimal("0.00")
    assert pareceres["d-005"].valor_reembolsavel == Decimal("0.00")
    assert pareceres["d-006"].valor_reembolsavel == Decimal("54.90")
    assert pareceres["d-007"].valor_reembolsavel == Decimal("0.00")
    assert pareceres["d-008"].valor_reembolsavel == Decimal("0.00")
    assert pareceres["d-009"].valor_reembolsavel == Decimal("-45.00")
    assert pareceres["d-010"].valor_reembolsavel == Decimal("0.00")  # D-002: hospedagem nao reembolsavel no CC
    assert pareceres["d-010"].status.value == "recusada"
    assert "RN-012" in pareceres["d-010"].regras_aplicadas
    assert pareceres["d-011"].despesa.valor == Decimal("33.33")
    assert pareceres["d-011"].valor_reembolsavel == Decimal("33.33")
    assert pareceres["d-012"].valor_reembolsavel == Decimal("47.20")
    assert pareceres["d-013"].valor_reembolsavel == Decimal("0.00")
    assert pareceres["d-014"].despesa.categoria == "alimentacao"
    assert pareceres["d-014"].valor_reembolsavel == Decimal("61.00")  # teto 75 (era 60 na v3): integral agora


def test_e2e_bloco_politica_do_cabecalho():
    resultado = _calcular()

    assert resultado.origem_dos_limites == "centro_custo"  # CC-ENG-PLATAFORMA esta na tabela


def test_e2e_soma_dos_itens_bate_com_o_resumo():
    resultado = _calcular()

    soma = sum((parecer.valor_reembolsavel for parecer in resultado.pareceres), Decimal("0.00"))
    assert soma == resultado.total_reembolsavel
