"""T-023 — a política deixa de expor constantes e passa a expor uma estrutura
consultável por centro de custo (plan.md §4, D-002)."""
from decimal import Decimal

from src.motor.politica import LimiteCategoria, Politica


def test_politica_e_uma_estrutura_consultavel_nao_constantes_de_modulo():
    politica = Politica(
        padrao={"alimentacao": LimiteCategoria(Decimal("60.00"))},
        centros_custo={},
        piso_nota_fiscal=Decimal("100.00"),
        fator_viagem=Decimal("1.5"),
        versao="v4",
    )

    limite = politica.limite("CC-QUALQUER", "alimentacao")
    assert limite == Decimal("60.00")
    assert isinstance(limite, Decimal)
    assert not isinstance(limite, float)


def test_politica_categoria_nao_coberta_e_none_nao_zero():
    # None (nao coberta) e Decimal("0.00") (bloqueada) sao distintos — AMB-014.
    politica = Politica(padrao={}, centros_custo={})

    assert politica.limite("CC-QUALQUER", "alimentacao") is None


def test_politica_piso_e_fator_sao_decimal():
    politica = Politica(
        padrao={},
        piso_nota_fiscal=Decimal("100.00"),
        fator_viagem=Decimal("1.5"),
    )

    for valor in (politica.piso_nota_fiscal, politica.fator_viagem):
        assert isinstance(valor, Decimal)
        assert not isinstance(valor, float)
