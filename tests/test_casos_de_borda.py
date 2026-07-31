"""T-016 — tabela de casos de borda da spec.md §7, uma linha por caso.

Cada caso monta um documento de entrada completo e passa pelo pipeline real
(carregar → calcular), não pelas funções de regra isoladas — é a forma mais
fiel de testar o comportamento observável descrito na spec.
"""
import json
from decimal import Decimal

import pytest

from src.io.carregador import carregar
from src.motor.calculadora import calcular
from src.motor.modelo import Estado, Status
from src.motor.politica import LimiteCategoria

from tests.fabricas import politica_padrao, tabela_cambio


def _d(id, data, categoria, valor, nota, descricao="Despesa de teste", fornecedor="Fornecedor Teste", moeda=None):
    dados = {
        "id": id,
        "data": data,
        "categoria": categoria,
        "descricao": descricao,
        "fornecedor": fornecedor,
        "valor": valor,
        "tem_nota_fiscal": nota,
    }
    if moeda is not None:
        dados["moeda"] = moeda
    return dados


def _entrada(despesas, competencia="2026-07", centro_custo="CC"):
    return {
        "colaborador": {"id": "c-1", "nome": "Teste", "centro_custo": centro_custo},
        "periodo": {"competencia": competencia, "inicio": "2026-07-01", "fim": "2026-07-31"},
        "despesas": despesas,
    }


CASOS = [
    (
        "RN-006-piso-inclusive",
        [_d("d-1", "2026-07-06", "transporte_urbano", 100.00, False)],
        lambda r: r.pareceres[0].status == Status.PARCIAL
        and r.pareceres[0].valor_reembolsavel == Decimal("80.00")
        and "RN-006" not in r.pareceres[0].regras_aplicadas,
    ),
    (
        "RN-006-acima-do-piso",
        [_d("d-1", "2026-07-06", "transporte_urbano", 100.01, False)],
        lambda r: r.pareceres[0].status == Status.RECUSADA
        and r.pareceres[0].valor_reembolsavel == Decimal("0.00")
        and "RN-006" in r.pareceres[0].regras_aplicadas,
    ),
    (
        "RN-007-no-teto",
        [_d("d-1", "2026-07-03", "alimentacao", 60.00, True)],
        lambda r: r.pareceres[0].status == Status.APROVADA
        and r.pareceres[0].valor_reembolsavel == Decimal("60.00")
        and r.pareceres[0].valor_glosado == Decimal("0.00"),
    ),
    (
        "RN-007-acima-do-teto",
        [_d("d-1", "2026-07-03", "alimentacao", 60.01, True)],
        lambda r: r.pareceres[0].status == Status.PARCIAL
        and r.pareceres[0].valor_reembolsavel == Decimal("60.00")
        and r.pareceres[0].valor_glosado == Decimal("0.01"),
    ),
    (
        "RN-007-teto-por-despesa",
        [
            _d("d-1", "2026-07-03", "alimentacao", 72.50, True, fornecedor="Restaurante Tavola"),
            _d("d-2", "2026-07-03", "alimentacao", 38.00, True, fornecedor="Cantina do Porto"),
        ],
        lambda r: r.pareceres[0].valor_reembolsavel == Decimal("60.00")
        and r.pareceres[1].valor_reembolsavel == Decimal("38.00"),
    ),
    (
        "RN-004-duplicata-exata",
        [
            _d("d-1", "2026-07-09", "alimentacao", 54.90, True, "Almoco", "Bistro Central"),
            _d("d-2", "2026-07-09", "alimentacao", 54.90, True, "Almoco", "Bistro Central"),
        ],
        lambda r: r.pareceres[0].valor_reembolsavel == Decimal("54.90")
        and r.pareceres[1].valor_reembolsavel == Decimal("0.00")
        and r.pareceres[1].status == Status.RECUSADA,
    ),
    (
        "RN-004-fornecedor-diferente",
        [
            _d("d-1", "2026-07-09", "alimentacao", 54.90, True, fornecedor="Loja A"),
            _d("d-2", "2026-07-09", "alimentacao", 54.90, True, fornecedor="Loja B"),
        ],
        lambda r: r.pareceres[0].status == Status.APROVADA and r.pareceres[1].status == Status.APROVADA,
    ),
    (
        "RN-003-fora-da-competencia",
        [_d("d-1", "2026-04-15", "alimentacao", 41.00, True)],
        lambda r: r.pareceres[0].status == Status.RECUSADA and r.pareceres[0].valor_reembolsavel == Decimal("0.00"),
    ),
    (
        "RN-001-categoria-fora-da-politica",
        [_d("d-1", "2026-07-07", "coworking", 89.00, True)],
        lambda r: r.pareceres[0].status == Status.RECUSADA and r.pareceres[0].valor_reembolsavel == Decimal("0.00"),
    ),
    (
        "RN-002-categoria-caixa-alta",
        [_d("d-1", "2026-07-31", "ALIMENTACAO", 50.00, True)],
        lambda r: r.pareceres[0].despesa.categoria == "alimentacao" and r.pareceres[0].status == Status.APROVADA,
    ),
    (
        "RN-005-estorno",
        [_d("d-1", "2026-07-11", "transporte_urbano", -45.00, False)],
        lambda r: r.pareceres[0].status == Status.ESTORNO and r.pareceres[0].valor_reembolsavel == Decimal("-45.00"),
    ),
    (
        "RN-005-estorno-acima-do-teto",
        [_d("d-1", "2026-07-11", "alimentacao", -500.00, False)],
        lambda r: r.pareceres[0].valor_reembolsavel == Decimal("-500.00"),
    ),
    (
        "RN-010-terceira-casa-decimal",
        [_d("d-1", "2026-07-15", "alimentacao", 33.333, True)],
        lambda r: r.pareceres[0].despesa.valor == Decimal("33.33")
        and r.pareceres[0].valor_reembolsavel == Decimal("33.33"),
    ),
    (
        "RN-008-hospedagem-varias-noites",
        [_d("d-1", "2026-07-14", "hospedagem", 480.00, True, descricao="Hotel Rio - 2 diarias")],
        # a propria hospedagem torna a data uma data de viagem (RN-009), o
        # que amplia o teto de 250.00 para 375.00 — mesma matematica de
        # d-010 no exemplo oficial (spec.md §9).
        lambda r: r.pareceres[0].valor_reembolsavel == Decimal("375.00")
        and "RN-008" in r.pareceres[0].regras_aplicadas,
    ),
    (
        "RN-006-hospedagem-sem-nota",
        [_d("d-1", "2026-07-22", "hospedagem", 690.00, False, descricao="Airbnb 3 noites")],
        lambda r: r.pareceres[0].status == Status.RECUSADA and r.pareceres[0].valor_reembolsavel == Decimal("0.00"),
    ),
    (
        "RN-009-data-com-hospedagem-amplia-teto",
        [
            _d("d-1", "2026-07-14", "hospedagem", 200.00, True),
            _d("d-2", "2026-07-14", "alimentacao", 85.00, True),
        ],
        lambda r: r.pareceres[1].status == Status.APROVADA
        and r.pareceres[1].valor_reembolsavel == Decimal("85.00")
        and "RN-009" in r.pareceres[1].regras_aplicadas,
    ),
    (
        "RN-009-hospedagem-recusada-ainda-e-viagem",
        [
            _d("d-1", "2026-07-14", "hospedagem", 690.00, False, descricao="Airbnb 3 noites"),
            _d("d-2", "2026-07-14", "alimentacao", 85.00, True),
        ],
        lambda r: r.pareceres[0].status == Status.RECUSADA
        and r.pareceres[1].status == Status.APROVADA
        and r.pareceres[1].valor_reembolsavel == Decimal("85.00"),
    ),
    (
        "lista-vazia",
        [],
        lambda r: r.pareceres == ()
        and r.total_lancado == Decimal("0.00")
        and r.total_reembolsavel == Decimal("0.00")
        and r.total_glosado == Decimal("0.00"),
    ),
    # --- linhas novas da spec.md §7 (v1.2, T-034) ---
    (
        "RN-012-limite-zero-recusa",
        [_d("d-1", "2026-07-14", "hospedagem", 480.00, True)],
        lambda r: r.pareceres[0].status == Status.RECUSADA
        and r.pareceres[0].valor_reembolsavel == Decimal("0.00")
        and "RN-012" in r.pareceres[0].regras_aplicadas,
        dict(
            centro_custo="CC-ENG-PLATAFORMA",
            politica=politica_padrao(centros_custo={"CC-ENG-PLATAFORMA": {"hospedagem": LimiteCategoria(Decimal("0.00"))}}),
        ),
    ),
    (
        "RN-012-cc-desconhecido-usa-padrao",
        [_d("d-1", "2026-07-03", "alimentacao", 55.00, True)],
        lambda r: r.pareceres[0].status == Status.APROVADA and r.pareceres[0].valor_reembolsavel == Decimal("55.00"),
        dict(
            centro_custo="CC-NUNCA-VISTO",
            politica=politica_padrao(centros_custo={"CC-ENG-PLATAFORMA": {"alimentacao": LimiteCategoria(Decimal("75.00"))}}),
        ),
    ),
    (
        "RN-001-categoria-so-existe-num-cc",
        [_d("d-1", "2026-07-17", "representacao", 190.00, True)],
        lambda r: r.pareceres[0].status == Status.RECUSADA and r.pareceres[0].valor_reembolsavel == Decimal("0.00"),
        dict(
            centro_custo="CC-SUPORTE-N2",
            politica=politica_padrao(centros_custo={"CC-COMERCIAL": {"representacao": LimiteCategoria(Decimal("300.00"))}}),
        ),
    ),
    (
        "RN-011-moeda-sem-cotacao-recusa",
        [_d("d-1", "2026-07-21", "representacao", 55.00, True, moeda="GBP")],
        lambda r: r.pareceres[0].status == Status.RECUSADA
        and r.pareceres[0].valor_reembolsavel == Decimal("0.00")
        and "RN-011" in r.pareceres[0].regras_aplicadas
        and r.pareceres[0].despesa.valor_origem == Decimal("55.00"),
        dict(
            centro_custo="CC-COMERCIAL",
            politica=politica_padrao(centros_custo={"CC-COMERCIAL": {"representacao": LimiteCategoria(Decimal("300.00"))}}),
            cambio=tabela_cambio(taxas={}),  # GBP nunca aparece
        ),
    ),
    # --- fronteira de RN-013 (opcional, T-035) ---
    (
        "RN-013-exatamente-500-nao-fica-pendente",
        [_d("d-1", "2026-07-03", "alimentacao", 500.00, True)],
        lambda r: r.pareceres[0].estado == Estado.APROVACAO_AUTOMATICA
        and r.pareceres[0].valor_reembolsavel == Decimal("500.00"),
        dict(politica=politica_padrao(padrao={"alimentacao": LimiteCategoria(Decimal("1000.00"))})),
    ),
    (
        "RN-013-um-centavo-acima-de-500-fica-pendente",
        [_d("d-1", "2026-07-03", "alimentacao", 500.01, True)],
        lambda r: r.pareceres[0].estado == Estado.PENDENTE_APROVACAO
        and r.pareceres[0].valor_reembolsavel == Decimal("500.01"),
        dict(politica=politica_padrao(padrao={"alimentacao": LimiteCategoria(Decimal("1000.00"))})),
    ),
]


@pytest.mark.parametrize("caso", CASOS, ids=[c[0] for c in CASOS])
def test_casos_de_borda(tmp_path, caso):
    _, despesas, verificar, *resto = caso
    extras = resto[0] if resto else {}
    centro_custo = extras.get("centro_custo", "CC")
    politica = extras.get("politica") or politica_padrao()
    cambio = extras.get("cambio") or tabela_cambio()

    caminho = tmp_path / "entrada.json"
    caminho.write_text(json.dumps(_entrada(despesas, centro_custo=centro_custo)), encoding="utf-8")

    resultado = calcular(carregar(str(caminho)), politica, cambio)

    assert verificar(resultado)


def test_casos_de_borda_cobre_as_24_linhas_da_spec():
    assert len(CASOS) == 24
