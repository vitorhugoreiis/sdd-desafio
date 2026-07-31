"""RN-013 (opcional, v4) — fila de aprovação manual: valor reembolsável
estritamente acima de R$ 500,00 fica pendente, sem alterar valor nem status
(AMB-024). Estorno nunca fica pendente (RN-005)."""
from decimal import Decimal

from src.motor.modelo import Estado, Parecer, Status
from src.motor.regras import rn_013_fila_aprovacao

from tests.fabricas import contexto, despesa

CONTEXTO = contexto()


def _parecer(valor_reembolsavel, status=Status.APROVADA):
    return Parecer(
        despesa=despesa(),
        valor_reembolsavel=valor_reembolsavel,
        status=status,
        regras_aplicadas=("RN-007",),
        justificativa="teste",
    )


def test_rn_013_parecer_nasce_com_estado_aprovacao_automatica():
    parecer = _parecer(Decimal("50.00"))
    assert parecer.estado == Estado.APROVACAO_AUTOMATICA


def test_rn_013_acima_de_500_fica_pendente():
    parecer = _parecer(Decimal("600.00"))

    resultado = rn_013_fila_aprovacao(parecer, CONTEXTO)

    assert resultado.estado == Estado.PENDENTE_APROVACAO
    assert resultado.valor_reembolsavel == Decimal("600.00")
    assert resultado.status == Status.APROVADA


def test_rn_013_exatamente_500_nao_fica_pendente():
    parecer = _parecer(Decimal("500.00"))

    resultado = rn_013_fila_aprovacao(parecer, CONTEXTO)

    assert resultado.estado == Estado.APROVACAO_AUTOMATICA


def test_rn_013_um_centavo_acima_de_500_fica_pendente():
    parecer = _parecer(Decimal("500.01"))

    resultado = rn_013_fila_aprovacao(parecer, CONTEXTO)

    assert resultado.estado == Estado.PENDENTE_APROVACAO


def test_rn_013_estorno_nunca_fica_pendente():
    # modulo do estorno > 500, mas estorno nunca fica pendente (RN-005).
    parecer = _parecer(Decimal("-600.00"), status=Status.ESTORNO)

    resultado = rn_013_fila_aprovacao(parecer, CONTEXTO)

    assert resultado.estado == Estado.APROVACAO_AUTOMATICA


def test_rn_013_valor_abaixo_de_500_nao_fica_pendente():
    parecer = _parecer(Decimal("50.00"))

    resultado = rn_013_fila_aprovacao(parecer, CONTEXTO)

    assert resultado.estado == Estado.APROVACAO_AUTOMATICA
