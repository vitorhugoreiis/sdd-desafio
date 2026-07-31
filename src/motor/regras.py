"""Uma função pura por regra de negócio, na ordem da spec.md §8 (DT-002).

Cada regra de decisão tem assinatura `(Despesa, Contexto) -> Parecer | None`,
onde `None` significa "não decidi, siga para a próxima". `normalizar_categoria`
é a exceção: é o passo 2 (transformação, não decisão) e devolve uma nova
`Despesa`, não um `Parecer`.
"""
from collections.abc import Callable
from dataclasses import replace
from decimal import Decimal

from src.motor.modelo import Contexto, Despesa, Parecer, Status
from src.motor.politica import Politica

ZERO = Decimal("0.00")


def normalizar_categoria(despesa: Despesa) -> Despesa:
    """RN-002 — ignora caixa e espaços nas pontas antes de qualquer decisão."""
    categoria_normalizada = despesa.categoria.strip().lower()
    if categoria_normalizada == despesa.categoria:
        return despesa
    return replace(despesa, categoria=categoria_normalizada)


def rn_003_competencia(despesa: Despesa, contexto: Contexto) -> Parecer | None:
    """RN-003 — despesa fora do mês de competência é recusada (AMB-009)."""
    if despesa.data.strftime("%Y-%m") == contexto.competencia:
        return None
    return Parecer(
        despesa=despesa,
        valor_reembolsavel=ZERO,
        status=Status.RECUSADA,
        regras_aplicadas=("RN-003",),
        justificativa=(
            f"Despesa fora do periodo de competencia {contexto.competencia}."
        ),
    )


def rn_001_categoria_coberta(despesa: Despesa, contexto: Contexto) -> Parecer | None:
    """RN-001 — categoria fora da tabela de política efetivamente aplicada ao
    centro de custo (padrão sobreposto pelo centro de custo, RN-012) é
    recusada, mas permanece no resultado."""
    if despesa.categoria in contexto.politica.categorias_cobertas(contexto.centro_custo):
        return None
    return Parecer(
        despesa=despesa,
        valor_reembolsavel=ZERO,
        status=Status.RECUSADA,
        regras_aplicadas=("RN-001",),
        justificativa=(
            f"Categoria '{despesa.categoria}' nao e coberta pela politica de reembolso "
            f"do centro de custo {contexto.centro_custo}."
        ),
    )


def criar_rn_004_duplicata() -> Callable[[Despesa, Contexto], Parecer | None]:
    """RN-004 — fábrica com estado próprio: a primeira ocorrência da chave
    (data, categoria, fornecedor, descrição, valor) passa; as demais são
    recusadas (AMB-008). Uma instância nova por cálculo, para não vazar
    estado entre execuções (spec.md §3)."""
    vistos: set[tuple] = set()

    def regra(despesa: Despesa, contexto: Contexto) -> Parecer | None:
        chave = (
            despesa.data,
            despesa.categoria,
            despesa.fornecedor,
            despesa.descricao,
            despesa.valor,
        )
        if chave in vistos:
            return Parecer(
                despesa=despesa,
                valor_reembolsavel=ZERO,
                status=Status.RECUSADA,
                regras_aplicadas=("RN-004",),
                justificativa=(
                    "Duplicata de um lancamento anterior identico em data, "
                    "categoria, fornecedor, descricao e valor."
                ),
            )
        vistos.add(chave)
        return None

    return regra


def rn_005_estorno(despesa: Despesa, contexto: Contexto) -> Parecer | None:
    """RN-005 — valor negativo é estorno: abate integral, sem teto e sem nota (AMB-010)."""
    if despesa.valor >= ZERO:
        return None
    return Parecer(
        despesa=despesa,
        valor_reembolsavel=despesa.valor,
        status=Status.ESTORNO,
        regras_aplicadas=("RN-005",),
        justificativa="Estorno: valor negativo abatido integralmente do total, sem teto e sem exigencia de nota fiscal.",
    )


def rn_006_nota_fiscal(despesa: Despesa, contexto: Contexto) -> Parecer | None:
    """RN-006 — nota fiscal obrigatória, estritamente acima do piso definido
    na política (AMB-003/004/005/021).

    Avaliada sobre o valor lançado, antes do teto (AMB-005). O piso não é
    ampliado por viagem (AMB-006).
    """
    piso = contexto.politica.piso_nota_fiscal
    if despesa.valor <= piso or despesa.tem_nota_fiscal:
        return None
    return Parecer(
        despesa=despesa,
        valor_reembolsavel=ZERO,
        status=Status.RECUSADA,
        regras_aplicadas=("RN-006",),
        justificativa=f"Valor acima de R$ {piso:.2f} exige nota fiscal, que nao foi declarada.",
    )


def construir_contexto(
    despesas: tuple[Despesa, ...], competencia: str, centro_custo: str, politica: Politica
) -> Contexto:
    """RN-009 — viagem é inferida por hospedagem na mesma data, aprovada,
    recusada ou com limite R$ 0,00 (AMB-006, AMB-015). Calculada uma vez
    sobre a lista como veio na entrada, antes de qualquer recusa dos passos
    3 a 8 (spec.md §8, DT-004)."""
    datas_em_viagem = frozenset(
        despesa.data for despesa in despesas if despesa.categoria.strip().lower() == "hospedagem"
    )
    return Contexto(
        competencia=competencia,
        centro_custo=centro_custo,
        politica=politica,
        datas_em_viagem=datas_em_viagem,
    )


def rn_007_teto_categoria(despesa: Despesa, contexto: Contexto) -> Parecer:
    """RN-007/RN-008/RN-009/RN-012 — teto por despesa, nunca por soma do dia
    (AMB-001), vindo da tabela de política do centro de custo (RN-012).

    Reembolsa o teto e glosa o excedente (AMB-002); limite R$ 0,00 recusa em
    vez de glosar o total (AMB-014). Em data de viagem, o teto é ampliado
    pelo fator da política (RN-009); hospedagem conta como uma diária,
    qualquer que seja o texto da descrição (RN-008). É o último passo de
    decisão da spec §8: sempre decide, nunca devolve None.
    """
    teto = contexto.politica.limite(contexto.centro_custo, despesa.categoria)
    override = contexto.politica.centros_custo.get(contexto.centro_custo, {}).get(despesa.categoria)

    if teto == ZERO:
        return Parecer(
            despesa=despesa,
            valor_reembolsavel=ZERO,
            status=Status.RECUSADA,
            regras_aplicadas=("RN-012",),
            justificativa=(
                f"Categoria '{despesa.categoria}' nao e reembolsavel no centro de custo "
                f"{contexto.centro_custo} (limite R$ 0,00)."
            ),
        )

    regras_aplicadas = ["RN-007"]
    if override is not None:
        regras_aplicadas.append("RN-012")
    if despesa.categoria == "hospedagem":
        regras_aplicadas.append("RN-008")
    if despesa.data in contexto.datas_em_viagem:
        teto = (teto * contexto.politica.fator_viagem).quantize(Decimal("0.01"))
        regras_aplicadas.append("RN-009")

    if despesa.valor <= teto:
        return Parecer(
            despesa=despesa,
            valor_reembolsavel=despesa.valor,
            status=Status.APROVADA,
            regras_aplicadas=tuple(regras_aplicadas),
            justificativa=f"Valor dentro do teto de R$ {teto:.2f} para {despesa.categoria}.",
        )

    excedente = despesa.valor - teto
    return Parecer(
        despesa=despesa,
        valor_reembolsavel=teto,
        status=Status.PARCIAL,
        regras_aplicadas=tuple(regras_aplicadas),
        justificativa=(
            f"Valor acima do teto de R$ {teto:.2f} para {despesa.categoria}. "
            f"Excedente de R$ {excedente:.2f} glosado."
        ),
    )
