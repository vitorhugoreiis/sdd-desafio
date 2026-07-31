"""T-011 — RN-006: nota fiscal obrigatória, estritamente acima de R$ 100 (AMB-003..005)."""
from decimal import Decimal

from src.motor.modelo import Status
from src.motor.regras import rn_006_nota_fiscal

from tests.fabricas import contexto, despesa

CONTEXTO = contexto()


def test_rn_006_piso_e_exclusivo():
    d = despesa(id="d-003", categoria="transporte_urbano", valor=Decimal("100.00"), tem_nota_fiscal=False)
    assert rn_006_nota_fiscal(d, CONTEXTO) is None


def test_rn_006_acima_do_piso_sem_nota_e_recusada():
    d = despesa(id="d-004", categoria="transporte_urbano", valor=Decimal("100.01"), tem_nota_fiscal=False)

    parecer = rn_006_nota_fiscal(d, CONTEXTO)

    assert parecer is not None
    assert parecer.valor_reembolsavel == Decimal("0.00")
    assert parecer.status == Status.RECUSADA
    assert "RN-006" in parecer.regras_aplicadas


def test_rn_006_acima_do_piso_com_nota_nao_decide():
    d = despesa(valor=Decimal("690.00"), tem_nota_fiscal=True)
    assert rn_006_nota_fiscal(d, CONTEXTO) is None


def test_rn_006_abaixo_do_piso_sem_nota_nao_decide():
    d = despesa(valor=Decimal("50.00"), tem_nota_fiscal=False)
    assert rn_006_nota_fiscal(d, CONTEXTO) is None


def test_rn_006_piso_comparado_ao_valor_convertido():
    """AMB-021 — o piso e comparado ao valor ja convertido em reais (`valor`),
    nao ao valor de origem. Simula o estado de uma despesa apos RN-011: 40
    USD convertidos para R$ 220,00, acima do piso, mesmo a origem sendo 40."""
    d = despesa(valor=Decimal("220.00"), valor_origem=Decimal("40.00"), moeda="USD", tem_nota_fiscal=False)

    parecer = rn_006_nota_fiscal(d, CONTEXTO)

    assert parecer is not None
    assert parecer.status == Status.RECUSADA
    assert parecer.valor_reembolsavel == Decimal("0.00")
