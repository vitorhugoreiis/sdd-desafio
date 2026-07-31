# Spec — Motor de Cálculo de Reembolso

**Versão:** 1.2 · **Status:** aprovada · **Última alteração:** 2026-07-31

> **Regra de ouro deste arquivo:** ele descreve o QUÊ e o PORQUÊ. Nenhuma linha
> aqui pode citar linguagem, biblioteca, classe, função ou estrutura de pasta.
> Se apareceu solução, o lugar dela é o `plan.md`.
>
> **Teste de aceitação da própria spec:** uma pessoa que nunca viu o projeto
> consegue, lendo só este arquivo, verificar se o sistema está correto?

---

## 1. Problema

O financeiro confere manualmente, item por item, cada despesa lançada por um
colaborador contra a política de reembolso. O processo é lento e inconsistente:
duas pessoas conferindo a mesma planilha chegam a valores diferentes, porque a
política admite mais de uma leitura em vários pontos. O custo aparece como
retrabalho, reembolso pago a maior e contestação de colaborador.

## 2. Objetivo

Dado o conjunto de despesas de um colaborador num período, o sistema decide
quanto é reembolsável e emite, para cada despesa, o valor aprovado e a
justificativa da decisão — de forma reproduzível e auditável.

## 3. Fora de escopo

- Não decide aprovação final: o resultado é um parecer de cálculo, não um pagamento.
- Não valida autenticidade de nota fiscal — apenas registra se o colaborador declarou possuí-la.
- Não consulta sistema externo (RH, ERP, folha, câmbio) em tempo de execução.
  A entrada de cada execução é um conjunto fechado de três documentos —
  despesas do período, tabela de limites por centro de custo e tabela de
  taxas de câmbio — todos fornecidos previamente; nenhum é buscado ao vivo.
- Não diferencia política por cargo ou senioridade. (Diferencia por centro de
  custo — ver RN-012 — o que deixou de ser verdade a partir da versão 1.2.)
- Não faz rateio entre centros de custo.
- Não corrige nem completa dados de entrada malformados: entrada inválida é rejeitada, não adivinhada.
- Não mantém histórico entre execuções. Cada execução considera apenas o
  período, a tabela de política e a tabela de câmbio recebidos naquela
  execução — inclusive o estado de pendência de aprovação da RN-013, que não
  é persistido (ver §10).

## 4. Entrada e saída

**Entrada:** conforme `exemplos/despesas-exemplo.json`, mais os documentos de
política e de câmbio descritos abaixo.

| Campo | Tipo | Significado | Obrigatório |
|---|---|---|---|
| `colaborador.id` | texto | Identificador do colaborador | sim |
| `colaborador.nome` | texto | Nome, para exibição no resultado | sim |
| `colaborador.centro_custo` | texto | Centro de custo, usado para selecionar a tabela de limites (RN-012) e repassado ao resultado | sim |
| `periodo.competencia` | texto `AAAA-MM` | Mês de competência do lançamento | sim |
| `periodo.inicio` | data `AAAA-MM-DD` | Início do período, informativo | sim |
| `periodo.fim` | data `AAAA-MM-DD` | Fim do período, informativo | sim |
| `despesas[].id` | texto | Identificador único da despesa | sim |
| `despesas[].data` | data `AAAA-MM-DD` | Data em que a despesa ocorreu | sim |
| `despesas[].categoria` | texto | Categoria declarada | sim |
| `despesas[].descricao` | texto | Texto livre; **não** é usado em nenhuma decisão de cálculo | sim |
| `despesas[].fornecedor` | texto | Estabelecimento; usado na detecção de duplicata | sim |
| `despesas[].valor` | número | Valor no lançamento original, na moeda de origem; pode ser negativo (estorno) | sim |
| `despesas[].tem_nota_fiscal` | booleano | Declaração de posse de nota fiscal | sim |
| `despesas[].moeda` | texto | Código de moeda ISO 4217 do lançamento; comparado ignorando caixa; ausente ⇒ assume-se `BRL` | não |

**Documento de política:** a tabela de limites que rege o cálculo, mantida
pelo financeiro e sujeita a mudar entre execuções sem que a spec mude junto.

| Campo | Tipo | Significado | Obrigatório |
|---|---|---|---|
| `padrao` | mapa categoria → limite | Tetos por categoria válidos para qualquer centro de custo ausente da tabela, ou para uma categoria não redefinida por um centro de custo presente (RN-012) | sim |
| `centros_custo` | mapa centro de custo → mapa categoria → limite | Tetos que sobrepõem o padrão, categoria a categoria, para o centro de custo indicado (RN-012, AMB-013) | não — ausência de um centro de custo específico ⇒ ele usa o padrão inteiro |
| `nota_fiscal_obrigatoria_acima_de` | número | Piso, em reais, acima do qual a nota fiscal é exigida (RN-006) | sim |
| `acrescimo_em_viagem_percentual` | número | Percentual de ampliação dos tetos por categoria em data de viagem (RN-009) | sim |
| `versao`, `vigencia` | texto | Identificação e data de vigência da tabela recebida nesta execução; informativos, repassados ao resultado para auditoria — não validados contra a data de nenhuma despesa (AMB-017) | sim |

**Documento de câmbio:** as taxas usadas para converter despesas em moeda
estrangeira para reais antes de compará-las a qualquer limite.

| Campo | Tipo | Significado | Obrigatório |
|---|---|---|---|
| `taxas` | mapa data → mapa moeda → taxa | Cotação de fechamento de cada moeda (ISO 4217) em cada data; usada pela conversão cambial (RN-011) | sim |

**Saída:** documento com o mesmo cabeçalho da entrada, um bloco de política
para auditoria, um resumo e um parecer por despesa. Valores monetários são
texto com exatamente duas casas decimais e ponto como separador. Todo valor
de saída derivado de dinheiro — `valor_lancado`, `valor_reembolsavel`,
`valor_glosado` e todos os totais do resumo — está **sempre em reais**,
mesmo quando o lançamento original veio em outra moeda.

| Campo | Tipo | Significado |
|---|---|---|
| `colaborador`, `periodo` | objeto | Copiados da entrada, sem alteração |
| `politica.versao`, `politica.vigencia` | texto | Copiados do documento de política recebido nesta execução |
| `politica.centro_custo_aplicado` | texto | Centro de custo do colaborador, repetido aqui para conveniência de auditoria |
| `politica.origem_dos_limites` | texto | `"centro_custo"` quando a tabela do centro de custo foi usada, `"padrao"` quando o centro de custo estava ausente da tabela (RN-012) |
| `resumo.total_lancado` | texto | Soma dos valores lançados **em reais**, após arredondamento e conversão (AMB-023: um item não convertível contribui `0.00`) |
| `resumo.total_reembolsavel` | texto | Soma dos valores reembolsáveis, estornos incluídos, itens pendentes de aprovação incluídos (AMB-024) |
| `resumo.total_glosado` | texto | `total_lancado` − `total_reembolsavel` |
| `resumo.quantidade_por_status` | objeto | Contagem de itens em cada status |
| `resumo.quantidade_por_estado` | objeto | Contagem de itens em cada estado de aprovação (RN-013, opcional) |
| `resumo.total_pendente_aprovacao` | texto | Soma de `valor_reembolsavel` dos itens com estado `pendente_aprovacao` (RN-013, opcional) |
| `itens[].id`, `.data`, `.categoria` | texto | Identificação da despesa; `categoria` já normalizada |
| `itens[].moeda` | texto | Código ISO 4217 da moeda de origem do lançamento; `BRL` quando ausente na entrada |
| `itens[].valor_origem` | texto | Valor do lançamento na moeda de origem, antes de qualquer conversão |
| `itens[].taxa_cambio` | texto ou nulo | Taxa usada para converter para reais; nulo quando a moeda de origem já é `BRL` ou quando a despesa foi recusada por falta de cotação (RN-011) |
| `itens[].data_taxa` | texto ou nulo | Data da cotação efetivamente usada; pode diferir de `itens[].data` quando a própria data não tinha cotação publicada (RN-011, AMB-018); nulo nas mesmas condições de `taxa_cambio` |
| `itens[].valor_lancado` | texto | Valor de entrada em reais, após arredondamento e conversão |
| `itens[].valor_reembolsavel` | texto | Valor aprovado, em reais; negativo em estorno |
| `itens[].valor_glosado` | texto | `valor_lancado` − `valor_reembolsavel` |
| `itens[].status` | texto | `aprovada`, `parcial`, `recusada` ou `estorno` |
| `itens[].estado` | texto | `aprovacao_automatica` ou `pendente_aprovacao` (RN-013, opcional) — informação adicional, não substitui `status` |
| `itens[].regras_aplicadas` | lista de texto | IDs das regras que determinaram o resultado |
| `itens[].justificativa` | texto | Frase legível explicando a decisão |

**Status:** `aprovada` = reembolsada integralmente · `parcial` = reembolsada com
glosa · `recusada` = reembolso zero · `estorno` = valor negativo abatido do total.

**Estado (opcional, RN-013):** `aprovacao_automatica` = segue o fluxo normal ·
`pendente_aprovacao` = valor reembolsável acima de R$ 500,00, aguardando
aprovação do gestor. O estado é ortogonal ao status: um item `parcial` pode
estar `pendente_aprovacao`, por exemplo.

Exemplo de saída para uma entrada de duas despesas do centro de custo
CC-ENG-PLATAFORMA — um almoço de R$ 82,50 e um jantar de R$ 38,00, ambos com
nota, no mesmo dia, sem nenhuma delas em moeda estrangeira:

```json
{
  "colaborador": { "id": "c-0417", "nome": "Marina Volpi", "centro_custo": "CC-ENG-PLATAFORMA" },
  "periodo": { "competencia": "2026-07", "inicio": "2026-07-01", "fim": "2026-07-31" },
  "politica": {
    "versao": "v4",
    "vigencia": "2026-07-01",
    "centro_custo_aplicado": "CC-ENG-PLATAFORMA",
    "origem_dos_limites": "centro_custo"
  },
  "resumo": {
    "total_lancado": "120.50",
    "total_reembolsavel": "113.00",
    "total_glosado": "7.50",
    "quantidade_por_status": { "aprovada": 1, "parcial": 1, "recusada": 0, "estorno": 0 },
    "quantidade_por_estado": { "aprovacao_automatica": 2, "pendente_aprovacao": 0 },
    "total_pendente_aprovacao": "0.00"
  },
  "itens": [
    {
      "id": "d-001",
      "data": "2026-07-03",
      "categoria": "alimentacao",
      "moeda": "BRL",
      "valor_origem": "82.50",
      "taxa_cambio": null,
      "data_taxa": null,
      "valor_lancado": "82.50",
      "valor_reembolsavel": "75.00",
      "valor_glosado": "7.50",
      "status": "parcial",
      "estado": "aprovacao_automatica",
      "regras_aplicadas": ["RN-007", "RN-012"],
      "justificativa": "Valor acima do teto de R$ 75,00 para alimentacao no centro de custo CC-ENG-PLATAFORMA. Excedente de R$ 7,50 glosado."
    },
    {
      "id": "d-002",
      "data": "2026-07-03",
      "categoria": "alimentacao",
      "moeda": "BRL",
      "valor_origem": "38.00",
      "taxa_cambio": null,
      "data_taxa": null,
      "valor_lancado": "38.00",
      "valor_reembolsavel": "38.00",
      "valor_glosado": "0.00",
      "status": "aprovada",
      "estado": "aprovacao_automatica",
      "regras_aplicadas": ["RN-007", "RN-012"],
      "justificativa": "Valor dentro do teto de R$ 75,00 para alimentacao no centro de custo CC-ENG-PLATAFORMA."
    }
  ]
}
```

## 5. Regras de negócio

### RN-001 — Categorias cobertas pela política

**Regra:** só são reembolsáveis as categorias presentes na tabela de política
efetivamente aplicada ao centro de custo do colaborador (padrão sobreposto
pelo centro de custo — ver RN-012). Qualquer outra categoria é recusada com
valor zero e permanece no resultado com justificativa — não é omitida.
**Origem:** política do RH v3, item 9; emendada pela v4 (comunicado bloco A)
**Aceite:** uma despesa de categoria `coworking`, ausente de qualquer tabela,
resulta em reembolsável R$ 0,00, status `recusada`, em qualquer centro de
custo; uma despesa de categoria `representacao` é recusada num centro de
custo cuja tabela não define essa categoria, mesmo que outro centro de custo
a defina.

### RN-002 — Normalização da categoria

**Regra:** a categoria declarada é comparada com a política ignorando maiúsculas
e minúsculas e espaços nas pontas. A categoria normalizada é a que aparece no
resultado.
**Origem:** política do RH, item 9 (decorrente de AMB-012)
**Aceite:** uma despesa com categoria `"ALIMENTACAO"` é tratada como
`alimentacao` e concorre ao teto da sua categoria, não é recusada por categoria.

### RN-003 — Período de competência

**Regra:** só é reembolsável a despesa cuja data pertença ao mês indicado em
`periodo.competencia`. Despesa fora dele é recusada com valor zero e permanece no
resultado com justificativa. Os campos `periodo.inicio` e `periodo.fim` são
informativos e não decidem nada.
**Origem:** política do RH, item 7
**Aceite:** com competência `2026-07`, uma despesa de `2026-04-15` no valor de
R$ 41,00 resulta em reembolsável R$ 0,00, status `recusada`.

### RN-004 — Duplicatas

**Regra:** duas ou mais despesas são duplicatas entre si quando coincidem em
data, categoria normalizada, fornecedor, descrição, valor de origem **e
moeda**. A primeira na ordem de aparição na entrada é processada normalmente;
as demais são recusadas com valor zero.
**Origem:** política do RH, item 8; chave emendada pela v4 (AMB-022)
**Aceite:** duas despesas idênticas de R$ 54,90 em `2026-07-09` no mesmo
fornecedor resultam em R$ 54,90 para a primeira e R$ 0,00 para a segunda; a
mesma comparação com valores numericamente iguais mas em moedas diferentes
não é duplicata — ambas são processadas.

### RN-005 — Estornos

**Regra:** despesa com valor negativo é um estorno. Ela não passa por exigência
de nota fiscal, teto nem conversão cambial: entra no total pelo seu valor
integral em reais, reduzindo o reembolso. Estorno não consome nem devolve
teto de nenhuma outra despesa, e nunca recebe estado de pendência de
aprovação (RN-013).
**Origem:** não prevista na política (decorrente de AMB-010)
**Aceite:** uma despesa de −R$ 45,00 resulta em reembolsável −R$ 45,00, status
`estorno`, e reduz o total do período em R$ 45,00.

### RN-006 — Exigência de nota fiscal

**Regra:** despesa cujo valor **em reais** — já convertido, quando aplicável —
seja **estritamente maior** que o piso definido na política exige nota fiscal
declarada. Sem ela, a despesa é recusada integralmente. Valor exatamente igual
ao piso não exige nota. O piso não é ampliado por viagem.
**Origem:** política do RH, item 5; emendada pela v4 (piso passa a vir da
política, comparação passa a ser sobre o valor convertido — AMB-021)
**Aceite:** com piso de R$ 100,00, uma despesa de R$ 100,00 sem nota segue
para o teto e é reembolsada; R$ 100,01 sem nota resulta em R$ 0,00, status
`recusada`; uma despesa de 40,00 USD sem nota, equivalente a R$ 220,00, é
recusada porque o piso é comparado ao valor em reais, não ao valor de origem.

### RN-007 — Tetos por categoria e reembolso parcial

**Regra:** cada despesa é comparada individualmente ao teto da sua categoria
na tabela de política efetivamente aplicada ao centro de custo do colaborador
(RN-012) — os tetos deixam de ser fixos e passam a variar por centro de
custo. O teto é por despesa, não pela soma do dia. Despesa acima do teto é
reembolsada pelo valor do teto; o excedente é glosado.
**Origem:** política do RH v3, itens 1, 2, 3 e 4; tetos emendados pela v4 (comunicado bloco A)
**Aceite:** no centro de custo CC-ENG-PLATAFORMA (teto de alimentação R$ 75,00),
duas despesas de alimentação no mesmo dia, de R$ 82,50 e R$ 38,00, resultam em
R$ 75,00 e R$ 38,00.

### RN-008 — Hospedagem é uma diária por lançamento

**Regra:** cada lançamento de hospedagem vale como uma diária, qualquer que seja
o número de noites mencionado na descrição. O teto incide sobre o valor
lançado inteiro (já em reais).
**Origem:** política do RH, item 3 (decorrente de AMB-007)
**Aceite:** hospedagem de R$ 480,00 descrita como "2 diarias", fora de viagem,
num centro de custo com teto de hospedagem R$ 250,00, é reembolsada em R$ 250,00.

### RN-009 — Ampliação por viagem

**Regra:** o colaborador é considerado em viagem numa data quando existe, nessa
mesma data, ao menos um lançamento de categoria `hospedagem` — independentemente
de esse lançamento ter sido aprovado, recusado ou ter teto igual a R$ 0,00
(AMB-015). Nas datas em viagem, os tetos de categoria da RN-007 são ampliados
pelo percentual definido na política. A ampliação não alcança o piso de nota
fiscal da RN-006.
**Origem:** política do RH v3, item 6 (decorrente de AMB-006); percentual
passa a vir da política a partir da v4
**Aceite:** hospedagem de R$ 480,00 em `2026-07-14`, num centro de custo com
teto de hospedagem R$ 250,00 e acréscimo de 50%, é reembolsada em R$ 375,00;
num centro de custo cujo teto de hospedagem é R$ 0,00, a mesma hospedagem é
recusada, mas a data continua caracterizando viagem para as demais despesas.

### RN-010 — Arredondamento

**Regra:** todo valor de entrada é arredondado para duas casas decimais, meio
para cima, antes de qualquer comparação. Para despesas em moeda estrangeira,
o arredondamento ocorre uma única vez, imediatamente após a conversão para
reais (RN-011) — o valor de origem e a taxa de câmbio não são arredondados
antes disso. Todos os cálculos e somas posteriores usam o valor já
arredondado, e nenhum arredondamento adicional ocorre depois.
**Origem:** não prevista na política (decorrente de AMB-011); estendida à
conversão cambial pela v4 (AMB-020)
**Aceite:** uma despesa lançada como `33.333` BRL é tratada como R$ 33,33 em
todas as comparações; uma despesa de 14,50 EUR convertida a 5,88 é tratada
como R$ 85,26, resultado exato de uma única multiplicação e um único
arredondamento.

### RN-011 — Conversão cambial (nova, v4)

**Regra:** despesas em moeda diferente de `BRL` são convertidas para reais
usando a taxa de câmbio da data da própria despesa. Quando não há cotação
publicada para aquela data, usa-se a cotação de fechamento da última data
anterior disponível para aquela moeda. Quando não existe nenhuma cotação
anterior, ou a moeda está inteiramente ausente da tabela de câmbio, a despesa
é recusada e permanece no resultado com valor reembolsável R$ 0,00, mantendo
visíveis o valor e a moeda de origem.
**Origem:** comunicado do RH, bloco B (v4)
**Aceite:** uma despesa de 30,00 EUR lançada num sábado sem cotação publicada
é convertida pela cotação de fechamento da sexta-feira anterior; uma despesa
de 55,00 GBP, moeda ausente da tabela de câmbio, é recusada com valor
reembolsável R$ 0,00, mantendo `55.00` e `GBP` visíveis no item.

### RN-012 — Limites por centro de custo (nova, v4)

**Regra:** os limites de cada categoria vêm da tabela de política do centro
de custo do colaborador. Quando o centro de custo não consta da tabela,
aplica-se a tabela padrão inteira. Quando o centro de custo consta da tabela
mas não define uma categoria específica, essa categoria herda o limite
padrão (a tabela do centro de custo sobrepõe o padrão, não o substitui —
AMB-013). Um limite de R$ 0,00 significa que a categoria não é reembolsável
naquele centro de custo: a despesa correspondente é recusada, não reembolsada
parcialmente (AMB-014).
**Origem:** comunicado do RH, bloco A (v4)
**Aceite:** um centro de custo ausente da tabela usa os limites padrão para
todas as categorias; um centro de custo presente na tabela mas sem uma
categoria usa o limite padrão dessa categoria; uma categoria com limite
R$ 0,00 no centro de custo do colaborador resulta sempre em reembolsável
R$ 0,00, status `recusada`, qualquer que seja o valor lançado.

### RN-013 — Fila de aprovação manual (nova, v4, opcional)

**Regra:** todo item cujo valor reembolsável seja **estritamente maior** que
R$ 500,00 recebe o estado `pendente_aprovacao`, além do status normal de
cálculo. Os demais itens recebem o estado `aprovacao_automatica`. O estado é
informação adicional sobre o item — não substitui o status nem altera o
valor reembolsável, que já entra nos totais do resumo. Estorno nunca recebe
estado de pendência (RN-005).
**Origem:** comunicado do RH, bloco C (v4) — item explicitamente opcional
**Aceite:** um item com valor reembolsável de R$ 600,00 recebe estado
`pendente_aprovacao`; um item de exatamente R$ 500,00 recebe estado
`aprovacao_automatica`.

---

## 6. Ambiguidades identificadas e decisões

> **Esta seção é o coração da spec.** Uma ambiguidade que foi resolvida no código
> sem estar registrada aqui conta como não resolvida.

### AMB-001 — "por dia" é por despesa ou por soma do dia?

**Texto original do RH:** "Alimentação tem limite de R$ 60 por dia."
**Tipo:** unidade de aplicação
**O que não está claro:** o teto incide sobre cada despesa isolada ou sobre a soma das despesas da categoria naquela data.
**Âncora no exemplo:** `d-001` (72,50) + `d-002` (38,00) no dia 03/07. Por despesa → 60,00 + 38,00 = 98,00. Por dia → 60,00.
**Decisão:** o teto incide sobre cada despesa individualmente.
**Justificativa:** o teto funciona como limite de razoabilidade por consumo, e o financeiro precisa justificar a glosa item a item para o colaborador — o que a leitura agregada não permite.
**Regra afetada:** RN-007

### AMB-002 — "reembolsadas parcialmente" significa cortar ou recusar?

**Texto original do RH:** "Despesas acima do limite são reembolsadas parcialmente."
**Tipo:** unidade de aplicação
**O que não está claro:** paga-se o teto e descarta-se o excedente, ou o item inteiro é recusado por violar o teto.
**Âncora no exemplo:** `d-014` (61,00 contra teto de 60,00 na v3). Cortar → 60,00. Recusar → 0,00.
**Decisão:** paga-se o valor do teto e o excedente é glosado.
**Justificativa:** é a leitura literal de "parcialmente"; recusar o item inteiro puniria o colaborador por um centavo de excesso.
**Regra afetada:** RN-007

### AMB-003 — "acima de R$ 100" inclui os R$ 100?

**Texto original do RH:** "Nota fiscal é obrigatória acima de R$ 100."
**Tipo:** fronteira
**O que não está claro:** a comparação é `> 100` ou `>= 100`.
**Âncora no exemplo:** `d-003` vale exatamente 100,00 e `d-004` vale 100,01 — ambas sem nota fiscal. O par existe para forçar esta decisão.
**Decisão:** a comparação é estrita: exatamente o valor do piso não exige nota fiscal.
**Justificativa:** "acima de" exclui o próprio valor em português corrente, e a leitura restritiva não pode ser presumida contra o colaborador.
**Regra afetada:** RN-006

### AMB-004 — falta de nota fiscal recusa o item ou limita o valor?

**Texto original do RH:** "Nota fiscal é obrigatória acima de R$ 100."
**Tipo:** unidade de aplicação
**O que não está claro:** sem nota, o item é recusado integralmente, ou é reembolsado até o piso (a parte que não exigiria nota).
**Âncora no exemplo:** `d-013` (690,00, sem nota). Recusa → 0,00. Limite ao piso → 100,00.
**Decisão:** a despesa é recusada integralmente.
**Justificativa:** a nota é o documento que comprova a despesa; sem ela não há o que reembolsar, nem parcialmente — reembolsar até o piso criaria incentivo a omitir nota.
**Regra afetada:** RN-006

### AMB-005 — a exigência de nota olha o valor lançado ou o valor já limitado?

**Texto original do RH:** itens 4 e 5 combinados.
**Tipo:** fronteira / ordem
**O que não está claro:** se o teto diário for aplicado antes, o valor pode cair abaixo do piso e dispensar a nota; se a nota for exigida antes, o item cai antes de chegar ao teto.
**Âncora no exemplo:** `d-004` (100,01, transporte, sem nota). Teto primeiro → abaixo do piso, nota dispensada. Nota primeiro → item recusado.
**Decisão:** a exigência de nota é avaliada primeiro, sobre o valor lançado (em reais, ver AMB-021).
**Justificativa:** a obrigação de documentar nasce do valor que o colaborador gastou, não do valor que a empresa decidiu pagar.
**Regra afetada:** RN-006 · define a §8

### AMB-006 — o que caracteriza "em viagem"?

**Texto original do RH:** "Colaborador em viagem tem limites ampliados em 50%."
**Tipo:** dado ausente
**O que não está claro:** não existe campo de viagem na entrada. Precisa ser inferido, declarado como não suportado, ou exigido como campo novo. Além disso: a ampliação alcança também o piso da nota fiscal, ou só os tetos por categoria?
**Âncora no exemplo:** nenhuma despesa traz marcação de viagem; `d-010` e `d-013` são hospedagens que poderiam servir de indício.
**Decisão:** viagem é inferida pela existência de lançamento de hospedagem na mesma data, aprovado ou não. A ampliação alcança apenas os tetos por categoria, não o piso da nota fiscal.
**Justificativa:** hospedagem é o indício mais direto de pernoite fora, e é o único disponível na entrada; o piso da nota é regra de comprovação, não de limite de gasto, e não há razão para afrouxá-lo em viagem.
**Regra afetada:** RN-009

### AMB-007 — "por diária" quando a entrada traz um valor só

**Texto original do RH:** "Hospedagem tem limite de R$ 250 por diária."
**Tipo:** dado ausente
**O que não está claro:** a entrada tem uma data e um valor agregado; o número de diárias só aparece no texto livre da descrição, que não é campo estruturado.
**Âncora no exemplo:** `d-010` = 480,00 "2 diarias" (240,00/noite). `d-013` = 690,00 "3 noites" (230,00/noite).
**Decisão:** cada lançamento de hospedagem conta como uma diária; a descrição não é interpretada.
**Justificativa:** derivar número de diárias de texto livre tornaria o resultado dependente da redação do colaborador, o que é o oposto de auditável — a correção certa é o campo passar a existir na entrada.
**Regra afetada:** RN-008 · consequência registrada na §10

### AMB-008 — o que é uma duplicata e o que é "tratar"

**Texto original do RH:** "Duplicatas devem ser tratadas."
**Tipo:** unidade de aplicação
**O que não está claro:** qual combinação de campos caracteriza duplicata, e o que se faz com ela — descartar a segunda, recusar as duas, ou apenas sinalizar.
**Âncora no exemplo:** `d-006` e `d-007` são idênticas em data, categoria, descrição, fornecedor e valor — diferem só no `id`.
**Decisão:** duplicata é a coincidência de data, categoria, fornecedor, descrição e valor (e, a partir da v4, moeda — AMB-022); a primeira ocorrência é paga e as demais são recusadas.
**Justificativa:** pagar as duas assume erro do financeiro e recusar as duas pune o colaborador por um lançamento legítimo — pagar a primeira é a única leitura que não escolhe um lado sem evidência.
**Regra afetada:** RN-004 · consequência registrada na §10

### AMB-009 — qual campo define a competência, e o que acontece fora dela

**Texto original do RH:** "Despesas devem ser lançadas dentro do período de competência."
**Tipo:** fronteira / dado ausente
**O que não está claro:** a entrada traz `competencia` e também `inicio`/`fim` — qual governa se divergirem. E o item fora do período é recusado com justificativa ou excluído do resultado.
**Âncora no exemplo:** `d-008` é de 2026-04-15, fora de julho.
**Decisão:** `periodo.competencia` governa; `inicio` e `fim` são informativos. A despesa fora do período é recusada com valor zero e **permanece** no resultado.
**Justificativa:** competência é o conceito contábil que a política cita, e omitir o item do resultado esconderia do colaborador o motivo de não ter sido pago.
**Regra afetada:** RN-003

### AMB-010 — valor negativo (estorno)

**Texto original do RH:** silente.
**Tipo:** dado ausente
**O que não está claro:** a política não prevê valor negativo. Ele abate o total, é ignorado, é rejeitado como entrada inválida, ou reduz o consumo do teto diário.
**Âncora no exemplo:** `d-009` = −45,00, transporte urbano, 11/07.
**Decisão:** o estorno abate o total pelo valor integral, sem passar por teto nem por exigência de nota.
**Justificativa:** o estorno é a devolução de um valor já adiantado; aplicar teto sobre ele reduziria a devolução e faria a empresa reter dinheiro do colaborador.
**Regra afetada:** RN-005

### AMB-011 — arredondamento: quantas casas e em que momento

**Texto original do RH:** silente.
**Tipo:** fronteira
**O que não está claro:** a entrada admite mais de duas casas decimais. Arredonda-se na leitura, a cada regra, ou só no total — e para cima, para baixo ou meio-a-par.
**Âncora no exemplo:** `d-011` = 33,333.
**Decisão:** arredonda-se para duas casas, meio para cima, uma única vez, na leitura.
**Justificativa:** real não tem fração de centavo, e arredondar uma só vez no começo garante que o item e o total nunca discordem entre si.
**Regra afetada:** RN-010

### AMB-012 — categoria com grafia diferente

**Texto original do RH:** "Categorias fora da política não são reembolsáveis."
**Tipo:** fronteira
**O que não está claro:** a comparação de categoria é literal ou normalizada. Se for literal, uma diferença de caixa joga o item para fora da política.
**Âncora no exemplo:** `d-014` vem como `"ALIMENTACAO"`; todas as outras vêm minúsculas. `d-005` (`coworking`) é o caso de categoria genuinamente fora da política.
**Decisão:** a comparação ignora caixa e espaços nas pontas.
**Justificativa:** diferença de maiúscula é ruído de digitação, não intenção de lançar em outra categoria; recusar por isso seria erro de forma travando direito de fundo.
**Regra afetada:** RN-002

### AMB-013 — "aplica-se a política padrão": centro de custo ausente ou categoria ausente dentro de um centro de custo presente?

**Texto original do RH:** "Alguns centros de custo não têm entrada na tabela. Nesse caso, aplica-se a política padrão."
**Tipo:** unidade de aplicação
**O que não está claro:** a frase cobre só o centro de custo inteiramente ausente da tabela, ou também uma categoria ausente dentro de um centro de custo que está presente?
**Âncora nos dados do envelope:** CC-ADM está na tabela mas não define `hospedagem`; os itens `f-*` pertencem a CC-SUPORTE-N2, ausente da tabela inteira.
**Decisão:** a tabela do centro de custo é um *override* categoria a categoria sobre o padrão, não uma substituição integral — uma categoria ausente dentro de um centro de custo presente herda o limite padrão daquela categoria.
**Justificativa:** CC-ENG-PLATAFORMA precisou declarar `hospedagem` com limite R$ 0,00 explicitamente para bloqueá-la; se a simples omissão já bloqueasse a categoria, essa linha seria redundante — a tabela só faz sentido como um merge campo a campo.
**Regra afetada:** RN-012

### AMB-014 — limite R$ 0,00 é recusa ou glosa total?

**Texto original do RH:** "`CC-ENG-PLATAFORMA` não reembolsa `hospedagem` de forma alguma."
**Tipo:** unidade de aplicação
**O que não está claro:** um limite de R$ 0,00 devolve status `recusada` (como categoria fora da política) ou `parcial` com valor R$ 0,00 (como excedente de teto glosado)?
**Âncora nos dados do envelope:** CC-ENG-PLATAFORMA, `hospedagem: 0.00`; `d-010`.
**Decisão:** limite R$ 0,00 é tratado como recusa, status `recusada`.
**Justificativa:** "não reembolsa de forma alguma" é uma negação de cobertura, não um teto extremamente baixo — está semanticamente mais perto de "categoria fora da política" (RN-001) do que de "excedente glosado" (RN-007).
**Regra afetada:** RN-012

### AMB-015 — hospedagem não reembolsável ainda caracteriza viagem?

**Texto original do RH:** silente — decorre da interação entre o bloco A e a RN-009 já existente.
**Tipo:** interação entre regras
**O que não está claro:** se a hospedagem tem limite R$ 0,00 num centro de custo, o lançamento ainda conta como indício de viagem para ampliar os outros tetos da mesma data?
**Âncora nos dados do envelope:** CC-ENG-PLATAFORMA — hospedagem sempre recusada; se ela deixasse de indicar viagem, nenhuma data desse arquivo ampliaria teto (`d-010`, `e-007`).
**Decisão:** sim — o indício de viagem é o pernoite (a existência do lançamento), não o valor efetivamente pago por ele. Hospedagem recusada por limite R$ 0,00 continua caracterizando viagem, do mesmo modo que hospedagem recusada por falta de nota fiscal já caracterizava viagem na leitura original da RN-009 (AMB-006).
**Justificativa:** é a mesma leitura já registrada em AMB-006, agora exercitada por um caminho de recusa diferente — o RH nunca disse que só hospedagem efetivamente paga conta como pernoite.
**Regra afetada:** RN-009

### AMB-016 — o campo `periodicidade` reabre a discussão de "por dia" (AMB-001)?

**Texto original do RH:** ausente no comunicado; aparece como campo `periodicidade` (`"dia"` ou `"diaria"`) na tabela de política.
**Tipo:** unidade de aplicação
**O que não está claro:** o campo poderia sugerir que o teto passa a ser aplicado sobre a soma das despesas do dia, e não mais por despesa isolada.
**Âncora nos dados do envelope:** `e-002` e `e-003`, duas despesas de alimentação em dias diferentes; nenhuma no mesmo dia neste arquivo.
**Decisão:** não. Nada no comunicado do RH altera a unidade de aplicação já decidida em AMB-001 — o teto continua por despesa individual. `periodicidade` é informação descritiva da tabela (com que frequência o limite se renova), não uma instrução para agregar despesas do mesmo dia.
**Justificativa:** mudar uma decisão de negócio já tomada por causa de um campo novo, sem instrução explícita do RH, seria exatamente o tipo de inferência silenciosa que esta spec existe para evitar.
**Regra afetada:** nenhuma — mantém RN-007/AMB-001 como já estavam

### AMB-017 — `vigencia` da política é validada contra a data da despesa?

**Texto original do RH:** ausente no comunicado; aparece como campo `vigencia` na tabela de política.
**Tipo:** dado não usado
**O que não está claro:** se a política tem uma data de vigência e uma despesa é anterior a ela, o sistema deveria rejeitar essa despesa ou aplicar a tabela recebida mesmo assim?
**Âncora nos dados do envelope:** `vigencia: "2026-07-01"`; as despesas do exemplo oficial começam em 2026-07-03, dentro da vigência, mas nada garante isso em geral.
**Decisão:** não é validada. A política recebida em cada execução é tratada como a vigente para todas as despesas processadas naquela execução, independentemente da data de cada uma. `vigencia` é apenas repassada ao resultado, para auditoria.
**Justificativa:** o sistema não guarda histórico de políticas anteriores (fora de escopo, §3) — não há com o que comparar a data de vigência a não ser a própria tabela recebida nesta execução.
**Regra afetada:** nenhuma regra de cálculo; §4 (saída)

### AMB-018 — taxa "da data da despesa" quando a data não tem cotação publicada

**Texto original do RH:** "A conversão usa a taxa da data da despesa."
**Tipo:** dado ausente / fronteira
**O que não está claro:** cotações só existem em dias úteis bancários; uma despesa lançada num sábado, domingo ou feriado não tem taxa exatamente daquela data.
**Âncora nos dados do envelope:** `e-004`, lançada num sábado (18/07), sem cotação publicada nesse dia.
**Decisão:** usa-se a cotação de fechamento da última data anterior que tenha aquela moeda publicada. Se não existir nenhuma cotação anterior, a despesa é recusada.
**Justificativa:** é a mesma convenção que o próprio mercado financeiro usa para fim de semana e feriado (a cotação de sexta-feira vale para o fim de semana seguinte) — não é invenção do sistema, é a leitura padrão de "taxa da data" quando a data não teve pregão.
**Regra afetada:** RN-011

### AMB-019 — moeda inteiramente ausente da tabela de câmbio

**Texto original do RH:** silente.
**Tipo:** dado ausente
**O que não está claro:** a tabela de câmbio não necessariamente cobre toda moeda ISO 4217 possível; uma despesa numa moeda sem nenhuma entrada na tabela não tem como ser convertida em nenhuma data.
**Âncora nos dados do envelope:** `e-006`, em libra esterlina (GBP), moeda que não aparece em nenhuma data da tabela de câmbio.
**Decisão:** a despesa é recusada, com valor reembolsável R$ 0,00, preservando `valor_origem` e `moeda` no resultado.
**Justificativa:** sem taxa não há como converter para reais, e a política só define limites em reais — inventar uma taxa ou ignorar o limite quebraria a auditabilidade do resultado.
**Regra afetada:** RN-011

### AMB-020 — arredondamento do valor convertido: quantas casas e em que momento

**Texto original do RH:** silente.
**Tipo:** fronteira
**O que não está claro:** a conversão (valor de origem × taxa) produz um número com muitas casas decimais; falta decidir quando e quantas vezes arredondar, e se a própria taxa é arredondada antes de multiplicar.
**Âncora nos dados do envelope:** `e-003`, 14,50 EUR × 5,88 = 85,26 exato — mas nem toda combinação fecha em duas casas.
**Decisão:** o valor convertido é arredondado para duas casas decimais, meio para cima, uma única vez, imediatamente após a multiplicação pela taxa. A taxa de câmbio em si não é arredondada antes de multiplicar.
**Justificativa:** preserva, para despesas convertidas, o mesmo invariante que a RN-010 original já garantia para despesas em reais — um único arredondamento, para que item e total nunca discordem entre si.
**Regra afetada:** RN-010, RN-011

### AMB-021 — o piso de nota fiscal é comparado em reais ou na moeda de origem?

**Texto original do RH:** o piso é declarado em reais ("Nota fiscal é obrigatória acima de R$ 100").
**Tipo:** fronteira
**O que não está claro:** uma despesa de 40 USD (equivalente a R$ 220,00) está acima ou abaixo do piso? O número de origem (40) é menor que 100; o valor convertido (220,00) é maior.
**Âncora nos dados do envelope:** `e-005`, 40,00 USD sem nota fiscal, equivalente a R$ 220,00.
**Decisão:** o piso é comparado ao valor já convertido em reais.
**Justificativa:** o piso é declarado em reais na política; comparar ao número de origem trataria 40 dólares e 40 reais como equivalentes, o que não é o que o RH quis dizer.
**Regra afetada:** RN-006

### AMB-022 — a chave de duplicata inclui a moeda?

**Texto original do RH:** decorrente de "Duplicatas devem ser tratadas" (v3), agora em contato com moeda estrangeira.
**Tipo:** unidade de aplicação
**O que não está claro:** dois lançamentos com o mesmo valor numérico, mesma data, categoria, fornecedor e descrição, mas em moedas diferentes, são a mesma despesa lançada duas vezes?
**Âncora:** nenhuma nos dados do envelope; risco identificado pela extensão da RN-004 já existente ao cenário internacional.
**Decisão:** a moeda de origem entra na chave de duplicata. Valores numericamente iguais em moedas diferentes não são duplicata.
**Justificativa:** 100 BRL e 100 USD não são o mesmo gasto — são gastos de magnitudes muito diferentes que coincidem só no número escrito; ignorar a moeda na comparação recusaria um lançamento legítimo.
**Regra afetada:** RN-004

### AMB-023 — como um item não convertível entra num total que é sempre em reais?

**Texto original do RH:** silente.
**Tipo:** dado ausente / consistência de agregados
**O que não está claro:** uma despesa recusada por falta de cotação (RN-011) tem valor de origem em moeda estrangeira, mas nenhum valor em reais — o que ela contribui para `total_lancado`, que é sempre em reais?
**Âncora nos dados do envelope:** `e-006`, em GBP, sem cotação.
**Decisão:** contribui com R$ 0,00 para `total_lancado`. O valor de origem permanece visível no item (`valor_origem`, `moeda`), mas não entra em nenhum total agregado em reais.
**Justificativa:** somar um valor em moeda estrangeira a um total em reais produziria um número sem significado; R$ 0,00 preserva o invariante de que todo total é uma soma de valores em reais, ao custo de subestimar o total lançado — o custo é registrado como item em aberto (§10), não escondido.
**Regra afetada:** RN-011 · §4 (saída)

### AMB-024 — a fronteira de R$ 500,00 e o que "pendente" significa

**Texto original do RH:** "Itens cujo valor reembolsável passe de R$ 500 não são mais aprovados automaticamente [...] entram em estado de pendência aguardando aprovação do gestor."
**Tipo:** fronteira / unidade de aplicação
**O que não está claro:** "passe de R$ 500" inclui o próprio R$ 500,00? O estado de pendência substitui o status de cálculo (aprovada/parcial/recusada/estorno) ou convive com ele? O valor pendente já entra em `total_reembolsavel` antes da aprovação do gestor?
**Âncora nos dados do envelope:** `e-007`, valor reembolsável R$ 600,00.
**Decisão:** "passe de" é estrito — exatamente R$ 500,00 não fica pendente. O estado é um campo adicional, ortogonal ao status; não o substitui. O valor pendente já entra em `total_reembolsavel`, porque o sistema calcula quanto é reembolsável, não se o pagamento já foi liberado — a pendência é sobre o fluxo de aprovação, não sobre o cálculo. Estorno nunca fica pendente, porque reduz o total pago, não aumenta.
**Justificativa:** mesma leitura estrita de fronteira já usada em AMB-003 para "acima de R$ 100"; manter estado e status separados evita que um item opcional force uma reescrita do vocabulário de status já estabelecido na v3.
**Regra afetada:** RN-013

---

## 7. Casos de borda

| Caso | Entrada | Comportamento esperado | Regra |
|---|---|---|---|
| Valor exatamente no piso da nota | R$ 100,00, sem nota | Não exige nota; segue para o teto | RN-006 |
| Um centavo acima do piso | R$ 100,01, sem nota | Recusada, R$ 0,00 | RN-006 |
| Valor exatamente no teto | Alimentação no valor do teto do centro de custo | Aprovada integralmente, sem glosa | RN-007 |
| Um centavo acima do teto | Alimentação um centavo acima do teto | Parcial, glosa de R$ 0,01 | RN-007 |
| Duas despesas mesmo dia e categoria | Duas despesas de alimentação no mesmo dia | Teto não é compartilhado; cada uma julgada isoladamente | RN-007 |
| Duplicata exata | Duas despesas iguais, tudo igual | Primeira paga, segunda recusada | RN-004 |
| Mesmo valor, fornecedor diferente | Mesmo valor em dois lugares | Ambas processadas; não é duplicata | RN-004 |
| Duplicata com moedas diferentes | Mesmo valor numérico, data/categoria/fornecedor/descrição iguais, moedas diferentes | Não é duplicata; ambas processadas | RN-004 |
| Fora da competência | Data fora do mês de `periodo.competencia` | Recusada, presente no resultado | RN-003 |
| Categoria fora da política | Categoria ausente de toda tabela aplicável | Recusada, presente no resultado | RN-001 |
| Categoria em caixa alta | Categoria com grafia diferente | Normalizada, concorre ao teto | RN-002 |
| Estorno | Valor negativo | Abate integral, sem teto e sem nota | RN-005 |
| Estorno acima do teto em módulo | Estorno cujo módulo excede o teto da categoria | Abate o valor integral; teto não se aplica | RN-005 |
| Terceira casa decimal | Valor com três casas decimais | Tratado com duas casas em tudo | RN-010 |
| Hospedagem de várias noites | Hospedagem descrita com mais de uma diária | Uma diária; teto sobre o valor todo | RN-008 |
| Hospedagem sem nota acima do piso | Hospedagem sem nota, acima do piso | Recusada antes de chegar ao teto | RN-006 |
| Data com hospedagem | Outra categoria lançada na mesma data de uma hospedagem | Teto ampliado pelo percentual de viagem | RN-009 |
| Hospedagem recusada na data | Hospedagem recusada (sem nota ou limite R$ 0,00) + outra despesa na mesma data | A data segue sendo viagem | RN-009 |
| Centro de custo ausente da tabela de política | Colaborador em centro de custo não listado | Usa a tabela padrão inteira | RN-012 |
| Categoria ausente só dentro de um centro de custo presente | Centro de custo na tabela, sem essa categoria | Herda o limite padrão da categoria | RN-012 |
| Limite de categoria igual a R$ 0,00 | Categoria com limite zero no centro de custo | Recusada, R$ 0,00 — não é glosa parcial | RN-012 |
| Categoria que só existe na tabela de um centro de custo | Categoria nova presente só num centro de custo | Recusada nos demais, como categoria não coberta | RN-001, RN-012 |
| Moeda ausente no lançamento | Despesa sem o campo `moeda` | Assume-se `BRL` | RN-011 |
| Data sem cotação publicada (fim de semana) | Despesa em moeda estrangeira lançada num sábado | Usa a cotação de fechamento da última data anterior disponível | RN-011 |
| Moeda sem nenhuma cotação na tabela | Despesa em moeda ausente de toda a tabela de câmbio | Recusada, R$ 0,00, valor e moeda de origem preservados | RN-011 |
| Piso de nota fiscal sobre valor convertido | Despesa estrangeira sem nota, equivalente acima do piso em reais | Recusada — piso comparado ao valor em reais, não ao de origem | RN-006, RN-011 |
| Valor reembolsável exatamente R$ 500,00 | Item aprovado em exatamente R$ 500,00 | Estado `aprovacao_automatica` | RN-013 |
| Um centavo acima de R$ 500,00 | Item aprovado em R$ 500,01 | Estado `pendente_aprovacao` | RN-013 |
| Lista de despesas vazia | `despesas: []` | Resultado válido, todos os totais em `0.00` | — |

## 8. Ordem de aplicação das regras

A ordem muda o resultado. Cada despesa percorre os passos abaixo e **para no
primeiro que a recusar**, exceto o último, que é aplicado depois da decisão e
nunca recusa.

```
1. Arredondamento na leitura                            RN-010
2. Normalização da categoria                            RN-002   (transformação)
3. Competência                                          RN-003
4. Categoria coberta pela tabela do centro de custo     RN-001, RN-012
5. Duplicata (chave inclui moeda)                       RN-004
6. Conversão cambial                                    RN-011   (transformação; pode recusar)
7. Estorno                                              RN-005
8. Nota fiscal (sobre o valor já convertido em reais)   RN-006
9. Teto do centro de custo, com ampliação de viagem     RN-007, RN-008, RN-009, RN-012
10. Fila de aprovação (opcional, após a decisão)        RN-013   (não recusa, não altera o valor)
```

O passo 9 é o único que pode produzir reembolso parcial. Os passos 3 a 8
produzem apenas aprovação integral ou recusa integral. O passo 10 nunca
recusa: apenas anota um estado adicional sobre uma decisão já tomada.

A condição de viagem (RN-009) é determinada antes do passo 1, sobre a lista
de despesas como veio na entrada — pela categoria do lançamento, não pelo seu
valor convertido — e não é afetada por recusas ocorridas nos passos 3 a 8
(AMB-015).

## 9. Critérios de aceite

O sistema está pronto quando:

- [x] Processa `exemplos/despesas-exemplo.json` (centro de custo
      CC-ENG-PLATAFORMA) e produz total reembolsável de **R$ 341,93** sobre
      total lançado de **R$ 1.816,84** (D-002 em `DECISIONS.md` explica por
      que este número mudou em relação à versão 1.1 da spec sem que a lógica
      de cálculo tenha mudado).
- [x] `d-001` (R$ 72,50) é reembolsada integralmente — o teto de alimentação
      deste centro de custo é R$ 75,00.
- [x] `d-003` (R$ 100,00 sem nota) é reembolsada em R$ 80,00 e `d-004`
      (R$ 100,01 sem nota) em R$ 0,00.
- [x] `d-006` é reembolsada em R$ 54,90 e `d-007`, sua duplicata, em R$ 0,00.
- [x] `d-010` (hospedagem, R$ 480,00) é recusada em R$ 0,00 — este centro de
      custo não reembolsa hospedagem.
- [x] `d-011` aparece como R$ 33,33 e não como R$ 33,333.
- [x] `d-014` é reconhecida como alimentação apesar da caixa alta e
      reembolsada integralmente, pelo mesmo teto de `d-001`.
- [x] Processa `exemplos/envelope/despesas-envelope.json` (centro de custo
      CC-COMERCIAL, despesas em moeda estrangeira) e produz total
      reembolsável de **R$ 1.343,26** sobre total lançado de **R$ 2.457,52**.
      Nele: a despesa lançada num sábado sem cotação publicada é convertida
      pela última cotação anterior disponível; a despesa em moeda ausente da
      tabela de câmbio é recusada com o valor de origem preservado; a
      despesa de hospedagem, acima de R$ 500,00 reembolsáveis, recebe estado
      `pendente_aprovacao`.
- [x] Processa `exemplos/envelope/despesas-envelope-cc-desconhecido.json`
      (centro de custo ausente da tabela de política) e produz total
      reembolsável de **R$ 433,76** sobre total lançado de **R$ 623,76**,
      usando a tabela padrão inteira e recusando a categoria que só existe
      na tabela de outro centro de custo.
- [x] A soma dos `valor_reembolsavel` dos itens é igual a
      `resumo.total_reembolsavel`, nos três arquivos acima.
- [x] Toda regra de RN-001 a RN-013 tem ao menos um caso de teste que a exercita.
- [x] Entrada com campo obrigatório ausente, na despesa ou nos documentos de
      política e câmbio, é rejeitada com mensagem, sem produzir resultado parcial.

## 10. O que fica em aberto

- **Viagem é inferida, não declarada.** A regra atual não reconhece viagem sem pernoite, e trata como viagem um dia em que houve hospedagem lançada por outro motivo. A correção certa é um campo explícito na entrada; enquanto ele não existe, a inferência da RN-009 é a decisão provisória.
- **Hospedagem de várias noites é penalizada.** Pela RN-008, uma hospedagem de múltiplas diárias é glosada mesmo quando o valor por noite está dentro da política. Isso é consequência aceita de não interpretar texto livre; um campo `diarias` na entrada resolveria.
- **Duplicata legítima é indistinguível de erro.** Dois lançamentos iguais no mesmo lugar e no mesmo dia existem na vida real, e a RN-004 os recusa. Não há campo na entrada — hora, número de nota — que permita separar os dois casos.
- **Fim de semana não é tratado como conceito de negócio, só como fronteira de câmbio.** A política não distingue dia útil de fim de semana para nenhuma regra além da RN-011; a convenção de "última cotação anterior" (AMB-018) é decisão nossa diante da lacuna de cotação, não algo que o RH pediu.
- **`vigencia` da política não é validada.** O sistema aplica a tabela recebida a toda despesa da execução, mesmo que anterior à data de vigência declarada (AMB-017) — não há histórico de políticas para comparar.
- **Item não convertível subestima `total_lancado`.** Uma despesa recusada por falta de cotação de câmbio contribui R$ 0,00 ao total lançado, mesmo tendo um valor de origem diferente de zero (AMB-023) — o total deixa de refletir o volume bruto de gastos declarados quando há moeda sem cotação.
- **A fila de aprovação (RN-013) não persiste estado entre execuções.** Rodar o sistema duas vezes sobre a mesma entrada sempre marca os mesmos itens como pendentes; não há registro de que um gestor já aprovou um item pendente numa execução anterior — está fora de escopo (§3), consistente com o sistema não guardar histórico.
