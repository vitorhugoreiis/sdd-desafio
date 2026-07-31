# Tasks — Motor de Cálculo de Reembolso

> Cada task é pequena o bastante para virar **um commit**. Se você não consegue
> descrever o critério de aceite como "o teste X passa", a task está grande demais.
>
> Marque `[x]` conforme conclui — ao longo do caminho, não tudo no fim. O histórico
> de quando cada task foi marcada é lido na correção.

**Formato do commit:** `feat(T-003): <descrição>` · `test(T-003): <descrição>`

**Derivado de:** `spec.md` 1.0 e `plan.md` 1.0. A ordem das tasks da Fase 2 segue
a ordem de aplicação da spec §8.

---

## Fase 1 — Fundação

- [x] **T-001** — Esqueleto do projeto: `src/`, `tests/`, `pyproject.toml` com `pytest` como dependência de desenvolvimento
  - **Atende:** nenhuma RN — habilita as demais
  - **Aceite:** `pytest` coleta e executa ao menos 1 teste, saída verde
  - **Commit:** `284bee9`

- [x] **T-002** — Modelo de dados imutável: `Despesa`, `Solicitacao`, `Contexto`, `Parecer`, `Resultado`, enum `Status`
  - **Atende:** `plan.md` §3
  - **Aceite:** `test_modelo_e_imutavel` — tentar atribuir a um campo de `Despesa` levanta `FrozenInstanceError`; `Resultado.total_reembolsavel` é propriedade calculada, não campo
  - **Commit:** `2ac9a6f`

- [x] **T-003** — Carregador: JSON → `Solicitacao`, com `parse_float=Decimal` e arredondamento único de duas casas meio-para-cima
  - **Atende:** RN-010, AMB-011, `spec.md` §4 (entrada)
  - **Aceite:** `test_rn_010_arredonda_na_leitura` — `33.333` vira exatamente `Decimal("33.33")`, e o valor nunca passa por `float`
  - **Commit:** `56ed38a`

- [x] **T-004** — Validação de entrada: campo obrigatório ausente ou tipo inválido rejeita a execução com mensagem nomeando o campo
  - **Atende:** `spec.md` §9 (último critério), §3 (não adivinha entrada malformada)
  - **Aceite:** `test_entrada_sem_campo_obrigatorio_e_rejeitada` — entrada sem `despesas[].valor` levanta erro citando `valor`, e nenhum resultado parcial é escrito
  - **Commit:** `b17f3c8`

- [x] **T-005** — Módulo de política: tetos por categoria, piso de nota fiscal e fator de viagem como constantes `Decimal`
  - **Atende:** `plan.md` §4
  - **Aceite:** `test_politica_expoe_limites_da_v3` — os quatro valores conferem com a spec §5 (60, 80, 250, 100) e são `Decimal`, não `float`
  - **Commit:** `3ad5782`

## Fase 2 — Regras de negócio

> Uma task por RN, na ordem dos passos da spec §8. Cada uma entra com o seu teste.

- [x] **T-006** — RN-002: normalização da categoria (caixa e espaços nas pontas)
  - **Atende:** RN-002, AMB-012
  - **Aceite:** `test_rn_002_categoria_em_caixa_alta_e_normalizada` — `"ALIMENTACAO"` é tratada como `alimentacao` e a categoria normalizada é a que sai no resultado
  - **Commit:** `3b56b0f`

- [x] **T-007** — RN-003: competência — despesa fora do mês é recusada e permanece no resultado
  - **Atende:** RN-003, AMB-009
  - **Aceite:** `test_rn_003_despesa_fora_da_competencia_e_recusada` — data `2026-04-15` com competência `2026-07` resulta em `0.00`, status `recusada`, presente na lista de itens
  - **Commit:** `8489fed`

- [x] **T-008** — RN-001: categoria fora da política é recusada e permanece no resultado
  - **Atende:** RN-001
  - **Aceite:** `test_rn_001_categoria_fora_da_politica_e_recusada` — `coworking` de R$ 89,00 resulta em `0.00`, status `recusada`
  - **Commit:** `9a3f528`

- [x] **T-009** — RN-004: duplicatas — primeira ocorrência paga, demais recusadas
  - **Atende:** RN-004, AMB-008
  - **Aceite:** `test_rn_004_duplicata_exata_recusa_a_segunda` — duas despesas iguais em data, categoria, fornecedor, descrição e valor resultam em R$ 54,90 e R$ 0,00; e `test_rn_004_fornecedor_diferente_nao_e_duplicata` passa
  - **Commit:** `3b1184f`

- [x] **T-010** — RN-005: estornos — valor negativo abate integral, sem teto e sem nota
  - **Atende:** RN-005, AMB-010
  - **Aceite:** `test_rn_005_estorno_abate_valor_integral` — −R$ 45,00 resulta em −R$ 45,00, status `estorno`; e −R$ 500,00 em alimentação não é limitado pelo teto
  - **Commit:** `e64b46e`

- [x] **T-011** — RN-006: nota fiscal obrigatória acima de R$ 100,00, comparação estrita, recusa integral na ausência
  - **Atende:** RN-006, AMB-003, AMB-004, AMB-005
  - **Aceite:** `test_rn_006_piso_e_exclusivo` — R$ 100,00 sem nota segue para o teto; `test_rn_006_acima_do_piso_sem_nota_e_recusada` — R$ 100,01 sem nota resulta em `0.00`
  - **Commit:** `22ea8fb`

- [x] **T-012** — RN-007: teto por despesa e reembolso parcial com glosa do excedente
  - **Atende:** RN-007, AMB-001, AMB-002
  - **Aceite:** `test_rn_007_teto_e_por_despesa_nao_por_dia` — R$ 72,50 e R$ 38,00 no mesmo dia resultam em R$ 60,00 e R$ 38,00; `test_rn_007_valor_no_teto_e_aprovado_integralmente` — R$ 60,00 sai como `aprovada` sem glosa
  - **Commit:** `2627349`

- [x] **T-013** — RN-008: cada lançamento de hospedagem vale uma diária; descrição não é interpretada
  - **Atende:** RN-008, AMB-007
  - **Aceite:** `test_rn_008_hospedagem_conta_como_uma_diaria` — R$ 480,00 descrita como "2 diarias", fora de viagem, resulta em R$ 250,00
  - **Commit:** `d706158`

- [x] **T-014** — RN-009: `Contexto` de viagem — datas com lançamento de hospedagem ampliam os tetos em 50%
  - **Atende:** RN-009, AMB-006
  - **Aceite:** `test_rn_009_data_com_hospedagem_amplia_tetos` — R$ 480,00 em `2026-07-14` resulta em R$ 375,00; `test_rn_009_hospedagem_recusada_ainda_caracteriza_viagem` passa; `test_rn_009_viagem_nao_amplia_piso_da_nota` passa
  - **Commit:** `8dc368a`

- [x] **T-015** — Calculadora: encadeia as regras na ordem da spec §8, parando na primeira que recusa
  - **Atende:** `spec.md` §8, RN-001 a RN-010
  - **Aceite:** `test_ordem_nota_fiscal_antes_do_teto` — `d-004` (R$ 100,01, transporte, sem nota) resulta em `0.00` e **não** em R$ 80,00, provando que o passo 7 roda antes do 8
  - **Commit:** `4b43e1b`

## Fase 3 — Casos de borda

- [x] **T-016** — Tabela de casos de borda da spec §7 como teste parametrizado, uma linha por caso
  - **Atende:** `spec.md` §7 (18 linhas)
  - **Aceite:** `test_casos_de_borda` — 18 casos passam, cada um identificado pelo ID da regra no parâmetro
  - **Commit:** `11fadb7`

- [x] **T-017** — Fronteiras testadas dos dois lados: R$ 100,00/R$ 100,01 e R$ 60,00/R$ 60,01
  - **Atende:** RN-006, RN-007, `plan.md` §6
  - **Aceite:** `test_fronteiras_inclusivas_e_exclusivas` — os quatro casos passam com os valores da spec
  - **Commit:** `ab7c6ce`

- [x] **T-018** — Lista de despesas vazia produz resultado válido com todos os totais em `0.00`
  - **Atende:** `spec.md` §7 (última linha)
  - **Aceite:** `test_lista_vazia_produz_resultado_valido` — saída bem formada, sem exceção
  - **Commit:** `8c88711`

## Fase 4 — Saída e CLI

- [x] **T-019** — Serializador: `Decimal` como texto de duas casas, `Status` em minúsculas, `valor_glosado` derivado
  - **Atende:** `spec.md` §4 (saída)
  - **Aceite:** `test_serializa_valores_como_texto_de_duas_casas` — `Decimal("60")` sai como `"60.00"`; nenhum `Decimal` cru chega ao `json.dump`
  - **Commit:** `fef1c39`

- [x] **T-020** — Resumo: totais lançado, reembolsável e glosado, mais contagem por status
  - **Atende:** `spec.md` §4, §9 (penúltimo critério)
  - **Aceite:** `test_soma_dos_itens_bate_com_o_resumo` — a soma dos `valor_reembolsavel` dos itens é idêntica a `resumo.total_reembolsavel`
  - **Commit:** `55ff10a`

- [x] **T-021** — CLI: `calcular --input <arquivo> --output <arquivo>`
  - **Atende:** contrato fixo do `DESAFIO.md`
  - **Aceite:** `test_cli_calcular_escreve_saida` — o comando cria o arquivo de saída e retorna código 0; entrada inválida retorna código diferente de 0 sem criar o arquivo
  - **Commit:** `9012a18`

- [x] **T-022** — Teste ponta a ponta sobre `exemplos/despesas-exemplo.json`
  - **Atende:** `spec.md` §9 (critérios 1 a 8)
  - **Aceite:** `test_e2e_exemplo_oficial` — total reembolsável `703.43` sobre total lançado `1816.84`, com os valores por item que a spec §9 fixa para `d-003`, `d-004`, `d-006`, `d-007`, `d-010`, `d-011` e `d-014`
  - **Commit:** `ac39242`

---

## Fase 5 — Política externa por centro de custo (T-023..T-026)

> Absorve o bloco A do envelope do Dia 2 (`exemplos/envelope/00-ENVELOPE-LACRADO.md`),
> registrado em D-002 (`DECISIONS.md`). Derivado de `spec.md` 1.2 e `plan.md` 1.1.

- [x] **T-023** — `motor/politica.py` deixa de expor constantes e passa a expor `Politica` e `LimiteCategoria` (`@dataclass(frozen=True)`), com `limite(centro_custo, categoria) -> Decimal | None` fazendo o merge `{**padrao, **centros_custo.get(cc, {})}` e `categorias_cobertas(centro_custo)`
  - **Atende:** RN-012, AMB-013, AMB-014, `plan.md` §4
  - **Aceite:** `test_rn_012_cc_desconhecido_usa_padrao`, `test_rn_012_categoria_ausente_no_cc_herda_padrao`, `test_rn_012_cc_sobrepoe_o_padrao`
  - **Commit:** `21d8bba` (test) / `93e1737` (feat)

- [x] **T-024** — `io/carregador_politica.py`: lê o documento de política e monta uma `Politica`, com `parse_float=Decimal`, validação nomeando o campo ausente (mesmo padrão de `ErroDeEntrada` do `io/carregador.py`); `acrescimo_em_viagem_percentual: 50` vira fator `1.5`
  - **Atende:** `spec.md` §4 (documento de política), `plan.md` DT-008
  - **Aceite:** `test_carregador_politica_rejeita_campo_ausente`, `test_carregador_politica_converte_percentual_em_fator`
  - **Commit:** `cb11194` (test) / `9c7636d` (feat) — extraiu `io/erros.py` do `io/carregador.py` para reuso

- [x] **T-025** — `Contexto` ganha `centro_custo` e `politica`. RN-001 e RN-007 passam a consultar a política em vez de constantes; limite `0.00` recusa (RN-012, AMB-014); RN-009 lê o fator de viagem da política
  - **Atende:** RN-001, RN-007, RN-009, RN-012
  - **Aceite:** `test_rn_012_limite_zero_recusa`, `test_rn_001_representacao_coberta_apenas_no_cc_comercial`, `test_rn_009_fator_vem_da_politica`
  - **Commit:** `06ab7d4` (test) / `36332db` (feat) — RN-006 também migrou (piso vem da política), necessário para o módulo compilar

- [x] **T-026** — CLI ganha `--politica` **opcional**, com default resolvido a partir da raiz do pacote (não do diretório de trabalho), apontando para a tabela vigente. Preserva o contrato fixo `calcular --input X --output Y` do `DESAFIO.md` — os casos ocultos do instrutor rodam sem flag nova
  - **Atende:** `DESAFIO.md` (contrato fixo da CLI), `plan.md` §1
  - **Aceite:** `test_cli_usa_politica_padrao_sem_flag`, `test_cli_aceita_politica_alternativa`
  - **Commit:** `6568b3b` (test) / `3396ed9` (feat)

## Fase 6 — Despesas internacionais (T-027..T-031)

> Absorve o bloco B do envelope, registrado em D-003 (`DECISIONS.md`).

- [ ] **T-027** — `Despesa` ganha `moeda`, `valor_origem`, `taxa_cambio`, `data_taxa`. O carregador de despesas lê `moeda` como campo opcional, default `BRL`, normalizada (caixa/espaços)
  - **Atende:** `spec.md` §4 (entrada), `plan.md` §3
  - **Aceite:** `test_carregador_moeda_ausente_assume_brl`, `test_carregador_normaliza_codigo_de_moeda`
  - **Commit:** `<preencher>`

- [ ] **T-028** — `motor/cambio.py` puro: `TabelaCambio.taxa(moeda, data) -> tuple[Decimal, date] | None`, retrocedendo para a última data que tenha aquela moeda. `io/carregador_cambio.py` lê o documento de câmbio; CLI ganha `--cambio` opcional, mesmo padrão de default da T-026
  - **Atende:** RN-011, AMB-018, AMB-019, `plan.md` DT-008
  - **Aceite:** `test_rn_011_taxa_da_data_exata`, `test_rn_011_data_sem_cotacao_usa_ultima_anterior`, `test_rn_011_sem_cotacao_anterior_recusa`
  - **Commit:** `<preencher>`

- [ ] **T-029** — Aplica DT-007: o passo do pipeline passa a devolver `Parecer | Despesa | None`; a calculadora passa a ter uma lista única de passos e `normalizar_categoria` (RN-002) entra nela como passo 2. `converter_para_brl` entra como passo 6
  - **Atende:** `spec.md` §8, `plan.md` DT-007
  - **Aceite:** `test_ordem_conversao_antes_da_nota_fiscal`, `test_pipeline_e_uma_lista_unica`
  - **Commit:** `<preencher>`

- [ ] **T-030** — RN-011 completa: converte o valor de origem pela taxa, arredonda uma única vez (RN-010 estendida, AMB-020), preenche `valor_origem`/`taxa_cambio`/`data_taxa` na `Despesa` resultante. Moeda sem cotação (AMB-019) recusa com valor `0.00` em BRL e origem preservada
  - **Atende:** RN-010, RN-011, AMB-020, AMB-023
  - **Aceite:** `test_rn_011_moeda_sem_cotacao_e_recusada`, `test_rn_011_arredonda_valor_convertido`, `test_rn_011_item_nao_convertivel_nao_polui_total`
  - **Commit:** `<preencher>`

- [ ] **T-031** — RN-004 passa a incluir `moeda` na chave de duplicata (AMB-022); RN-006 compara o piso ao valor já convertido em reais (AMB-021); o serializador emite `moeda`/`valor_origem`/`taxa_cambio`/`data_taxa` por item e o bloco `politica` no cabeçalho
  - **Atende:** RN-004, RN-006, AMB-021, AMB-022, `spec.md` §4 (saída)
  - **Aceite:** `test_rn_004_moedas_diferentes_nao_sao_duplicata`, `test_rn_006_piso_comparado_ao_valor_convertido`, `test_serializa_despesa_em_moeda_estrangeira`, `test_serializa_bloco_politica_no_cabecalho`
  - **Commit:** `<preencher>`

## Fase 7 — Reexecução dos aceites (T-032..T-034) — ponto de corte seguro

> Com as Fases 5 e 6 verdes, a spec §9 (v1.2) passa a valer. Estas tasks
> conferem os três totais registrados em D-002/D-003 e na memória de cálculo
> de `docs/HANDOFF-dia2.md`, item a item, antes de qualquer trabalho opcional.

- [ ] **T-032** — Atualiza `test_e2e_exemplo_oficial` para os valores da v1.2 (**R$ 341,93** sobre R$ 1.816,84), com comentário citando D-002
  - **Atende:** `spec.md` §9
  - **Aceite:** `test_e2e_exemplo_oficial` verde nos novos números, incluindo `d-001` (72,50, integral), `d-010` (0,00) e `d-014` (61,00, integral)
  - **Commit:** `<preencher>`

- [ ] **T-033** — Testes ponta a ponta novos sobre os dois arquivos de `exemplos/envelope/`
  - **Atende:** `spec.md` §9
  - **Aceite:** `test_e2e_envelope_cc_comercial` (R$ 1.343,26 sobre R$ 2.457,52), `test_e2e_envelope_cc_desconhecido` (R$ 433,76 sobre R$ 623,76)
  - **Commit:** `<preencher>`

- [ ] **T-034** — Casos de borda novos da spec §7 (v1.2) em `test_casos_de_borda.py`; os casos já existentes usam `centro_custo: "CC"` (ausente da tabela ⇒ padrão) e continuam válidos sem alteração de valor
  - **Atende:** `spec.md` §7
  - **Aceite:** `test_casos_de_borda` com as linhas novas (limite zero, CC desconhecido, categoria só existente num CC, moeda sem cotação, fronteira de R$ 500,00); contador de casos atualizado
  - **Commit:** `<preencher>`

## Fase 8 — Fila de aprovação manual (T-035..T-036) — opcional

> Absorve o bloco C do envelope, registrado em D-004 (`DECISIONS.md`). Só
> começar com a Fase 7 inteiramente verde. Se não fechar, D-004 e `spec.md`
> §3 são reescritas declarando o item fora de escopo desta entrega — nunca
> deixadas descrevendo um comportamento que o código não tem.

- [ ] **T-035** — Enum `Estado` (`aprovacao_automatica` / `pendente_aprovacao`) em `motor/modelo.py`; campo `estado` em `Parecer`; `rn_013_fila_aprovacao(parecer, contexto)` como passo pós-decisão (não recusa, não altera valor)
  - **Atende:** RN-013, AMB-024
  - **Aceite:** `test_rn_013_acima_de_500_fica_pendente`, `test_rn_013_exatamente_500_nao_fica_pendente`, `test_rn_013_estorno_nunca_fica_pendente`
  - **Commit:** `<preencher>`

- [ ] **T-036** — Saída ganha `itens[].estado`, `resumo.quantidade_por_estado`, `resumo.total_pendente_aprovacao`
  - **Atende:** RN-013, `spec.md` §4 (saída)
  - **Aceite:** `test_resumo_conta_pendencias`; `test_e2e_envelope_cc_comercial` passa a conferir que `e-007` sai com estado `pendente_aprovacao`
  - **Commit:** `<preencher>`

---

## Cobertura

Preencha ao fechar cada fase. É a sua própria checagem de rastreabilidade — e é
exatamente a matriz que a correção vai montar.

| Regra da spec | Task | Teste |
|---|---|---|
| RN-001 | T-008 | `test_rn_001_categoria_fora_da_politica_e_recusada` |
| RN-002 | T-006 | `test_rn_002_categoria_em_caixa_alta_e_normalizada` |
| RN-003 | T-007 | `test_rn_003_despesa_fora_da_competencia_e_recusada` |
| RN-004 | T-009 | `test_rn_004_duplicata_exata_recusa_a_segunda` |
| RN-005 | T-010 | `test_rn_005_estorno_abate_valor_integral` |
| RN-006 | T-011 | `test_rn_006_piso_e_exclusivo` |
| RN-007 | T-012 | `test_rn_007_teto_e_por_despesa_nao_por_dia` |
| RN-008 | T-013 | `test_rn_008_hospedagem_conta_como_uma_diaria` |
| RN-009 | T-014 | `test_rn_009_data_com_hospedagem_amplia_tetos` |
| RN-010 | T-003 | `test_rn_010_arredonda_na_leitura` |
| AMB-001 | T-012 | `test_rn_007_teto_e_por_despesa_nao_por_dia` |
| AMB-002 | T-012 | `test_rn_007_valor_no_teto_e_aprovado_integralmente` |
| AMB-003 | T-011 | `test_rn_006_piso_e_exclusivo` |
| AMB-004 | T-011 | `test_rn_006_acima_do_piso_sem_nota_e_recusada` |
| AMB-005 | T-015 | `test_ordem_nota_fiscal_antes_do_teto` |
| AMB-006 | T-014 | `test_rn_009_viagem_nao_amplia_piso_da_nota` |
| AMB-007 | T-013 | `test_rn_008_hospedagem_conta_como_uma_diaria` |
| AMB-008 | T-009 | `test_rn_004_fornecedor_diferente_nao_e_duplicata` |
| AMB-009 | T-007 | `test_rn_003_despesa_fora_da_competencia_e_recusada` |
| AMB-010 | T-010 | `test_rn_005_estorno_abate_valor_integral` |
| AMB-011 | T-003 | `test_rn_010_arredonda_na_leitura` |
| AMB-012 | T-006 | `test_rn_002_categoria_em_caixa_alta_e_normalizada` |
| Ordem §8 | T-015 | `test_ordem_nota_fiscal_antes_do_teto` |
| §7 bordas | T-016, T-017, T-018 | `test_casos_de_borda`, `test_fronteiras_inclusivas_e_exclusivas` |
| §9 aceite (v1.1) | T-022 | `test_e2e_exemplo_oficial` |
| RN-011 | T-028, T-030 | `test_rn_011_taxa_da_data_exata`, `test_rn_011_data_sem_cotacao_usa_ultima_anterior`, `test_rn_011_sem_cotacao_anterior_recusa`, `test_rn_011_moeda_sem_cotacao_e_recusada` |
| RN-012 | T-023, T-025 | `test_rn_012_cc_sobrepoe_o_padrao`, `test_rn_012_cc_desconhecido_usa_padrao`, `test_rn_012_categoria_ausente_no_cc_herda_padrao`, `test_rn_012_limite_zero_recusa` |
| RN-013 | T-035 | `test_rn_013_acima_de_500_fica_pendente`, `test_rn_013_exatamente_500_nao_fica_pendente`, `test_rn_013_estorno_nunca_fica_pendente` |
| AMB-013 | T-023 | `test_rn_012_categoria_ausente_no_cc_herda_padrao` |
| AMB-014 | T-025 | `test_rn_012_limite_zero_recusa` |
| AMB-015 | T-025 | `test_rn_009_hospedagem_com_limite_zero_ainda_caracteriza_viagem` |
| AMB-016 | T-034 | `test_casos_de_borda` (linha "periodicidade não agrega por dia") |
| AMB-017 | T-024 | `test_carregador_politica_converte_percentual_em_fator` (vigência apenas copiada, não validada) |
| AMB-018 | T-028 | `test_rn_011_data_sem_cotacao_usa_ultima_anterior` |
| AMB-019 | T-030 | `test_rn_011_moeda_sem_cotacao_e_recusada` |
| AMB-020 | T-030 | `test_rn_011_arredonda_valor_convertido` |
| AMB-021 | T-031 | `test_rn_006_piso_comparado_ao_valor_convertido` |
| AMB-022 | T-031 | `test_rn_004_moedas_diferentes_nao_sao_duplicata` |
| AMB-023 | T-030 | `test_rn_011_item_nao_convertivel_nao_polui_total` |
| AMB-024 | T-035 | `test_rn_013_exatamente_500_nao_fica_pendente` |
| §7 bordas (v1.2) | T-034 | `test_casos_de_borda` (linhas novas) |
| §9 aceite (v1.2) | T-032, T-033 | `test_e2e_exemplo_oficial`, `test_e2e_envelope_cc_comercial`, `test_e2e_envelope_cc_desconhecido` |
