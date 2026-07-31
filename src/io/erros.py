"""Erro de entrada e validações compartilhadas pelos carregadores.

Extraído de `io/carregador.py` (T-003/T-004) para reuso em
`io/carregador_politica.py` e `io/carregador_cambio.py` (T-024, T-028) —
mesmo padrão, um documento de entrada a menos para reinventar.
"""
from datetime import date


class ErroDeEntrada(Exception):
    """Campo obrigatorio ausente ou de tipo invalido na entrada."""


def exigir(dados: dict, chave: str, rotulo: str):
    if not isinstance(dados, dict) or chave not in dados:
        raise ErroDeEntrada(f"Campo obrigatorio ausente: {rotulo}")
    return dados[chave]


def exigir_data(dados: dict, chave: str, rotulo: str) -> date:
    valor = exigir(dados, chave, rotulo)
    try:
        return date.fromisoformat(valor)
    except (TypeError, ValueError):
        raise ErroDeEntrada(f"Campo invalido: {rotulo}") from None
