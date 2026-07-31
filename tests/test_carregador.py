"""T-003 — carregador: JSON em disco vira Solicitacao com Decimal (RN-010, AMB-011)."""
import json
from decimal import Decimal

from src.io.carregador import carregar


def _escrever_entrada(tmp_path, valor):
    dados = {
        "colaborador": {"id": "c-1", "nome": "Teste", "centro_custo": "CC"},
        "periodo": {"competencia": "2026-07", "inicio": "2026-07-01", "fim": "2026-07-31"},
        "despesas": [
            {
                "id": "d-001",
                "data": "2026-07-15",
                "categoria": "alimentacao",
                "descricao": "Cafe da manha hotel",
                "fornecedor": "Hotel Copa Sul",
                "valor": valor,
                "tem_nota_fiscal": True,
            }
        ],
    }
    caminho = tmp_path / "entrada.json"
    # Escreve com json.dumps padrão: números permanecem literais textuais no
    # arquivo (ex.: 33.333), exatamente como chegariam de um arquivo real.
    caminho.write_text(json.dumps(dados), encoding="utf-8")
    return caminho


def test_rn_010_arredonda_na_leitura(tmp_path):
    caminho = _escrever_entrada(tmp_path, 33.333)

    solicitacao = carregar(str(caminho))

    valor = solicitacao.despesas[0].valor
    assert valor == Decimal("33.33")
    assert isinstance(valor, Decimal)


def test_rn_010_conversao_nunca_passa_por_float(tmp_path):
    # 2.675 como float binário vale 2.67499999999999982...; se o valor tivesse
    # passado por float em algum ponto, o arredondamento meio-para-cima erraria
    # para 2.67. Só dá 2.68 se o texto "2.675" foi lido direto como Decimal.
    caminho = _escrever_entrada(tmp_path, 2.675)

    solicitacao = carregar(str(caminho))

    assert solicitacao.despesas[0].valor == Decimal("2.68")


def test_carregador_preenche_periodo_e_colaborador(tmp_path):
    caminho = _escrever_entrada(tmp_path, 10)

    solicitacao = carregar(str(caminho))

    assert solicitacao.competencia == "2026-07"
    assert solicitacao.colaborador["id"] == "c-1"
    assert solicitacao.despesas[0].categoria == "alimentacao"
    assert solicitacao.despesas[0].tem_nota_fiscal is True


def _escrever_entrada_com_moeda(tmp_path, moeda=None, valor=22.00):
    dados = {
        "colaborador": {"id": "c-1", "nome": "Teste", "centro_custo": "CC"},
        "periodo": {"competencia": "2026-07", "inicio": "2026-07-01", "fim": "2026-07-31"},
        "despesas": [
            {
                "id": "e-002",
                "data": "2026-07-14",
                "categoria": "alimentacao",
                "descricao": "Almoco - Lisboa",
                "fornecedor": "Taberna do Chiado",
                "valor": valor,
                "tem_nota_fiscal": True,
            }
        ],
    }
    if moeda is not None:
        dados["despesas"][0]["moeda"] = moeda
    caminho = tmp_path / "entrada.json"
    caminho.write_text(json.dumps(dados), encoding="utf-8")
    return caminho


def test_carregador_moeda_ausente_assume_brl(tmp_path):
    caminho = _escrever_entrada_com_moeda(tmp_path, moeda=None, valor=88.00)

    solicitacao = carregar(str(caminho))
    despesa = solicitacao.despesas[0]

    assert despesa.moeda == "BRL"
    assert despesa.valor == Decimal("88.00")
    assert despesa.valor_origem == Decimal("88.00")
    assert despesa.taxa_cambio is None
    assert despesa.data_taxa is None


def test_carregador_normaliza_codigo_de_moeda(tmp_path):
    caminho = _escrever_entrada_com_moeda(tmp_path, moeda=" eur ")

    solicitacao = carregar(str(caminho))

    assert solicitacao.despesas[0].moeda == "EUR"


def test_carregador_moeda_estrangeira_nao_arredonda_valor_origem_na_leitura(tmp_path):
    # RN-010/AMB-020: o arredondamento de uma despesa estrangeira so ocorre
    # apos a conversao (RN-011) — na leitura, o valor de origem fica intacto.
    caminho = _escrever_entrada_com_moeda(tmp_path, moeda="EUR", valor=14.505)

    solicitacao = carregar(str(caminho))
    despesa = solicitacao.despesas[0]

    assert despesa.valor_origem == Decimal("14.505")
    assert despesa.moeda == "EUR"
