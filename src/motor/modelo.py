"""Estruturas de dados do motor (plan.md §3). Núcleo puro: sem I/O."""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum

from src.motor.cambio import TabelaCambio
from src.motor.politica import Politica


class Status(Enum):
    APROVADA = "aprovada"
    PARCIAL = "parcial"
    RECUSADA = "recusada"
    ESTORNO = "estorno"


class Estado(Enum):
    """RN-013 (opcional, v4) — ortogonal a `Status`: informa se o item
    segue o fluxo normal ou aguarda aprovação manual do gestor."""

    APROVACAO_AUTOMATICA = "aprovacao_automatica"
    PENDENTE_APROVACAO = "pendente_aprovacao"


@dataclass(frozen=True)
class Despesa:
    id: str
    data: date
    categoria: str
    descricao: str
    fornecedor: str
    valor: Decimal
    tem_nota_fiscal: bool
    moeda: str = "BRL"
    valor_origem: Decimal | None = None
    taxa_cambio: Decimal | None = None
    data_taxa: date | None = None

    def __post_init__(self):
        if self.valor_origem is None:
            object.__setattr__(self, "valor_origem", self.valor)


@dataclass(frozen=True)
class Solicitacao:
    colaborador: dict
    competencia: str
    inicio: date
    fim: date
    despesas: tuple[Despesa, ...]


@dataclass(frozen=True)
class Contexto:
    competencia: str
    centro_custo: str
    politica: Politica
    tabela_cambio: TabelaCambio
    datas_em_viagem: frozenset[date] = field(default_factory=frozenset)


@dataclass(frozen=True)
class Parecer:
    despesa: Despesa
    valor_reembolsavel: Decimal
    status: Status
    regras_aplicadas: tuple[str, ...]
    justificativa: str
    estado: Estado = Estado.APROVACAO_AUTOMATICA

    @property
    def valor_glosado(self) -> Decimal:
        return self.despesa.valor - self.valor_reembolsavel


@dataclass(frozen=True)
class Resultado:
    solicitacao: Solicitacao
    politica: Politica
    pareceres: tuple[Parecer, ...]

    @property
    def origem_dos_limites(self) -> str:
        """RN-012 — "centro_custo" quando a tabela do centro de custo do
        colaborador foi usada, "padrao" quando ele estava ausente dela."""
        centro_custo = self.solicitacao.colaborador["centro_custo"]
        return "centro_custo" if centro_custo in self.politica.centros_custo else "padrao"

    @property
    def total_lancado(self) -> Decimal:
        return sum((p.despesa.valor for p in self.pareceres), Decimal("0.00"))

    @property
    def total_reembolsavel(self) -> Decimal:
        return sum((p.valor_reembolsavel for p in self.pareceres), Decimal("0.00"))

    @property
    def total_glosado(self) -> Decimal:
        return self.total_lancado - self.total_reembolsavel

    @property
    def quantidade_por_status(self) -> dict[Status, int]:
        contagem = {status: 0 for status in Status}
        for parecer in self.pareceres:
            contagem[parecer.status] += 1
        return contagem

    @property
    def quantidade_por_estado(self) -> dict[Estado, int]:
        contagem = {estado: 0 for estado in Estado}
        for parecer in self.pareceres:
            contagem[parecer.estado] += 1
        return contagem

    @property
    def total_pendente_aprovacao(self) -> Decimal:
        return sum(
            (p.valor_reembolsavel for p in self.pareceres if p.estado == Estado.PENDENTE_APROVACAO),
            Decimal("0.00"),
        )
