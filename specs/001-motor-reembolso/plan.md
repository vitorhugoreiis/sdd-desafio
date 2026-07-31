# Plano Técnico — Motor de Cálculo de Reembolso

**Versão:** 1.1 · **Baseado na spec:** 1.2

> Aqui mora o COMO. Este arquivo pode e deve falar de linguagem, biblioteca e
> arquitetura. O que ele **não** pode é introduzir regra de negócio nova — se
> apareceu uma, ela pertence à `spec.md`.

---

## 1. Stack

| Escolha | O quê | Por quê | O que descartei e por quê |
|---|---|---|---|
| Linguagem | Python 3.11+ | Domínio maior; `decimal` e `json` na biblioteca padrão cobrem todo o problema | Go — compilaria num binário só, mas o ganho não paga a menor fluência sob prazo de 2 dias |
| Testes | `pytest` | Parametrização (`@pytest.mark.parametrize`) mapeia direto na tabela de casos de borda da spec §7 | `unittest` — verboso demais para uma tabela de dezenas de casos |
| Parsing/validação | `json` da stdlib + validação manual explícita | Zero dependência; a spec exige rejeitar entrada inválida com mensagem, e um validador escrito à mão diz exatamente qual campo faltou | `pydantic` — resolveria a validação, mas adiciona dependência e esconde a mensagem de erro atrás de um formato que eu não controlo |
| Aritmética monetária | `decimal.Decimal`, com `json.load(parse_float=Decimal)` | Único jeito de `33.333` da entrada nunca virar binário flutuante; RN-010 exige arredondamento controlado (`ROUND_HALF_UP`), inclusive após a conversão cambial | `float` — quebraria a RN-010 de forma silenciosa · centavos em `int` — correto, mas obrigaria a converter na fronteira e a spec fala em reais |
| CLI | `argparse` da stdlib | O contrato original é um subcomando e duas flags; a v1.1 adiciona duas flags opcionais (política, câmbio) com default resolvido a partir da raiz do pacote — não justifica trocar de biblioteca | `typer`/`click` — ergonomia melhor, irrelevante para uma CLI de um comando |

## 2. Arquitetura

```
arquivos JSON de entrada (despesas · política · câmbio)
   ↓  carregador            (I/O)   lê despesas, valida presença de campos, converte para Decimal
   ↓  carregador_politica   (I/O)   lê a tabela de limites por centro de custo
   ↓  carregador_cambio     (I/O)   lê a tabela de taxas de câmbio
   ↓  Solicitacao, Politica, TabelaCambio     estruturas imutáveis
   ↓  motor                  (puro)  monta o Contexto (viagem + política + câmbio); aplica os 10 passos da spec §8
   ↓  Resultado                      lista de pareceres + resumo
   ↓  serializador          (I/O)   formata Decimal como texto de 2 casas, escreve JSON
arquivo JSON de saída
```

**Fronteiras.** O `motor` continua sem conhecer arquivo, `argparse`, `json`
nem caminho de disco: recebe uma `Solicitacao`, uma `Politica` e uma
`TabelaCambio` já montadas, e devolve um `Resultado`. Toda a I/O vive nos
carregadores, no serializador e na CLI (DT-003, inalterada pelo envelope).

```
src/
  cli.py                       argparse, orquestra carregadores → motor → serializador
  io/carregador.py             arquivo de despesas → Solicitacao (+ erros de validação)
  io/carregador_politica.py    arquivo de política → Politica (DT-008)
  io/carregador_cambio.py      arquivo de câmbio → TabelaCambio (DT-008)
  io/serializador.py           Resultado → arquivo
  motor/modelo.py              Despesa, Solicitacao, Contexto, Parecer, Resultado, Status, Estado
  motor/politica.py            Politica, LimiteCategoria — consulta de limite por centro de custo (§4, DT-008)
  motor/cambio.py              TabelaCambio — consulta de taxa por moeda e data, com retrocesso (DT-008)
  motor/regras.py              uma função por RN, na ordem da spec §8
  motor/calculadora.py         percorre as despesas, monta o Resultado
tests/
```

## 3. Modelo de dados

Todas as estruturas são `@dataclass(frozen=True)` — nenhuma regra muda uma
despesa no lugar; cada passo devolve um valor novo.

| Estrutura | Campos | Observação |
|---|---|---|
| `Despesa` | `id, data (date), categoria (str normalizada), descricao, fornecedor, valor (Decimal, sempre em reais), tem_nota_fiscal (bool), moeda (str ISO 4217), valor_origem (Decimal), taxa_cambio (Decimal \| None), data_taxa (date \| None)` | `valor` é sempre o valor em reais, já arredondado; para lançamentos em moeda estrangeira, começa igual a `valor_origem` e é substituído pelo valor convertido no passo 6 (RN-011). `taxa_cambio`/`data_taxa` só são preenchidos quando há conversão |
| `Solicitacao` | `colaborador (dict), competencia (str), inicio, fim, despesas (tuple[Despesa])` | Imutável; ordem da entrada preservada, que é o que a RN-004 usa para eleger a primeira ocorrência |
| `Politica` | `padrao (dict[str, LimiteCategoria]), centros_custo (dict[str, dict[str, LimiteCategoria]]), piso_nota_fiscal (Decimal), fator_viagem (Decimal), versao (str), vigencia (date)` | `limite(centro_custo, categoria) -> Decimal \| None` faz o merge padrão+override da RN-012; `None` = categoria não coberta em lugar nenhum, distinto de limite `Decimal("0.00")` (AMB-014) |
| `LimiteCategoria` | `valor (Decimal)` | Estrutura mínima — existe só para deixar o `None` (categoria ausente) e o zero (categoria bloqueada) visivelmente diferentes no tipo, não só no valor |
| `TabelaCambio` | consulta indexada por data e moeda | `taxa(moeda, data) -> tuple[Decimal, date] \| None`, retrocedendo para a última data anterior que tenha aquela moeda (RN-011, AMB-018); `None` = sem cotação em nenhuma data anterior, ou moeda ausente da tabela (AMB-019) |
| `Contexto` | `competencia, datas_em_viagem (frozenset[date]), centro_custo (str), politica (Politica), tabela_cambio (TabelaCambio)` | Ganhou três campos sem mudar a assinatura de nenhuma regra — a aposta de DT-004 do Dia 1 paga o dividendo aqui |
| `Parecer` | `despesa, valor_reembolsavel (Decimal), status (Status), estado (Estado), regras_aplicadas (tuple[str]), justificativa (str)` | `estado` (RN-013, opcional) é ortogonal a `status`; `valor_glosado` continua derivado, não armazenado |
| `Status` | enum: `APROVADA, PARCIAL, RECUSADA, ESTORNO` | Inalterado; serializado em minúsculas |
| `Estado` | enum: `APROVACAO_AUTOMATICA, PENDENTE_APROVACAO` | Novo (RN-013, opcional); serializado em minúsculas, como `Status` |
| `Resultado` | `solicitacao, politica_aplicada (dict com versao/vigencia/centro_custo_aplicado/origem_dos_limites), pareceres (tuple[Parecer])` | Os totais do resumo continuam propriedades calculadas, nunca campos — não há como divergirem dos itens |

`regras_aplicadas` continua carregando os IDs `RN-00X` literais — é o que
fecha a rastreabilidade da spec até a saída em execução.

## 4. Como a política e o câmbio são representados

A política deixa de ser um módulo de constantes e passa a ser uma estrutura
de dados carregada de um documento externo em tempo de execução (DT-008).
`motor/politica.py` continua puro: define `Politica` e `LimiteCategoria`
como `@dataclass(frozen=True)` e a função de consulta `limite(centro_custo,
categoria)`, que faz o merge padrão+override descrito em RN-012 — mas não
sabe ler arquivo. Quem lê o documento e monta a `Politica` é
`io/carregador_politica.py`, na fronteira de I/O, do mesmo jeito que
`io/carregador.py` já faz para as despesas. O câmbio segue o padrão idêntico:
`motor/cambio.py` define `TabelaCambio` e a consulta com retrocesso de data;
`io/carregador_cambio.py` lê o documento.

**Decisão:** módulo consultável, carregado de fora, não constantes de
código. Mudar um limite ou publicar uma cotação nova passa a ser editar o
documento externo entre execuções, sem tocar em código nem reimplantar nada
— exatamente o requisito do bloco A do envelope.

**Alternativa descartada:** manter constantes e acrescentar um `if
centro_custo == "X"` por centro de custo conhecido — inviável já no segundo
centro de custo novo que chegasse, e o próprio comunicado do RH avisa que a
tabela "muda sem aviso".

**Consequência:** os testes de regra que dependem de limite ou de taxa
(RN-001, RN-006, RN-007, RN-009, RN-011, RN-012) passam a montar uma
`Politica` e/ou uma `TabelaCambio` de teste (fábricas em `tests/fabricas.py`)
em vez de importar uma constante de módulo — o mesmo padrão que DT-001 já
tinha estabelecido para `Despesa`.

## 5. Decisões técnicas

### DT-001 — `Decimal` desde a leitura do arquivo

**Contexto:** `d-011` vale `33.333` no JSON. Lido como `float`, vira
`33.332999999999998` e a RN-010 passa a depender de sorte de arredondamento.
**Decisão:** `json.load(f, parse_float=Decimal)`, e arredondamento único com
`quantize(Decimal("0.01"), ROUND_HALF_UP)` na construção da `Despesa`.
**Alternativa descartada:** converter para `Decimal` depois de já ter passado por
`float` — inútil, a precisão já se perdeu no parse.
**Consequência:** torna impossível o bug mais previsível do projeto; obriga a
converter para `str` na serialização, porque `Decimal` não é serializável por
padrão.

### DT-002 — Uma função pura por regra de negócio

**Contexto:** a spec §8 define dez passos com parada no primeiro que recusa.
**Decisão:** cada RN é uma função `(Despesa, Contexto) -> Parecer | Despesa |
None` (ver DT-007), onde `None` significa "não decidi, siga para a próxima".
A calculadora percorre a lista de regras na ordem da spec.
**Alternativa descartada:** um `if/elif` aninhado dentro de uma função grande —
funcionaria, mas a ordem da spec §8 ficaria implícita na indentação em vez de
declarada numa lista legível.
**Consequência:** mudar a ordem das regras vira reordenar uma lista; adicionar
regra vira acrescentar uma função. Foi a aposta explícita deste plano para o
envelope do Dia 2, e o envelope confirmou a aposta — ver DT-007.

### DT-003 — Núcleo sem I/O

**Contexto:** critério de aceite da spec exige verificar toda regra de RN-001 a RN-013.
**Decisão:** `motor/` não importa `json`, `argparse`, `pathlib` nem `open` —
regra que se estende aos dois módulos novos, `motor/politica.py` e
`motor/cambio.py`.
**Alternativa descartada:** motor que recebe caminho de arquivo — mais curto de
escrever, mas cada teste de regra viraria um teste de disco.
**Consequência:** os testes de regra rodam em memória; o custo é uma camada de
tradução a mais entre o arquivo e o modelo, agora paga três vezes (despesas,
política, câmbio) em vez de uma.

### DT-004 — Viagem calculada uma vez, antes do laço

**Contexto:** a RN-009 diz que a condição de viagem é determinada sobre a
lista de entrada e não é afetada por recusas — inclusive recusas por limite
zero, a partir da v4 (AMB-015).
**Decisão:** varrer as despesas uma vez, montar `frozenset` das datas com
hospedagem, guardar no `Contexto`.
**Alternativa descartada:** consultar as outras despesas de dentro da regra de
teto — criaria dependência entre itens no meio do laço e abriria a porta para a
ordem de processamento mudar o resultado.
**Consequência:** o resultado de cada despesa passa a depender só dela e do
`Contexto`, o que é o que torna o motor testável item a item — e o que
permitiu o `Contexto` crescer (política, câmbio) sem essa garantia quebrar.

### DT-005 — Sem dependência externa em produção

**Contexto:** `pytest` é a única dependência, e só de desenvolvimento.
**Decisão:** stdlib para tudo em `src/`.
**Alternativa descartada:** `pydantic` para validação de entrada.
**Consequência:** `python -m src.cli` roda em qualquer Python 3.11+ sem instalar
nada; em troca, a validação de entrada é código escrito à mão que precisa de
teste próprio — agora para três documentos de entrada, não um.

### DT-006 — Nome de teste carrega o ID da regra

**Contexto:** o critério de rastreabilidade da rúbrica pede chegar da spec ao
teste sem adivinhar.
**Decisão:** arquivos `tests/test_rn_007_tetos.py`, funções
`test_rn_007_despesa_acima_do_teto_e_reembolsada_pelo_teto`.
**Alternativa descartada:** nomes descritivos sem o ID — legíveis, mas exigiriam
um índice à parte para amarrar na spec.
**Consequência:** `pytest -k rn_007` roda exatamente os testes de uma regra, e a
matriz de cobertura do `tasks.md` se preenche por leitura direta.

### DT-007 — Passo do pipeline passa a devolver `Parecer | Despesa | None`

**Contexto:** a spec §8 agora tem dez passos, e o passo 6 (RN-011, conversão
cambial) precisa fazer duas coisas que nenhuma regra anterior fazia:
transformar a despesa (substituir o valor de origem pelo valor convertido em
reais) e, em alguns casos, recusar (moeda sem cotação, AMB-019). A
assinatura de DT-002, `(Despesa, Contexto) -> Parecer | None`, só comporta
"decidi" ou "não decidi" — não "transformei e sigo".
**Decisão:** a assinatura de um passo do pipeline passa a ser `(Despesa,
Contexto) -> Parecer | Despesa | None`. `None` continua "não decidi, siga
para a próxima"; `Parecer` continua "decidi, pare"; `Despesa` é o caso novo —
"transformei, continue com esta despesa a partir daqui". A calculadora troca
a despesa corrente pela devolvida sempre que o passo devolve uma `Despesa`.
Ganho colateral: `normalizar_categoria` (RN-002), que na v1.0 era chamada à
parte antes do laço de regras, vira a entrada nº 2 da mesma lista declarada
— ela sempre devolveu uma `Despesa` nova, só nunca tinha sido tratada como
parte da lista.
**Alternativa descartada:** dois laços separados, um para as regras antes da
conversão e outro para depois — resolveria sem mudar a assinatura, mas
quebraria exatamente o que DT-002 existe para garantir: a ordem da spec §8
declarada numa lista só, legível de cima a baixo. Também cogitado: a
conversão viver fora da lista, chamada explicitamente entre os passos 5 e 7
— mesmo problema, ordem implícita em vez de declarada.
**Consequência:** é o único ponto da arquitetura do Dia 1 que resistiu à
mudança de requisito sem absorver de graça — toda regra de decisão, antiga
ou nova, continua devolvendo `Parecer | None`; só o passo de conversão usa o
terceiro caso.

### DT-008 — Política e câmbio entram no `Contexto`, carregados na fronteira de I/O

**Contexto:** RN-012 (limites por centro de custo) e RN-011 (conversão
cambial) precisam consultar, respectivamente, a tabela de política e a
tabela de câmbio — dois documentos que só existem fora do motor.
**Decisão:** `motor/politica.py` e `motor/cambio.py` continuam módulos
puros: definem as estruturas (`Politica`, `LimiteCategoria`, `TabelaCambio`)
e a lógica de consulta (merge padrão+override; retrocesso de data), mas não
sabem ler arquivo. Quem lê os documentos e monta essas estruturas é
`io/carregador_politica.py` e `io/carregador_cambio.py`, seguindo o mesmo
padrão de `io/carregador.py`. O resultado de ambos entra no `Contexto`, ao
lado de `datas_em_viagem` — DT-004 do Dia 1 previu um `Contexto` montado uma
vez antes do laço exatamente para acomodar dado auxiliar sem tocar na
assinatura das regras.
**Alternativa descartada:** o motor lendo o JSON de política e câmbio
diretamente — mais direto de escrever, mas mataria DT-003 (núcleo sem I/O) e
transformaria todo teste de RN-011/RN-012 num teste de disco, exatamente o
problema que DT-003 já resolveu uma vez para despesas.
**Consequência:** o `Contexto` cresce de dois para cinco campos, mas nenhuma
função de regra muda de assinatura — o custo da mudança cai inteiro em
`calculadora.py` (que monta o `Contexto`) e nos dois carregadores novos, não
nas regras.

## 6. Estratégia de testes

- **Nível.** Maioria unitária sobre o motor puro (uma função de regra por vez);
  um punhado de testes de integração nos carregadores e no serializador; três
  testes ponta a ponta que rodam a CLI — um por arquivo de aceite da spec §9
  (`exemplos/despesas-exemplo.json` e os dois arquivos de
  `exemplos/envelope/`), cada um conferindo o total e os itens-chave que a
  spec cita.
- **Cada `RN-NNN` tem teste?** Sim, por construção: a task de cada RN só fecha com
  o teste de nome correspondente passando, e a tabela de cobertura no fim do
  `tasks.md` é preenchida ao encerrar cada fase.
- **Casos de borda da spec §7.** A tabela de casos vira um
  `@pytest.mark.parametrize` em `tests/test_casos_de_borda.py`, uma linha por
  caso, com o ID da regra no `id` do parâmetro — inclusive as linhas novas da
  v1.2 (limite zero, CC desconhecido, moeda sem cotação, fronteira de R$ 500).
- **Fronteiras têm teste dos dois lados.** Onde a spec fixa um limite, existem
  dois casos: no valor exato e um centavo acima — incluindo a fronteira nova
  de R$ 500,00/R$ 500,01 da RN-013.
- **Fábricas novas.** `tests/fabricas.py` ganha `politica()` (padrão e
  overrides por centro de custo configuráveis) e `tabela_cambio()` (taxas
  configuráveis por data e moeda), no mesmo espírito da fábrica `despesa()`
  já existente (DT-001) — os testes de RN-011/012/013 montam `Contexto` a
  partir dessas fábricas em vez de repetir literais de política e câmbio em
  cada teste.
- **Nomenclatura.** `test_rn_00X_<comportamento>` — ver DT-006.

## 7. Riscos

| Risco | Probabilidade | O que faço se acontecer |
|---|---|---|
| Limites passam a variar por perfil, centro de custo ou data de vigência | Média (avaliada no Dia 1) | **Aconteceu — ver D-002.** A mitigação prevista (política isolada num módulo próprio, §4) funcionou sem precisar de retrabalho: virou tabela consultável carregada de fora, sem tocar nas regras. |
| O envelope introduz campo novo na entrada (`moeda`) | Alta (avaliada no Dia 1, sobre `em_viagem`/`diarias`) | **Aconteceu de forma parecida, mas não idêntica — ver D-003.** O campo novo foi `moeda`, não os campos de viagem/diárias previstos; o carregador ganhou campo opcional como esperado, mas a conversão exigiu DT-007, não prevista no Dia 1. |
| O envelope muda a unidade de aplicação do teto (AMB-001, de "por despesa" para "por dia") | Alta (avaliada no Dia 1) | **Não se materializou nesta forma.** O campo `periodicidade` da política nova tentou sugerir isso; a decisão (AMB-016) manteve o teto por despesa, por falta de instrução explícita do RH para mudar uma decisão de negócio já tomada. |
| Um passo do pipeline precisa transformar a despesa **e** poder recusar, e a assinatura das regras não comporta os dois | Não avaliado no Dia 1 | **Aconteceu — ver DT-007.** Foi o único ponto de resistência real da arquitetura: resolvido ampliando o tipo de retorno do passo, sem quebrar a lista única de DT-002. |
| `Decimal` vazando para o `json.dump` e estourando `TypeError` | Média | Serializador converte explicitamente; teste ponta a ponta pega. Continua valendo para os campos novos (`valor_origem`, `taxa_cambio`). |
| Testes escritos depois do código, quebrando a ordem da rastreabilidade | Média | Cada task do `tasks.md` tem o teste como critério de aceite, e o commit `test(T-00X)` vem antes do `feat(T-00X)` — obrigatório sem exceção a partir de T-023. |
| Spec e código divergirem em silêncio ao absorver o envelope | Baixa | `DECISIONS.md` obrigatório antes de tocar em código; os três testes ponta a ponta travam os totais da spec §9 e falham se o comportamento mudar sem a spec mudar junto. |
