# CLAUDE.md

## O projeto

Motor de cálculo de reembolso de despesas corporativas. CLI que lê um JSON de
despesas — e, desde a Política v4, um documento de política e um de câmbio —
e emite um JSON com o valor reembolsável e a justificativa de cada item.

## Fonte da verdade

`specs/001-motor-reembolso/spec.md` define **o que** o sistema faz.
`specs/001-motor-reembolso/plan.md` define **como**.
`specs/001-motor-reembolso/tasks.md` define **em que ordem**.

Quando o código e a spec discordarem, a spec está certa e o código é o bug —
a menos que a spec esteja errada, e nesse caso corrigimos a spec primeiro e
registramos em `DECISIONS.md`.

**Antes de implementar qualquer coisa, leia a task correspondente em `tasks.md`.**
Se o que eu pedi não está coberto por nenhuma task, me avise em vez de implementar.

## Regras de trabalho

- Toda regra de negócio vive na spec, não no chat e não em comentário de código.
- Se eu te explicar uma regra que não está na spec, **pare e me diga isso** antes
  de escrever código. Isso é um bug de spec.
- Todo commit de código referencia uma task, sempre em dois — teste antes de
  implementação, sem exceção a partir de T-023: `test(T-003): <descrição>`
  seguido de `feat(T-003): <descrição>`.
- Escopos de commit em uso neste projeto: `docs(spec):`, `docs(plan):`,
  `docs(tasks):` (mudança de documento correspondente), `docs(envelope):`
  (incorporação de material do envelope do Dia 2) e `docs:` /
  `docs(sessions):` (demais documentação e exports de sessão).
- Nenhuma regra de negócio entra sem teste.

## Stack e comandos

- Linguagem: Python 3.11+, apenas biblioteca padrão em `src/`
- Rodar: `python -m src.cli calcular --input exemplos/despesas-exemplo.json --output resultado.json`
  (`--politica` e `--cambio` são opcionais — default resolvido a partir da
  raiz do pacote, apontando para `exemplos/envelope/`)
- Testes: `pytest`
- Testes de uma regra só: `pytest -k rn_012`
- Lint/format: não configurado. `pytest` é a única dependência do projeto
  (`plan.md` DT-005). Siga o estilo do arquivo que estiver editando.

## Convenções de código

- Português nos nomes de domínio (`Despesa`, `valor_reembolsavel`, `teto`).
  Inglês só onde a linguagem obriga.
- `src/motor/` é núcleo puro: **não importa** `json`, `argparse`, `pathlib` nem
  `open`. Toda I/O vive em `src/io/` e `src/cli.py` (`plan.md` DT-003) — inclusive
  a leitura dos documentos de política e câmbio.
- Um passo por regra de negócio, assinatura `(Despesa, Contexto) -> Parecer |
  Despesa | None` (`plan.md` DT-002, DT-007): `None` significa "não decidi,
  siga para a próxima"; `Parecer` significa "decidi, pare"; `Despesa` significa
  "transformei, continue com esta a partir daqui" (só `normalizar_categoria` e
  `rn_011_conversao_cambial` usam o terceiro caso). A ordem de aplicação é a da
  `spec.md` §8 e vive numa lista declarada (`construir_passos`), não em `if`
  aninhado.
- Estruturas são `@dataclass(frozen=True)`. Nenhuma regra altera uma despesa no
  lugar; cada passo devolve um valor novo. Totais são propriedades calculadas,
  nunca campos armazenados.
- Política e câmbio são estruturas consultáveis (`motor/politica.py`,
  `motor/cambio.py`), carregadas de documentos externos na fronteira de I/O
  (`plan.md` DT-008) — nunca constantes de módulo.
- Todo `Parecer` carrega em `regras_aplicadas` os IDs `RN-00X` que o produziram.
- Nome de teste começa pelo ID da regra: `test_rn_012_<comportamento>` (DT-006).
- Fronteira testada dos dois lados: se a spec fixa R$ 100,00, existem casos para
  R$ 100,00 **e** R$ 100,01.
- Valores monetários: `decimal.Decimal` sempre. Leitura com
  `json.load(f, parse_float=Decimal)` e arredondamento único de duas casas com
  `ROUND_HALF_UP` — na construção da `Despesa` para valores em reais, ou
  imediatamente após a conversão cambial para valores em moeda estrangeira
  (RN-010). `float` em dinheiro é bug, não estilo. Na saída, valor vira texto
  com duas casas.

## Fora de escopo

Manda a `spec.md` §3. Em resumo: não aprova pagamento, não valida autenticidade
de nota, não consulta sistema externo em tempo de execução (as entradas são
três documentos fornecidos: despesas, política e câmbio), não diferencia
política por cargo ou senioridade, não faz rateio, não adivinha entrada
malformada e não guarda estado entre execuções — inclusive a fila de aprovação
opcional (RN-013) não persiste pendências de uma execução para a outra.

Diferente da v3, a v4 **diferencia política por centro de custo** (RN-012) e
**trata despesas em moeda estrangeira** (RN-011) — não são mais itens de fora
de escopo. Ver `DECISIONS.md` D-002/D-003.

Não invente campo de entrada que não esteja na `spec.md` §4. As lacunas conhecidas
da entrada (viagem, número de diárias) estão na `spec.md` §10 como questões em
aberto — são decisão de produto, não de implementação.
