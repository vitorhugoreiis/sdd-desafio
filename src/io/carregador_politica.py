"""Documento de política → Politica (plan.md §2, DT-008).

Núcleo puro não sabe ler arquivo (DT-003); esta é a fronteira de I/O que lê
o documento de política e monta a estrutura que `motor/politica.py` consulta.
"""
import json
from decimal import Decimal, InvalidOperation

from src.io.erros import ErroDeEntrada, exigir, exigir_data
from src.motor.politica import LimiteCategoria, Politica


def carregar(caminho: str) -> Politica:
    with open(caminho, "r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo, parse_float=Decimal)
    return _para_politica(dados)


def _para_decimal(valor, rotulo: str) -> Decimal:
    try:
        return Decimal(valor)
    except (InvalidOperation, TypeError, ValueError):
        raise ErroDeEntrada(f"Campo invalido: {rotulo}") from None


def _para_limites(mapa: dict, rotulo_base: str) -> dict[str, LimiteCategoria]:
    limites = {}
    for categoria, info in mapa.items():
        valor = exigir(info, "limite", f"{rotulo_base}.{categoria}.limite")
        limites[categoria.strip().lower()] = LimiteCategoria(_para_decimal(valor, f"{rotulo_base}.{categoria}.limite"))
    return limites


def _para_politica(dados: dict) -> Politica:
    padrao_bruto = exigir(dados, "padrao", "padrao")
    piso = exigir(dados, "nota_fiscal_obrigatoria_acima_de", "nota_fiscal_obrigatoria_acima_de")
    percentual = exigir(dados, "acrescimo_em_viagem_percentual", "acrescimo_em_viagem_percentual")
    versao = exigir(dados, "versao", "versao")
    vigencia = exigir_data(dados, "vigencia", "vigencia")

    centros_custo_bruto = dados.get("centros_custo", {})
    centros_custo = {
        centro_custo.strip(): _para_limites(mapa, f"centros_custo.{centro_custo}")
        for centro_custo, mapa in centros_custo_bruto.items()
    }

    fator_viagem = Decimal("1") + (_para_decimal(percentual, "acrescimo_em_viagem_percentual") / Decimal("100"))

    return Politica(
        padrao=_para_limites(padrao_bruto, "padrao"),
        centros_custo=centros_custo,
        piso_nota_fiscal=_para_decimal(piso, "nota_fiscal_obrigatoria_acima_de"),
        fator_viagem=fator_viagem,
        versao=versao,
        vigencia=vigencia,
    )
