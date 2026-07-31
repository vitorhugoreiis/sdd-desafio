"""Formata Resultado como documento de saída (spec.md §4).

É a única fronteira onde Decimal vira texto: json.dump nunca recebe um
Decimal cru (DT-001).
"""
import json

from src.motor.modelo import Parecer, Resultado


def _valor(valor) -> str:
    return f"{valor:.2f}"


def _valor_opcional(valor) -> str | None:
    return _valor(valor) if valor is not None else None


def _data_opcional(data) -> str | None:
    return data.isoformat() if data is not None else None


def _item(parecer: Parecer) -> dict:
    despesa = parecer.despesa
    return {
        "id": despesa.id,
        "data": despesa.data.isoformat(),
        "categoria": despesa.categoria,
        "moeda": despesa.moeda,
        "valor_origem": _valor(despesa.valor_origem),
        "taxa_cambio": _valor_opcional(despesa.taxa_cambio),
        "data_taxa": _data_opcional(despesa.data_taxa),
        "valor_lancado": _valor(despesa.valor),
        "valor_reembolsavel": _valor(parecer.valor_reembolsavel),
        "valor_glosado": _valor(parecer.valor_glosado),
        "status": parecer.status.value,
        "estado": parecer.estado.value,
        "regras_aplicadas": list(parecer.regras_aplicadas),
        "justificativa": parecer.justificativa,
    }


def para_documento(resultado: Resultado) -> dict:
    solicitacao = resultado.solicitacao
    politica = resultado.politica
    return {
        "colaborador": solicitacao.colaborador,
        "periodo": {
            "competencia": solicitacao.competencia,
            "inicio": solicitacao.inicio.isoformat(),
            "fim": solicitacao.fim.isoformat(),
        },
        "politica": {
            "versao": politica.versao,
            "vigencia": _data_opcional(politica.vigencia),
            "centro_custo_aplicado": solicitacao.colaborador["centro_custo"],
            "origem_dos_limites": resultado.origem_dos_limites,
        },
        "resumo": {
            "total_lancado": _valor(resultado.total_lancado),
            "total_reembolsavel": _valor(resultado.total_reembolsavel),
            "total_glosado": _valor(resultado.total_glosado),
            "quantidade_por_status": {
                status.value: quantidade
                for status, quantidade in resultado.quantidade_por_status.items()
            },
            "quantidade_por_estado": {
                estado.value: quantidade
                for estado, quantidade in resultado.quantidade_por_estado.items()
            },
            "total_pendente_aprovacao": _valor(resultado.total_pendente_aprovacao),
        },
        "itens": [_item(parecer) for parecer in resultado.pareceres],
    }


def salvar(resultado: Resultado, caminho: str) -> None:
    documento = para_documento(resultado)
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(documento, arquivo, ensure_ascii=False, indent=2)
        arquivo.write("\n")
