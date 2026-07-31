"""Fábricas de Despesa, Política, Câmbio e Contexto para os testes (DT-006, plan.md §6)."""
from datetime import date
from decimal import Decimal

from src.motor.cambio import TabelaCambio
from src.motor.modelo import Contexto, Despesa
from src.motor.politica import LimiteCategoria, Politica

PADRAO_V3 = {
    "alimentacao": LimiteCategoria(Decimal("60.00")),
    "transporte_urbano": LimiteCategoria(Decimal("80.00")),
    "hospedagem": LimiteCategoria(Decimal("250.00")),
}


def despesa(
    *,
    id="d-teste",
    data=date(2026, 7, 3),
    categoria="alimentacao",
    descricao="Despesa de teste",
    fornecedor="Fornecedor Teste",
    valor=Decimal("50.00"),
    tem_nota_fiscal=True,
    moeda="BRL",
    valor_origem=None,
    taxa_cambio=None,
    data_taxa=None,
) -> Despesa:
    return Despesa(
        id=id,
        data=data,
        categoria=categoria,
        descricao=descricao,
        fornecedor=fornecedor,
        valor=valor,
        tem_nota_fiscal=tem_nota_fiscal,
        moeda=moeda,
        valor_origem=valor_origem,
        taxa_cambio=taxa_cambio,
        data_taxa=data_taxa,
    )


def politica_padrao(
    *,
    padrao=None,
    centros_custo=None,
    piso_nota_fiscal=Decimal("100.00"),
    fator_viagem=Decimal("1.5"),
    versao="v-teste",
    vigencia=date(2026, 1, 1),
) -> Politica:
    """Reproduz os valores da política v3 como padrão de teste — os testes
    de regra que não têm nenhum interesse específico em política (a maioria)
    continuam exercitando os mesmos números de sempre."""
    return Politica(
        padrao=padrao if padrao is not None else dict(PADRAO_V3),
        centros_custo=centros_custo or {},
        piso_nota_fiscal=piso_nota_fiscal,
        fator_viagem=fator_viagem,
        versao=versao,
        vigencia=vigencia,
    )


def tabela_cambio(*, taxas=None) -> TabelaCambio:
    return TabelaCambio(taxas=taxas or {})


def contexto(
    *,
    competencia="2026-07",
    datas_em_viagem=frozenset(),
    centro_custo="CC-TESTE",
    politica=None,
    tabela_cambio=None,
) -> Contexto:
    return Contexto(
        competencia=competencia,
        datas_em_viagem=datas_em_viagem,
        centro_custo=centro_custo,
        politica=politica if politica is not None else politica_padrao(),
        tabela_cambio=tabela_cambio if tabela_cambio is not None else TabelaCambio(taxas={}),
    )
