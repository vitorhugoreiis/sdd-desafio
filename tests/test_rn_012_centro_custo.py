"""RN-012 — limites por centro de custo: a tabela do CC sobrepõe o padrão
categoria a categoria; CC ausente da tabela usa o padrão inteiro (AMB-013);
categoria que só existe na tabela de um CC não é coberta em outro (spec.md §5)."""
from decimal import Decimal

from src.motor.politica import LimiteCategoria, Politica

PADRAO = {
    "alimentacao": LimiteCategoria(Decimal("60.00")),
    "transporte_urbano": LimiteCategoria(Decimal("80.00")),
    "hospedagem": LimiteCategoria(Decimal("250.00")),
}


def _politica(centros_custo):
    return Politica(padrao=PADRAO, centros_custo=centros_custo)


def test_rn_012_cc_desconhecido_usa_padrao():
    politica = _politica(centros_custo={})

    assert politica.limite("CC-SUPORTE-N2", "alimentacao") == Decimal("60.00")
    assert politica.limite("CC-SUPORTE-N2", "transporte_urbano") == Decimal("80.00")
    assert politica.limite("CC-SUPORTE-N2", "hospedagem") == Decimal("250.00")


def test_rn_012_categoria_ausente_no_cc_herda_padrao():
    politica = _politica(
        centros_custo={
            "CC-ADM": {
                "alimentacao": LimiteCategoria(Decimal("45.00")),
                "transporte_urbano": LimiteCategoria(Decimal("60.00")),
            }
        }
    )

    # CC-ADM nao define hospedagem: herda o limite padrao (AMB-013) — a
    # tabela do CC e um override categoria a categoria, nao uma substituicao.
    assert politica.limite("CC-ADM", "hospedagem") == Decimal("250.00")
    assert politica.limite("CC-ADM", "alimentacao") == Decimal("45.00")


def test_rn_012_cc_sobrepoe_o_padrao():
    politica = _politica(
        centros_custo={
            "CC-ENG-PLATAFORMA": {
                "alimentacao": LimiteCategoria(Decimal("75.00")),
                "hospedagem": LimiteCategoria(Decimal("0.00")),
            }
        }
    )

    assert politica.limite("CC-ENG-PLATAFORMA", "alimentacao") == Decimal("75.00")
    assert politica.limite("CC-ENG-PLATAFORMA", "transporte_urbano") == Decimal("80.00")
    assert politica.limite("CC-ENG-PLATAFORMA", "hospedagem") == Decimal("0.00")


def test_rn_012_categoria_que_so_existe_num_cc_nao_e_coberta_em_outro():
    politica = _politica(centros_custo={"CC-COMERCIAL": {"representacao": LimiteCategoria(Decimal("300.00"))}})

    assert politica.limite("CC-COMERCIAL", "representacao") == Decimal("300.00")
    assert politica.limite("CC-SUPORTE-N2", "representacao") is None


def test_rn_012_categorias_cobertas_e_a_uniao_do_padrao_com_o_cc():
    politica = _politica(centros_custo={"CC-COMERCIAL": {"representacao": LimiteCategoria(Decimal("300.00"))}})

    cobertas = politica.categorias_cobertas("CC-COMERCIAL")

    assert cobertas == frozenset({"alimentacao", "transporte_urbano", "hospedagem", "representacao"})
    assert politica.categorias_cobertas("CC-SUPORTE-N2") == frozenset({"alimentacao", "transporte_urbano", "hospedagem"})
