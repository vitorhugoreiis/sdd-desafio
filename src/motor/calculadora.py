"""Percorre as despesas e monta o Resultado (spec.md §8, plan.md DT-002/DT-007).

`construir_passos` é a lista única e declarada da spec §8, passos 2 a 9 —
mudar a ordem das regras é reordenar esta lista, não reescrever `if`s
aninhados (DT-002). Cada passo devolve `Parecer | Despesa | None` (DT-007):
`None` segue para o próximo passo com a mesma despesa; `Despesa` segue para o
próximo passo com a despesa transformada; `Parecer` encerra a despesa atual.
`rn_007_teto_categoria` nunca devolve `None`, então o laço sempre para nela
quando nenhum passo anterior decidiu.
"""
from src.motor.cambio import TabelaCambio
from src.motor.modelo import Despesa, Parecer, Resultado, Solicitacao
from src.motor.politica import Politica
from src.motor.regras import (
    construir_contexto,
    criar_rn_004_duplicata,
    normalizar_categoria,
    rn_001_categoria_coberta,
    rn_003_competencia,
    rn_005_estorno,
    rn_006_nota_fiscal,
    rn_007_teto_categoria,
    rn_011_conversao_cambial,
)


def construir_passos():
    """Uma instância nova por cálculo: `criar_rn_004_duplicata()` carrega
    estado próprio e não pode vazar entre execuções (spec.md §3)."""
    return (
        normalizar_categoria,
        rn_003_competencia,
        rn_001_categoria_coberta,
        criar_rn_004_duplicata(),
        rn_011_conversao_cambial,
        rn_005_estorno,
        rn_006_nota_fiscal,
        rn_007_teto_categoria,
    )


def calcular(solicitacao: Solicitacao, politica: Politica, tabela_cambio: TabelaCambio) -> Resultado:
    centro_custo = solicitacao.colaborador["centro_custo"]
    contexto = construir_contexto(solicitacao.despesas, solicitacao.competencia, centro_custo, politica, tabela_cambio)
    passos = construir_passos()

    pareceres: list[Parecer] = []
    for despesa in solicitacao.despesas:
        despesa_atual = despesa
        for passo in passos:
            resultado = passo(despesa_atual, contexto)
            if resultado is None:
                continue
            if isinstance(resultado, Despesa):
                despesa_atual = resultado
                continue
            pareceres.append(resultado)
            break

    return Resultado(solicitacao=solicitacao, politica=politica, pareceres=tuple(pareceres))
