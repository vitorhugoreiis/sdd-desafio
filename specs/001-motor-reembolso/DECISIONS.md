# Log de Decisões e Mudanças de Spec

> Uma entrada **toda vez** que a spec mudar. Este arquivo é a prova de que a spec
> foi tratada como artefato vivo e não como cerimônia de abertura.
>
> Spec que não muda em dois dias é spec que ninguém consultou. Mudança não é
> demérito — mudança não registrada é.

Ordem cronológica inversa: a mais recente primeiro.

---

## D-004 — Fila de aprovação manual: opcional, entra como último passo do pipeline · `2026-07-31`

**Gatilho:** o envelope do Dia 2 (`exemplos/envelope/00-ENVELOPE-LACRADO.md`,
bloco C, explicitamente marcado como opcional pelo próprio comunicado)
informa que itens cujo valor reembolsável passe de R$ 500,00 deixam de ser
aprovados automaticamente e entram em estado de pendência aguardando
aprovação do gestor.

**O que mudou na spec:** `spec.md` §4 ganhou o campo `itens[].estado` na
saída (`aprovacao_automatica` | `pendente_aprovacao`) e os agregados
`resumo.quantidade_por_estado` e `resumo.total_pendente_aprovacao`. Regra
nova RN-013, explicitamente marcada como opcional no próprio texto da regra.
Ambiguidade nova AMB-024 resolve a fronteira de R$ 500,00 (estrita), se o
estado substitui o status (não substitui) e se o valor pendente já entra no
total reembolsável (entra). §8 ganha um décimo passo, que roda depois da
decisão de cada despesa e nunca recusa.

**Por quê:** requisito de negócio do envelope (bloco C). Entra na spec
porque o próprio comunicado pede para tratar toda mudança — inclusive esta
— com o mesmo processo de identificar, decidir, justificar e registrar. O
que é opcional é a implementação em código chegar ao fim, não o registro da
decisão de negócio.

**O que isso invalidou:** nada da versão 1.1 é contradito — é aditivo. Se a
Fase 8 (T-035/T-036 em `tasks.md`) não fechar com os testes verdes, esta
entrada será substituída por uma nova que reescreve RN-013 e `spec.md` §3
declarando o item C fora de escopo desta entrega, para nunca deixar a spec
descrevendo um comportamento que o código não tem.

**Tasks afetadas:** T-035 e T-036 (Fase 8 de `tasks.md`), condicionadas à
Fase 7 estar inteiramente verde antes de começar.

**Custo:** `spec.md`, `tasks.md`, este `DECISIONS.md`; em código, um enum de
estado e uma função de decisão executada após a lista de regras — não
compete com nenhuma regra existente porque nunca recusa.

---

## D-003 — Despesas internacionais: conversão cambial antes de qualquer limite · `2026-07-31`

**Gatilho:** o envelope do Dia 2 (bloco B) informa que colaboradores em
viagem internacional podem lançar despesas em moeda estrangeira. O campo
`moeda` (ISO 4217) passa a ser aceito na entrada — ausente ⇒ `BRL` — e a
conversão usa a taxa de câmbio da data da própria despesa; os limites da
política continuam sempre em reais.

**O que mudou na spec:** `spec.md` §3 perdeu a linha "não trata moeda
diferente de real". §4 ganhou o campo `despesas[].moeda` na entrada, o
contrato do documento de câmbio (taxas por data e por moeda) e, na saída, os
campos por item `moeda`, `valor_origem`, `taxa_cambio` e `data_taxa`. Regra
nova RN-011 (conversão cambial, incluindo o caso de data sem cotação
publicada e de moeda ausente da tabela). RN-004 (duplicata) passou a incluir
a moeda na chave; RN-006 (nota fiscal) passou a comparar o piso ao valor já
convertido em reais; RN-010 (arredondamento) foi estendida ao valor
convertido. Seis ambiguidades novas — AMB-018 a AMB-023 — documentam as
decisões sobre fim de semana sem cotação, moeda sem cotação, arredondamento
da conversão, em que moeda o piso de nota fiscal é comparado, a chave de
duplicata e como um item não convertível entra num total que é sempre em
reais.

**Por quê:** requisito de negócio do envelope (bloco B), não decisão de
implementação — a única escolha de arquitetura embutida aqui é *onde* a
conversão entra no pipeline (ver DT-007 em `plan.md`), e isso pertence ao
`plan.md`, não à spec.

**O que isso invalidou:** `spec.md` §3 (versão 1.1); o modelo de dados da
despesa em `plan.md` §3 ganha campos novos; o schema de saída documentado em
`spec.md` §4 ganha quatro campos por item. Nenhum critério de aceite da
versão 1.1 usava moeda, então nada de `spec.md` §9 (v1.1) foi contradito —
apenas estendido pelos dois arquivos novos do envelope.

**Tasks afetadas:** T-027 a T-031 (Fase 6 de `tasks.md`): campos novos em
`Despesa`, o módulo de câmbio, o passo de conversão no pipeline (DT-007),
RN-011 completa e a extensão de RN-004 e do serializador. T-033 reexecuta os
dois arquivos do envelope como teste ponta a ponta.

**Custo:** `spec.md`, `plan.md`, `tasks.md`, este `DECISIONS.md`, mais dois
módulos novos em código e um ponto de resistência arquitetural real: a
assinatura `(Despesa, Contexto) -> Parecer | None` do Dia 1 não comporta um
passo que transforma a despesa e pode recusar. Isso vira DT-007 em
`plan.md`, não uma regra de negócio nova.

---

## D-002 — Política v4: limites variam por centro de custo, política sai do código · `2026-07-31`

**Gatilho:** o envelope do Dia 2 (bloco A) informa que a política deixa de
ser única para toda a empresa: cada centro de custo passa a ter sua própria
tabela de limites, mantida pelo financeiro num documento à parte, sujeito a
mudar sem aviso. O centro de custo do exemplo oficial (`CC-ENG-PLATAFORMA`)
passa a ter `hospedagem` com limite R$ 0,00 e `alimentacao` com limite
R$ 75,00 — na v3 esses dois valores eram constantes fixas de R$ 250,00 e
R$ 60,00 para toda a empresa.

**O que mudou na spec:** `spec.md` avançou de 1.1 para 1.2. §3 perdeu a
linha "não aplica política diferente por centro de custo" (mantendo cargo e
senioridade fora de escopo). §4 ganhou o contrato do documento de política
(`padrao`, `centros_custo`, `nota_fiscal_obrigatoria_acima_de`,
`acrescimo_em_viagem_percentual`, `versao`, `vigencia`) e a saída ganhou o
bloco `politica` no cabeçalho. RN-001 e RN-007 foram emendadas para
consultar a tabela do centro de custo em vez de constantes fixas. Regra nova
RN-012 (resolução do limite por centro de custo, incluindo o merge
padrão+override e o caso de limite R$ 0,00) e as ambiguidades que essa
resolução expõe — AMB-013 e AMB-014.

**Por quê:** é literalmente o que o comunicado do RH pede (bloco A) — não é
uma escolha de implementação, é requisito de negócio chegando fora de ciclo,
exatamente o cenário que a `spec.md` §10 da versão 1.1 já cogitava ("a
política não versiona seus limites").

**O que isso invalidou:** o critério de aceite mais visível da spec — **o
total reembolsável de `exemplos/despesas-exemplo.json` muda de R$ 703,43
(v1.1) para R$ 341,93 (v1.2)**, mesmo sem nenhuma mudança na lógica de
cálculo em si. O item `d-010` (hospedagem, R$ 480,00) passa de reembolsável
R$ 375,00 (teto de R$ 250,00 ampliado em 50% por viagem) para R$ 0,00 — o
centro de custo do colaborador não reembolsa hospedagem; `d-001` e `d-014`
deixam de sofrer glosa porque o teto de alimentação deste centro de custo
subiu de R$ 60,00 para R$ 75,00. Invalida `spec.md` §3 e §9 (versão 1.1),
`plan.md` §4 (política como constantes de módulo) e o teste
`test_e2e_exemplo_oficial`, que precisa ser reexecutado com os novos números
— não reescrito às cegas, e sim conferido item a item contra a memória de
cálculo registrada em `docs/HANDOFF-dia2.md`.

**Tasks afetadas:** T-023 a T-026 (Fase 5 de `tasks.md`) implementam a
leitura e a consulta da política externa; T-032 reexecuta
`test_e2e_exemplo_oficial` com os números da versão 1.2.

**Custo:** `spec.md`, `plan.md`, `tasks.md`, este `DECISIONS.md`; em código,
o módulo de política deixa de expor constantes e passa a expor uma estrutura
consultável — o motor absorve a mudança sem alterar a assinatura das regras
(`Contexto` ganha os campos novos; a decisão DT-004 do Dia 1 paga o
dividendo aqui).

---

## D-001 — Corrige ID de regra trocado no exemplo ilustrativo da §4 · `2026-07-30`

**Gatilho:** ao implementar T-012 (RN-007, teto por categoria) na tarde do Dia 1,
o exemplo de saída da `spec.md` §4 rotulava as duas decisões de teto
(`d-001` parcial, `d-002` aprovada) com `regras_aplicadas: ["RN-006"]`. RN-006
é a regra de nota fiscal (§5); a decisão ali descrita é claramente de teto —
RN-007. É inconsistência interna da spec, não ambiguidade de negócio: o
catálogo de regras (§5) e o exemplo (§4) discordavam entre si dentro do mesmo
arquivo.

**O que mudou na spec:** exemplo de saída em `spec.md` §4 — `regras_aplicadas`
de `d-001` e `d-002` passou de `["RN-006"]` para `["RN-007"]`, coerente com a
definição de RN-007 e com a ordem de aplicação da §8. Versão do documento
avançou de 1.0 para 1.1.

**Por quê:** o número de regra errado no único exemplo de saída da spec teria
sido copiado para o código e para os testes se não fosse corrigido antes —
exatamente o tipo de erro que a rastreabilidade regra→teste deveria expor, não
esconder.

**O que isso invalidou:** nada em código ou teste, pois a implementação de
T-012 ainda não existia. Nenhum critério de aceite da §9 cita `regras_aplicadas`
literalmente, então nenhum outro trecho da spec dependia do valor errado.

**Tasks afetadas:** nenhuma tarefa precisou ser refeita; T-012 (RN-007) foi
implementada já com o ID correto.

**Custo:** 2 arquivos (`spec.md`, este `DECISIONS.md`), sem retrabalho de código.
