"""Política de reembolso, consultável por centro de custo (plan.md §4, RN-012).

Núcleo puro: não sabe ler arquivo. Quem lê o documento externo e monta uma
`Politica` é `io/carregador_politica.py` (DT-008).
"""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class LimiteCategoria:
    """Existe só para que "categoria não coberta" (`None`) e "categoria
    bloqueada" (`Decimal("0.00")`) sejam visivelmente diferentes no tipo,
    não apenas no valor — a distinção que a AMB-014 exige."""

    valor: Decimal


@dataclass(frozen=True)
class Politica:
    padrao: dict[str, LimiteCategoria]
    centros_custo: dict[str, dict[str, LimiteCategoria]] = field(default_factory=dict)
    piso_nota_fiscal: Decimal = Decimal("100.00")
    fator_viagem: Decimal = Decimal("1.5")
    versao: str = ""
    vigencia: date | None = None

    def categorias_cobertas(self, centro_custo: str) -> frozenset[str]:
        """RN-012 — a união do padrão com as categorias do centro de custo."""
        tabela_cc = self.centros_custo.get(centro_custo, {})
        return frozenset({**self.padrao, **tabela_cc})

    def limite(self, centro_custo: str, categoria: str) -> Decimal | None:
        """RN-012 — a tabela do centro de custo sobrepõe o padrão categoria a
        categoria (AMB-013); `None` quando a categoria não está coberta em
        nenhuma das duas."""
        tabela_cc = self.centros_custo.get(centro_custo, {})
        limite_categoria = tabela_cc.get(categoria)
        if limite_categoria is None:
            limite_categoria = self.padrao.get(categoria)
        if limite_categoria is None:
            return None
        return limite_categoria.valor
