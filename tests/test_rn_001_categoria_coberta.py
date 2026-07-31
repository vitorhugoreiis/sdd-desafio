"""T-008 — RN-001: categoria fora da política é recusada.

T-025 (RN-012): a partir da v1.2, "coberta" depende da tabela do centro de
custo — uma categoria pode existir só num centro de custo (AMB-013).
"""
from decimal import Decimal

from src.motor.modelo import Status
from src.motor.politica import LimiteCategoria
from src.motor.regras import rn_001_categoria_coberta

from tests.fabricas import contexto, despesa, politica_padrao

CONTEXTO = contexto()


def test_rn_001_categoria_fora_da_politica_e_recusada():
    d = despesa(id="d-005", categoria="coworking", valor=Decimal("89.00"))

    parecer = rn_001_categoria_coberta(d, CONTEXTO)

    assert parecer is not None
    assert parecer.valor_reembolsavel == Decimal("0.00")
    assert parecer.status == Status.RECUSADA
    assert "RN-001" in parecer.regras_aplicadas


def test_rn_001_categorias_cobertas_nao_decidem():
    for categoria in ("alimentacao", "transporte_urbano", "hospedagem"):
        d = despesa(categoria=categoria)
        assert rn_001_categoria_coberta(d, CONTEXTO) is None


def test_rn_001_representacao_coberta_apenas_no_cc_comercial():
    politica = politica_padrao(centros_custo={"CC-COMERCIAL": {"representacao": LimiteCategoria(Decimal("300.00"))}})
    d = despesa(categoria="representacao", valor=Decimal("340.00"))

    ctx_comercial = contexto(centro_custo="CC-COMERCIAL", politica=politica)
    ctx_outro = contexto(centro_custo="CC-SUPORTE-N2", politica=politica)

    assert rn_001_categoria_coberta(d, ctx_comercial) is None

    parecer = rn_001_categoria_coberta(d, ctx_outro)
    assert parecer is not None
    assert parecer.status == Status.RECUSADA
    assert parecer.valor_reembolsavel == Decimal("0.00")
