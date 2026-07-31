"""T-033 — testes ponta a ponta sobre os dois arquivos de `exemplos/envelope/`
(spec.md §9). Números conferidos à mão na memória de cálculo do
`docs/HANDOFF-dia2.md` antes da implementação — ver anexo daquele arquivo.
"""
from decimal import Decimal
from pathlib import Path

from src.io.carregador import carregar
from src.io.carregador_cambio import carregar as carregar_cambio
from src.io.carregador_politica import carregar as carregar_politica
from src.motor.calculadora import calcular

RAIZ = Path(__file__).resolve().parent.parent
ENVELOPE = RAIZ / "exemplos" / "envelope"
CAMINHO_POLITICA = ENVELOPE / "politica-v4.json"
CAMINHO_CAMBIO = ENVELOPE / "cambio.json"


def _calcular(nome_arquivo):
    solicitacao = carregar(str(ENVELOPE / nome_arquivo))
    politica = carregar_politica(str(CAMINHO_POLITICA))
    tabela_cambio = carregar_cambio(str(CAMINHO_CAMBIO))
    return calcular(solicitacao, politica, tabela_cambio)


def _por_id(resultado):
    return {parecer.despesa.id: parecer for parecer in resultado.pareceres}


def test_e2e_envelope_cc_comercial():
    resultado = _calcular("despesas-envelope.json")

    assert resultado.total_lancado == Decimal("2457.52")
    assert resultado.total_reembolsavel == Decimal("1343.26")
    assert resultado.origem_dos_limites == "centro_custo"

    pareceres = _por_id(resultado)

    assert pareceres["e-001"].valor_reembolsavel == Decimal("300.00")  # teto representacao
    assert pareceres["e-002"].valor_reembolsavel == Decimal("90.00")  # 22 EUR * 5.93 = 130.46, teto 90
    assert pareceres["e-002"].despesa.taxa_cambio == Decimal("5.93")
    assert pareceres["e-003"].valor_reembolsavel == Decimal("85.26")  # 14.50 EUR * 5.88, <=100 dispensa nota
    assert pareceres["e-004"].valor_reembolsavel == Decimal("90.00")  # sabado sem cotacao, usa 17/07
    assert pareceres["e-004"].despesa.data_taxa.isoformat() == "2026-07-17"
    assert pareceres["e-005"].valor_reembolsavel == Decimal("0.00")  # 40 USD = 220 BRL, sem nota
    assert pareceres["e-005"].status.value == "recusada"
    assert pareceres["e-006"].valor_reembolsavel == Decimal("0.00")  # GBP sem cotacao
    assert "RN-011" in pareceres["e-006"].regras_aplicadas
    assert pareceres["e-006"].despesa.valor_origem == Decimal("55.00")
    assert pareceres["e-006"].despesa.moeda == "GBP"
    assert pareceres["e-007"].valor_reembolsavel == Decimal("600.00")  # teto 400 * 1.5 (viagem)
    assert pareceres["e-007"].estado.value == "pendente_aprovacao"  # RN-013 (opcional): > 500
    assert pareceres["e-008"].valor_reembolsavel == Decimal("90.00")
    assert pareceres["e-009"].valor_reembolsavel == Decimal("0.00")  # coworking fora da politica
    assert pareceres["e-010"].valor_reembolsavel == Decimal("88.00")  # moeda ausente -> BRL
    assert pareceres["e-010"].despesa.moeda == "BRL"


def test_e2e_envelope_cc_desconhecido():
    resultado = _calcular("despesas-envelope-cc-desconhecido.json")

    assert resultado.total_lancado == Decimal("623.76")
    assert resultado.total_reembolsavel == Decimal("433.76")
    assert resultado.origem_dos_limites == "padrao"  # CC-SUPORTE-N2 nao esta na tabela

    pareceres = _por_id(resultado)

    assert pareceres["f-001"].valor_reembolsavel == Decimal("58.00")
    assert pareceres["f-002"].valor_reembolsavel == Decimal("310.00")  # teto 250*1.5=375 (viagem, ela mesma)
    assert pareceres["f-003"].valor_reembolsavel == Decimal("0.00")  # representacao so existe no CC-COMERCIAL
    assert pareceres["f-003"].status.value == "recusada"
    assert "RN-001" in pareceres["f-003"].regras_aplicadas
    assert pareceres["f-004"].valor_reembolsavel == Decimal("65.76")  # 12 USD * 5.48


def test_e2e_envelope_soma_dos_itens_bate_com_o_resumo():
    for nome_arquivo in ("despesas-envelope.json", "despesas-envelope-cc-desconhecido.json"):
        resultado = _calcular(nome_arquivo)
        soma = sum((parecer.valor_reembolsavel for parecer in resultado.pareceres), Decimal("0.00"))
        assert soma == resultado.total_reembolsavel
