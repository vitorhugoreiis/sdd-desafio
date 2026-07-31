"""T-019 — serializador: Decimal como texto de duas casas, status em minúsculas.

T-031: cada item ganha `moeda`/`valor_origem`/`taxa_cambio`/`data_taxa`, e o
cabeçalho ganha o bloco `politica` (spec.md §4).
"""
import json
from datetime import date
from decimal import Decimal

from src.io.serializador import para_documento
from src.motor.modelo import Parecer, Resultado, Solicitacao, Status

from tests.fabricas import despesa, politica_padrao


def _solicitacao(despesas, centro_custo="CC-ENG"):
    return Solicitacao(
        colaborador={"id": "c-0417", "nome": "Marina Volpi", "centro_custo": centro_custo},
        competencia="2026-07",
        inicio=date(2026, 7, 1),
        fim=date(2026, 7, 31),
        despesas=tuple(despesas),
    )


def test_serializa_valores_como_texto_de_duas_casas():
    d = despesa(id="d-001", valor=Decimal("60"))
    parecer = Parecer(
        despesa=d,
        valor_reembolsavel=Decimal("60"),
        status=Status.APROVADA,
        regras_aplicadas=("RN-007",),
        justificativa="Valor dentro do teto.",
    )
    resultado = Resultado(solicitacao=_solicitacao([d]), politica=politica_padrao(), pareceres=(parecer,))

    documento = para_documento(resultado)
    item = documento["itens"][0]

    assert item["valor_lancado"] == "60.00"
    assert item["valor_reembolsavel"] == "60.00"
    assert item["valor_glosado"] == "0.00"
    assert item["status"] == "aprovada"

    # nenhum Decimal cru chega ao json.dump: se algum tivesse escapado, esta
    # linha levantaria TypeError.
    json.dumps(documento)


def test_serializa_regras_aplicadas_como_lista():
    d = despesa()
    parecer = Parecer(
        despesa=d,
        valor_reembolsavel=d.valor,
        status=Status.APROVADA,
        regras_aplicadas=("RN-007",),
        justificativa="ok",
    )
    resultado = Resultado(solicitacao=_solicitacao([d]), politica=politica_padrao(), pareceres=(parecer,))

    item = para_documento(resultado)["itens"][0]
    assert item["regras_aplicadas"] == ["RN-007"]


def test_serializa_colaborador_e_periodo_sem_alteracao():
    resultado = Resultado(solicitacao=_solicitacao([despesa()]), politica=politica_padrao(), pareceres=())
    documento = para_documento(resultado)

    assert documento["colaborador"]["id"] == "c-0417"
    assert documento["periodo"]["competencia"] == "2026-07"
    assert documento["periodo"]["inicio"] == "2026-07-01"
    assert documento["periodo"]["fim"] == "2026-07-31"


def test_serializa_despesa_em_moeda_estrangeira():
    d = despesa(
        id="e-002",
        valor=Decimal("130.46"),
        moeda="EUR",
        valor_origem=Decimal("22.00"),
        taxa_cambio=Decimal("5.93"),
        data_taxa=date(2026, 7, 14),
    )
    parecer = Parecer(
        despesa=d,
        valor_reembolsavel=Decimal("90.00"),
        status=Status.PARCIAL,
        regras_aplicadas=("RN-007",),
        justificativa="acima do teto",
    )
    resultado = Resultado(solicitacao=_solicitacao([d]), politica=politica_padrao(), pareceres=(parecer,))

    item = para_documento(resultado)["itens"][0]

    assert item["moeda"] == "EUR"
    assert item["valor_origem"] == "22.00"
    assert item["taxa_cambio"] == "5.93"
    assert item["data_taxa"] == "2026-07-14"
    assert item["valor_lancado"] == "130.46"


def test_serializa_despesa_em_brl_nao_tem_taxa_nem_data_de_taxa():
    d = despesa(valor=Decimal("50.00"))
    parecer = Parecer(
        despesa=d,
        valor_reembolsavel=d.valor,
        status=Status.APROVADA,
        regras_aplicadas=("RN-007",),
        justificativa="ok",
    )
    resultado = Resultado(solicitacao=_solicitacao([d]), politica=politica_padrao(), pareceres=(parecer,))

    item = para_documento(resultado)["itens"][0]

    assert item["moeda"] == "BRL"
    assert item["valor_origem"] == "50.00"
    assert item["taxa_cambio"] is None
    assert item["data_taxa"] is None
    json.dumps(para_documento(resultado))


def test_serializa_bloco_politica_no_cabecalho_com_centro_de_custo():
    politica = politica_padrao(centros_custo={"CC-ENG": {}})
    resultado = Resultado(solicitacao=_solicitacao([despesa()], centro_custo="CC-ENG"), politica=politica, pareceres=())

    bloco = para_documento(resultado)["politica"]

    assert bloco["versao"] == politica.versao
    assert bloco["vigencia"] == politica.vigencia.isoformat()
    assert bloco["centro_custo_aplicado"] == "CC-ENG"
    assert bloco["origem_dos_limites"] == "centro_custo"


def test_serializa_bloco_politica_no_cabecalho_com_padrao():
    politica = politica_padrao(centros_custo={})
    resultado = Resultado(
        solicitacao=_solicitacao([despesa()], centro_custo="CC-DESCONHECIDO"), politica=politica, pareceres=()
    )

    bloco = para_documento(resultado)["politica"]

    assert bloco["centro_custo_aplicado"] == "CC-DESCONHECIDO"
    assert bloco["origem_dos_limites"] == "padrao"
