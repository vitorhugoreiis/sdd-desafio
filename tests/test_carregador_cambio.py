"""T-028 — io/carregador_cambio.py: documento de câmbio → TabelaCambio (DT-008)."""
import json
from datetime import date
from decimal import Decimal

import pytest

from src.io.carregador_cambio import carregar
from src.io.erros import ErroDeEntrada

CAMBIO_BASE = {
    "moeda_base": "BRL",
    "taxas": {
        "2026-07-14": {"USD": 5.44, "EUR": 5.93},
        "2026-07-15": {"USD": 5.39, "EUR": 5.88},
    },
}


def _escrever(tmp_path, dados):
    caminho = tmp_path / "cambio.json"
    caminho.write_text(json.dumps(dados), encoding="utf-8")
    return str(caminho)


def test_carregador_cambio_monta_tabela_por_data_e_moeda(tmp_path):
    caminho = _escrever(tmp_path, CAMBIO_BASE)

    tabela = carregar(caminho)

    assert tabela.taxa("EUR", date(2026, 7, 14)) == (Decimal("5.93"), date(2026, 7, 14))
    assert tabela.taxa("USD", date(2026, 7, 15)) == (Decimal("5.39"), date(2026, 7, 15))


def test_carregador_cambio_normaliza_codigo_de_moeda(tmp_path):
    caminho = _escrever(tmp_path, {"taxas": {"2026-07-14": {" eur ": 5.93}}})

    tabela = carregar(caminho)

    assert tabela.taxa("EUR", date(2026, 7, 14)) == (Decimal("5.93"), date(2026, 7, 14))


def test_carregador_cambio_rejeita_campo_taxas_ausente(tmp_path):
    caminho = _escrever(tmp_path, {"moeda_base": "BRL"})

    with pytest.raises(ErroDeEntrada, match="taxas"):
        carregar(caminho)


def test_carregador_cambio_rejeita_data_invalida(tmp_path):
    caminho = _escrever(tmp_path, {"taxas": {"nao-e-data": {"USD": 5.0}}})

    with pytest.raises(ErroDeEntrada):
        carregar(caminho)


def test_carregador_cambio_rejeita_taxa_de_tipo_invalido(tmp_path):
    caminho = _escrever(tmp_path, {"taxas": {"2026-07-14": {"USD": "nao-e-numero"}}})

    with pytest.raises(ErroDeEntrada):
        carregar(caminho)
