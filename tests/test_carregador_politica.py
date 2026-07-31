"""T-024 — io/carregador_politica.py: documento de política → Politica (DT-008)."""
import copy
import json
from decimal import Decimal

import pytest

from src.io.carregador_politica import carregar
from src.io.erros import ErroDeEntrada

POLITICA_BASE = {
    "versao": "v4",
    "vigencia": "2026-07-01",
    "padrao": {
        "alimentacao": {"limite": 60.00},
        "transporte_urbano": {"limite": 80.00},
        "hospedagem": {"limite": 250.00},
    },
    "centros_custo": {
        "CC-ENG-PLATAFORMA": {
            "alimentacao": {"limite": 75.00},
            "hospedagem": {"limite": 0.00},
        }
    },
    "nota_fiscal_obrigatoria_acima_de": 100.00,
    "acrescimo_em_viagem_percentual": 50,
}


def _escrever(tmp_path, dados):
    caminho = tmp_path / "politica.json"
    caminho.write_text(json.dumps(dados), encoding="utf-8")
    return str(caminho)


def test_carregador_politica_converte_percentual_em_fator(tmp_path):
    caminho = _escrever(tmp_path, POLITICA_BASE)

    politica = carregar(caminho)

    assert politica.fator_viagem == Decimal("1.5")
    assert politica.piso_nota_fiscal == Decimal("100.00")
    assert politica.versao == "v4"
    for valor in (politica.fator_viagem, politica.piso_nota_fiscal):
        assert isinstance(valor, Decimal)


def test_carregador_politica_monta_limites_por_centro_de_custo(tmp_path):
    caminho = _escrever(tmp_path, POLITICA_BASE)

    politica = carregar(caminho)

    assert politica.limite("CC-ENG-PLATAFORMA", "alimentacao") == Decimal("75.00")
    assert politica.limite("CC-ENG-PLATAFORMA", "hospedagem") == Decimal("0.00")
    assert politica.limite("CC-ENG-PLATAFORMA", "transporte_urbano") == Decimal("80.00")
    assert politica.limite("CC-DESCONHECIDO", "alimentacao") == Decimal("60.00")


@pytest.mark.parametrize(
    "campo",
    ["padrao", "nota_fiscal_obrigatoria_acima_de", "acrescimo_em_viagem_percentual", "versao", "vigencia"],
)
def test_carregador_politica_rejeita_campo_ausente(tmp_path, campo):
    dados = copy.deepcopy(POLITICA_BASE)
    del dados[campo]
    caminho = _escrever(tmp_path, dados)

    with pytest.raises(ErroDeEntrada, match=campo):
        carregar(caminho)


def test_carregador_politica_centros_custo_e_opcional(tmp_path):
    dados = copy.deepcopy(POLITICA_BASE)
    del dados["centros_custo"]
    caminho = _escrever(tmp_path, dados)

    politica = carregar(caminho)

    assert politica.limite("CC-QUALQUER", "alimentacao") == Decimal("60.00")
