# Motor de Cálculo de Reembolso

CLI que lê um JSON de despesas de um colaborador e emite um JSON com o valor
reembolsável e a justificativa de cada item, segundo a Política de Reembolso de
Despesas v4 — limites por centro de custo, despesas em moeda estrangeira e,
opcionalmente, fila de aprovação manual para valores altos.

> **Status:** especificação fechada (`spec.md` 1.2, `plan.md` 1.1) e as 36
> tasks da implementação concluídas — 162 testes verdes, incluindo a
> absorção do envelope do Dia 2 (Política v4). Ver o detalhe em
> [`specs/001-motor-reembolso/tasks.md`](specs/001-motor-reembolso/tasks.md)
> e o registro da mudança em
> [`DECISIONS.md`](specs/001-motor-reembolso/DECISIONS.md) (D-002/D-003/D-004).

---

## Requisitos

- Python 3.11 ou superior
- `pytest` (única dependência, apenas para rodar os testes)

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install pytest
```

## Como rodar

```bash
python -m src.cli calcular --input exemplos/despesas-exemplo.json --output resultado.json
```

O comando lê o arquivo de entrada, aplica a política e escreve o resultado.
Retorna `0` em caso de sucesso. Entrada malformada retorna código diferente de
zero, informa qual campo está errado e **não** escreve o arquivo de saída.

`--politica` e `--cambio` são **opcionais**: sem eles, a CLI usa a tabela de
limites e a tabela de câmbio vigentes do envelope
(`exemplos/envelope/politica-v4.json` e `cambio.json`), resolvidas a partir da
raiz do pacote — o comando acima roda de qualquer diretório, sem flag extra.
Para apontar outra tabela (por exemplo, uma política futura):

```bash
python -m src.cli calcular \
  --input exemplos/envelope/despesas-envelope.json \
  --output resultado.json \
  --politica exemplos/envelope/politica-v4.json \
  --cambio exemplos/envelope/cambio.json
```

## Como testar

```bash
pytest                  # suíte completa
pytest -k rn_012        # só os testes de uma regra de negócio
pytest -k e2e           # só os testes ponta a ponta (exemplo oficial + envelope)
```

Cada teste começa pelo ID da regra que exercita (`test_rn_012_...`), então dá
para ir de qualquer regra da spec ao teste que a cobre — e vice-versa. A matriz
completa está no fim do [`tasks.md`](specs/001-motor-reembolso/tasks.md).

## O que o sistema faz

A política deixou de ser única para toda a empresa: cada centro de custo tem
sua própria tabela de limites, despesas podem vir em moeda estrangeira, e
itens acima de R$ 500 reembolsáveis entram numa fila de aprovação (opcional).
Isso quebrou legitimamente o aceite do Dia 1 — sobre
`exemplos/despesas-exemplo.json`, o total reembolsável caiu de **R$ 703,43**
para **R$ 341,93**, porque o centro de custo do exemplo (CC-ENG-PLATAFORMA)
passou a não reembolsar hospedagem. D-002 em `DECISIONS.md` registra o porquê.

| Arquivo | Centro de custo | Lançado | Reembolsável | Destaque |
|---|---|---|---|---|
| `exemplos/despesas-exemplo.json` | CC-ENG-PLATAFORMA | R$ 1.816,84 | **R$ 341,93** | hospedagem não reembolsável neste CC (`d-010`: R$ 0,00) |
| `exemplos/envelope/despesas-envelope.json` | CC-COMERCIAL | R$ 2.457,52 | **R$ 1.343,26** | despesas em EUR/USD/GBP; `e-006` (GBP) recusada por falta de cotação; `e-007` fica pendente de aprovação |
| `exemplos/envelope/despesas-envelope-cc-desconhecido.json` | CC-SUPORTE-N2 (fora da tabela) | R$ 623,76 | **R$ 433,76** | usa a tabela padrão inteira; `f-003` recusada (categoria só existe no CC-COMERCIAL) |

Entrada, saída, todas as regras (RN-001 a RN-013) e as 24 ambiguidades
resolvidas estão documentadas em
[`spec.md`](specs/001-motor-reembolso/spec.md) §4 a §7.

## Documentação

| Arquivo | O que responde |
|---|---|
| [`spec.md`](specs/001-motor-reembolso/spec.md) | O **quê** e o **porquê**: regras de negócio, as 24 ambiguidades e as decisões, casos de borda, ordem de aplicação |
| [`plan.md`](specs/001-motor-reembolso/plan.md) | O **como**: stack, arquitetura, modelo de dados, decisões técnicas, estratégia de testes |
| [`tasks.md`](specs/001-motor-reembolso/tasks.md) | Em que **ordem**: T-001 a T-036, com critério de aceite e matriz de cobertura |
| [`DECISIONS.md`](specs/001-motor-reembolso/DECISIONS.md) | O que **mudou** na spec, quando e por quê |
| [`CLAUDE.md`](CLAUDE.md) | Convenções do projeto para o agente |
| [`docs/RELATORIO.md`](docs/RELATORIO.md) | Relatório final: delegação, descrição, discernimento, diligência e o envelope |

Se o código e a spec discordarem, a spec está certa e o código é o bug.

## Material do desafio

Este repositório é um fork do desafio de Spec Driven Development. O enunciado
original está em [`DESAFIO.md`](DESAFIO.md), a rubrica em [`RUBRICA.md`](RUBRICA.md),
o FAQ de processo em [`FAQ.md`](FAQ.md) e os esqueletos de documento em
[`template/`](template/). O comunicado da mudança de requisito do Dia 2 está
preservado em
[`exemplos/envelope/00-ENVELOPE-LACRADO.md`](exemplos/envelope/00-ENVELOPE-LACRADO.md).
