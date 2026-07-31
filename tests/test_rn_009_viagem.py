"""T-014 — RN-009: contexto de viagem por data com hospedagem (AMB-006).

T-025: o fator de ampliação passa a vir da política (spec.md RN-009), e
hospedagem com limite R$ 0,00 no centro de custo continua caracterizando
viagem (AMB-015) — o indício é o pernoite, não o pagamento.
"""
from datetime import date
from decimal import Decimal

from src.motor.cambio import TabelaCambio
from src.motor.modelo import Status
from src.motor.politica import LimiteCategoria
from src.motor.regras import construir_contexto, rn_006_nota_fiscal, rn_007_teto_categoria

from tests.fabricas import despesa, politica_padrao

DATA_VIAGEM = date(2026, 7, 14)


def _contexto_de(despesas, *, politica=None, centro_custo="CC-TESTE"):
    return construir_contexto(
        despesas,
        competencia="2026-07",
        centro_custo=centro_custo,
        politica=politica or politica_padrao(),
        tabela_cambio=TabelaCambio(taxas={}),
    )


def test_rn_009_data_com_hospedagem_amplia_tetos():
    hospedagem = despesa(id="d-010", data=DATA_VIAGEM, categoria="hospedagem", valor=Decimal("480.00"))
    contexto = _contexto_de((hospedagem,))

    parecer = rn_007_teto_categoria(hospedagem, contexto)

    assert parecer.valor_reembolsavel == Decimal("375.00")
    assert "RN-009" in parecer.regras_aplicadas


def test_rn_009_hospedagem_recusada_ainda_caracteriza_viagem():
    hospedagem_sem_nota = despesa(
        id="d-013", data=DATA_VIAGEM, categoria="hospedagem", valor=Decimal("690.00"), tem_nota_fiscal=False
    )
    almoco_mesma_data = despesa(id="d-x", data=DATA_VIAGEM, categoria="alimentacao", valor=Decimal("85.00"))

    contexto = _contexto_de((hospedagem_sem_nota, almoco_mesma_data))

    assert DATA_VIAGEM in contexto.datas_em_viagem
    # a hospedagem em si seria recusada por falta de nota fiscal (RN-006)...
    assert rn_006_nota_fiscal(hospedagem_sem_nota, contexto).status == Status.RECUSADA
    # ...mas isso nao impede a data de contar como viagem.

    parecer_almoco = rn_007_teto_categoria(almoco_mesma_data, contexto)
    assert parecer_almoco.status == Status.APROVADA
    assert parecer_almoco.valor_reembolsavel == Decimal("85.00")


def test_rn_009_hospedagem_com_limite_zero_ainda_caracteriza_viagem():
    """AMB-015 — o indicio de viagem e o pernoite, nao o pagamento: uma
    hospedagem recusada por limite R$ 0,00 (RN-012) continua ampliando o
    teto das demais despesas da mesma data."""
    politica = politica_padrao(centros_custo={"CC-ENG-PLATAFORMA": {"hospedagem": LimiteCategoria(Decimal("0.00"))}})
    hospedagem = despesa(id="d-010", data=DATA_VIAGEM, categoria="hospedagem", valor=Decimal("480.00"))
    almoco_mesma_data = despesa(id="d-x", data=DATA_VIAGEM, categoria="alimentacao", valor=Decimal("85.00"))

    contexto = _contexto_de((hospedagem, almoco_mesma_data), politica=politica, centro_custo="CC-ENG-PLATAFORMA")

    assert DATA_VIAGEM in contexto.datas_em_viagem

    parecer_hospedagem = rn_007_teto_categoria(hospedagem, contexto)
    assert parecer_hospedagem.status == Status.RECUSADA
    assert parecer_hospedagem.valor_reembolsavel == Decimal("0.00")

    parecer_almoco = rn_007_teto_categoria(almoco_mesma_data, contexto)
    assert parecer_almoco.status == Status.APROVADA
    assert parecer_almoco.valor_reembolsavel == Decimal("85.00")  # abaixo do teto ampliado (60 * 1.5 = 90)
    assert "RN-009" in parecer_almoco.regras_aplicadas


def test_rn_009_fator_vem_da_politica():
    """O percentual de ampliacao (acrescimo_em_viagem_percentual) e um dado
    da politica, nao uma constante do motor — um fator de 100% (em vez de
    50%) dobra o teto em vez de multiplicar por 1,5."""
    politica = politica_padrao(fator_viagem=Decimal("2.0"))
    hospedagem = despesa(id="d-010", data=DATA_VIAGEM, categoria="hospedagem", valor=Decimal("600.00"))

    contexto = _contexto_de((hospedagem,), politica=politica)

    parecer = rn_007_teto_categoria(hospedagem, contexto)
    assert parecer.status == Status.PARCIAL
    assert parecer.valor_reembolsavel == Decimal("500.00")  # 250 * 2.0


def test_rn_009_viagem_nao_amplia_piso_da_nota():
    d = despesa(id="d-y", data=DATA_VIAGEM, categoria="alimentacao", valor=Decimal("105.00"), tem_nota_fiscal=False)
    hospedagem = despesa(id="d-010", data=DATA_VIAGEM, categoria="hospedagem", valor=Decimal("480.00"))
    contexto = _contexto_de((hospedagem, d))

    parecer = rn_006_nota_fiscal(d, contexto)

    assert parecer is not None
    assert parecer.status == Status.RECUSADA


def test_rn_009_data_sem_hospedagem_nao_e_viagem():
    almoco = despesa(id="d-z", data=date(2026, 7, 3), categoria="alimentacao", valor=Decimal("72.50"))
    contexto = _contexto_de((almoco,))

    assert contexto.datas_em_viagem == frozenset()

    parecer = rn_007_teto_categoria(almoco, contexto)
    assert parecer.valor_reembolsavel == Decimal("60.00")


def test_rn_009_viagem_e_por_categoria_normalizada():
    hospedagem_caixa_alta = despesa(id="d-w", data=DATA_VIAGEM, categoria="HOSPEDAGEM", valor=Decimal("300.00"))
    contexto = _contexto_de((hospedagem_caixa_alta,))

    assert DATA_VIAGEM in contexto.datas_em_viagem
