# Relatório — Desafio SDD

**Aluno:** vitorhugoreiis · **Repositório:** `sdd-desafio` (branch `feature/day2_implementation_envelope`) · **Data:** 2026-07-31

> Isto não é redação. São **evidências**. Toda afirmação deve vir acompanhada de
> arquivo, hash de commit ou trecho de sessão exportada. Um parágrafo bonito sem
> evidência vale menos que uma frase curta com um hash.
>
> Vale 20 dos 100 pontos, e é a seção que mais separa notas.

---

## Delegação

*O que você fez, o que o Claude fez, e por que dividiu assim.*

**A divisão:**

| Atividade | Quem | Por quê |
|---|---|---|
| Identificar ambiguidades | Claude, sistematicamente contra `exemplos/despesas-exemplo.json` | Claude levantou as 12 ambiguidades da v3 numa tabela com opções A/B/C e a consequência numérica de cada uma no exemplo (`docs/sessions/02-especificacao-spec-plan-tasks.md:621-656`) |
| Decidir as ambiguidades (v3) | Nominalmente eu, na prática delegado em bloco | Minha resposta inteira foi `"1A e assim por diante... completa tudo de acordo com o que esta sendo solicitado nos arquivos"` (`docs/sessions/02-especificacao-spec-plan-tasks.md:721`) — não há decisão individual registrada para as outras 11 |
| Decidir as ambiguidades (v4, envelope) | Colaborativo, com checkpoint explícito | A tabela "Decisões de ambiguidade já tomadas (confirmadas com o usuário)" em `docs/HANDOFF-dia2.md:44-49` — quatro decisões (CC sobrepõe padrão, retrocesso de câmbio, moeda sem cotação recusa, fila como fase final) discutidas e fechadas antes de eu autorizar a execução |
| Escrever a spec | Claude redige, eu aprovo por bloco | `spec.md` 1.0 saiu inteira do commit `a85d821`; a 1.2 (v4) saiu inteira de `29a3686`, redigida a partir do plano já fechado em `docs/HANDOFF-dia2.md` |
| Desenhar a arquitetura | Claude (DT-001 a DT-008 em `plan.md`) | Eu não propus nenhuma decisão técnica — só travei a ordem de execução (spec → DECISIONS → tasks → código) e a granularidade de commit |
| Implementar | Claude, autonomamente | Sessão 03 (T-001..T-022) e sessão 05 (T-023..T-036, este relatório) rodaram sem eu interromper entre tasks |
| Escrever testes | Claude, mesmo agente que escreveu o código | Ver ressalva em Diligência — é exatamente o risco que o próprio template do relatório avisa |
| Absorver o envelope | Claude planeja (sessão 04) e executa (sessão 05); eu fixo a ordem inegociável e o número de aceite como oráculo | Minha instrução de abertura desta sessão: *"O aceite oficial quebra de propósito: R$ 703,43 → R$ 341,93. Se a implementação der outro número, [...] a primeira hipótese é erro de conta meu, não bug."* — decidi verificar pelo **resultado**, não pelo processo |

**Onde deleguei e me arrependi:** não identifiquei um caso concreto de arrependimento até o fechamento deste relatório — a arquitetura do Dia 1 (DT-002/DT-004) absorveu a política externa e o câmbio sem precisar de retrabalho (ver "O envelope" abaixo), o que sugere que delegar o desenho técnico foi uma aposta que se pagou. Mas o candidato mais honesto a "deveria ter pensado duas vezes" é a própria decisão de ambiguidade em bloco (`1A e assim por diante`) — funcionou, mas eu não teria como saber disso *antes* de funcionar, e é o tipo de aposta que só parece boa em retrospecto.

**Onde não deleguei e deveria ter delegado:** não encontrei um caso claro. A única coisa que retive deliberadamente — o número de aceite como oráculo de verificação — não foi um excesso de controle; foi o único ponto de verificação barato que eu tinha, dado que não li o diff linha a linha (ver Diligência).

**Usei subagentes / skills / MCP / hooks?** Não. O trabalho é uma cadeia sequencial onde cada etapa depende do estado final da anterior (spec precisa existir antes do `plan.md`; uma task de código às vezes depende do código da task anterior) — não identifiquei um recorte que se beneficiasse de paralelização por subagente sem herdar o risco de dessincronizar do plano único. Isso já estava registrado como decisão consciente em `docs/HANDOFF-dia2.md:309` antes desta sessão começar.

---

## Descrição

*Como você transformou requisito ambíguo em requisito verificável.*

Ambiguidade escolhida: **AMB-006 — "colaborador em viagem tem limites ampliados em 50%"**, porque é o único item que o próprio `plan.md` 1.0 já sinalizava como maior risco do projeto (`§7`, linha "O envelope do Dia 2 muda a unidade de aplicação do teto... Alta") antes de o envelope existir.

**Texto do RH (imutável, política v3, item 6):**
> "Colaborador em viagem tem limites ampliados em 50%."

**V1 — como Claude estruturou a ambiguidade antes de qualquer decisão** (`docs/sessions/02-especificacao-spec-plan-tasks.md:650`):
> `6 | "em viagem" | A infere (ex.: há hospedagem na data) · B declara fora de escopo até existir o campo · C exige campo novo na entrada | Nenhuma despesa marca viagem. Sub-pergunta: os 50% ampliam também o piso de 100 da nota?`

**Minha decisão** (`docs/sessions/02-especificacao-spec-plan-tasks.md:721`, resposta a uma tabela de 12 itens):
> "1A e assim por diante... completa tudo de acordo com o que esta sendo solicitado nos arquivos e nos exemplos que te entreguei."

**Versão final na spec** (`specs/001-motor-reembolso/spec.md` §6, AMB-006 — texto idêntico desde o commit `a85d821`, primeiro conteúdo real do arquivo):
> **Decisão:** viagem é inferida pela existência de lançamento de hospedagem na mesma data, aprovado ou não. A ampliação alcança apenas os tetos por categoria, não o piso da nota fiscal.
> **Justificativa:** hospedagem é o indício mais direto de pernoite fora, e é o único disponível na entrada; o piso da nota é regra de comprovação, não de limite de gasto, e não há razão para afrouxá-lo em viagem.

**O que estava ambíguo:** duas perguntas empilhadas — (1) como inferir viagem sem campo dedicado na entrada, e (2) se a ampliação alcança também o piso de nota fiscal (uma sub-pergunta que a política do RH nem cogita).

**Como percebi:** não fui eu — foi Claude, ao rodar a política mentalmente contra `d-010`/`d-013` (as duas hospedagens do exemplo oficial) e notar que nenhuma delas tem como ser "viagem" sem uma regra de inferência. Isso está documentado no próprio texto acima ("Nenhuma despesa marca viagem").

**Honestidade sobre o "V1 → final":** o texto da §6 do `spec.md` **não mudou** entre o primeiro commit de conteúdo (`a85d821`) e hoje — `git diff a85d821 bd1f432 -- specs/001-motor-reembolso/spec.md` mostra que o único ajuste feito depois (`bd1f432`, D-001) foi um rótulo de regra num exemplo ilustrativo não relacionado. A primeira versão já saiu correta. O `DESAFIO.md` aceita essa resposta explicitamente: *"Se a primeira versão já estava boa, prove com o histórico do arquivo."* O que de fato evoluiu não foi a prosa da spec, e sim o processo que a produziu: de uma frase ambígua do RH para uma tabela de opções com consequência numérica, para uma decisão em bloco minha, para o texto final com decisão e justificativa — nunca reescrito.

**Continuação no envelope (AMB-015):** a v4 reabriu exatamente esta regra — "hospedagem com limite R$ 0,00 ainda caracteriza viagem?" — e a resposta que dei nesta sessão (`spec.md` AMB-015) foi a mesma lógica de AMB-006 aplicada a um caminho de recusa novo: o indício é o pernoite, não o pagamento. **Commit:** `29a3686`.

---

## Discernimento

*Onde o Claude errou e você pegou.*

> **Sem um caso concreto e verificável, esta seção vale zero.**

### Caso 1 — fase de rubrica inventada no plano do envelope

**O que ele propôs:** durante o planejamento do envelope (sessão 04), Claude tentou editar `docs/HANDOFF-dia2.md` para acrescentar uma **"Fase 9 — Passagem pela `RUBRICA.md`"**, um gate formal de conferência da rubrica antes do relatório final.

**Por que estava errado:** a rubrica é o instrumento de quem corrige, não um entregável. `template/` tem seis arquivos (`CLAUDE.md`, `RELATORIO.md`, `spec.md`, `plan.md`, `tasks.md`, `DECISIONS.md`) e nenhum é de rubrica; o `DESAFIO.md` só manda lê-la antes de começar. Era uma fase a mais no repositório sem nenhum pedido do enunciado — exatamente a categoria "solução desnecessariamente complexa" que o próprio `DESAFIO.md` lista como erro esperado do agente.

**Como eu detectei:** rejeitei a edição (a ferramenta registra a rejeição) e devolvi uma pergunta direta: *"a forma que o avaliador esta pedindo a rubrica é dessa forma que estamos fazendo mesmo?"* — sem afirmar que estava errado, só pedindo para conferir antes de aceitar.

**O que ele fez:** Claude rodou `ls template/` e `grep` pelas menções à `RUBRICA.md` fora dela mesma, confirmou que ela nunca é citada como entregável, admitiu o exagero ("a Fase 9 que eu ia criar era invenção minha, e ainda por cima do tipo errado") e reduziu a proposta aos quatro pontos reais que a rubrica expunha, encaixando-os dentro das fases que já existiam — sem criar fase nova.

**Onde está a evidência:** `docs/sessions/04-plano-envelope-dia2.md:1559-1660` (a pergunta na linha 1559, a rejeição da ferramenta logo antes da linha 1601, a verificação e o recuo entre 1607 e 1660).

### Caso 2 — mensagem de commit corrompida por sintaxe de shell errada

**O que ele propôs:** para commitar o plano do envelope, Claude rodou `git commit -q -m @'...'@` dentro da ferramenta Bash — sintaxe de here-string do **PowerShell**, não do Bash (a ferramenta Bash deste ambiente é Git Bash).

**Por que estava errado:** o Bash não reconhece `@'...'@`; o `@` sobrou como texto literal e virou a primeira "palavra" da mensagem de commit: `bb53fe6 @ docs: plano de absorcao do envelope do Dia 2 (Politica v4)`.

**Como eu detectei:** não fui eu desta vez — foi o próprio Claude, ao conferir o resultado do commit (`git log -1 --format='%B'`) logo depois de criá-lo, e reconheceu o problema imediatamente: *"O `@'...'@` é sintaxe PowerShell — no Bash ele virou parte da mensagem."*

**O que ele fez:** corrigiu com `git commit --amend -F -` usando um heredoc de Bash de verdade, produzindo a mensagem limpa que está hoje no histórico como `fcdf7eb docs: plano de absorcao do envelope do Dia 2 (Politica v4)`.

**Onde está a evidência:** `docs/sessions/04-plano-envelope-dia2.md:1200-1250`.

### Padrão que eu notei

Os dois casos acima e um terceiro — uma afirmação exagerada de que descrever os *campos* dos documentos de política e câmbio na spec seria "vazamento de solução" (`docs/sessions/04-plano-envelope-dia2.md:1688-1728`; a spec já documenta campos de contrato de entrada como `despesas[].tem_nota_fiscal`, então campo não é vazamento — arquivo, caminho, flag e formato são) — têm o mesmo formato: **Claude se autocorrigiu ao conferir o próprio resultado, não porque eu apontei o erro antes.** Isso se repetiu nesta própria sessão: escrevi dois testes novos (`test_rn_009_hospedagem_com_limite_zero_ainda_caracteriza_viagem` e `test_rn_009_fator_vem_da_politica`, em `tests/test_rn_009_viagem.py`) assumindo que o valor reembolsável seria sempre igual ao teto ampliado — errado quando a despesa fica abaixo do teto, caso em que o reembolsável é o valor lançado. `pytest` acusou os dois na hora (`Decimal('85.00') == Decimal('90.00')` e `Decimal('480.00') == Decimal('500.00')`, ambos `AssertionError`), e corrigi antes de qualquer commit — nenhum dos dois chegou a entrar no histórico como erro. Isso é bom sinal de rede de segurança (suíte + leitura de output), mas é desconfortável como sinal de supervisão: em nenhum dos quatro casos fui eu quem primeiro percebeu.

---

## Diligência

*O que você verificou antes de aceitar.*

**Meu procedimento de verificação real, nesta sessão:** não li o diff linha a linha em tempo real — deixei o agente executar as 36 tasks de forma contínua. O que eu de fato fiz foi fixar, **antes** de qualquer código, três âncoras de verificação baratas e difíceis de forjar por acidente: (1) a ordem inegociável spec → DECISIONS → tasks → código; (2) commits sempre em pares `test`/`feat` a partir de T-023; (3) os três números de aceite (341,93 / 1.343,26 / 433,76), pré-calculados à mão na sessão anterior e registrados em `docs/HANDOFF-dia2.md`, como oráculo independente do código.

**Li o diff inteiro em que porcentagem das entregas?** Perto de 0% em tempo real nesta sessão. A verificação aconteceu por proxy: `pytest -q` rodou depois de cada mudança de código (42 vezes, uma por commit), e eu só seguia adiante com a suíte relevante verde. Isso pega regressão de comportamento; não pega, por exemplo, uma regra implementada de um jeito diferente do que a spec diz mas que ainda passa nos testes que eu mesmo não escrevi.

**O que aceitei sem verificar direito, e o que isso me custou:** aceitei que "a arquitetura absorveu a task de graça" (T-030, T-032, T-033 e T-034 fecharam sem nenhum commit `feat`, só reexecutando os testes contra a política real — ver `tasks.md`) como sinal de que a Fase 6 estava correta, sem uma segunda conferência independente da minha própria conta de 341,93/1.343,26/433,76. Não me custou nada desta vez — os três valores bateram exatamente — mas é sorte de ter feito a conta direito da primeira vez, não verificação.

**Testes: quem escreveu, e como você sabe que testam a coisa certa?** Claude escreveu 100% dos testes desta sessão — o mesmo agente que escreveu a implementação, exatamente o risco que este template avisa ("teste escrito pelo mesmo agente que escreveu o código passa com muita facilidade"). A mitigação real que existe: os testes de cada task foram escritos e **confirmados falhando** antes do código de produção existir (ex.: `ImportError: cannot import name 'LimiteCategoria'` no commit `21d8bba`, antes de `93e1737`; `AttributeError: 'Despesa' object has no attribute 'moeda'` no commit `397f920`, antes de `1e94ffd`) — então pelo menos sei que cada teste falha quando deveria falhar. A segunda mitigação é o oráculo externo: os totais de aceite não vieram do código, vieram de uma conta manual anterior a qualquer implementação (`docs/HANDOFF-dia2.md`, seção "Anexo — memória de cálculo").

---

## O envelope

*A mudança de requisito do Dia 2.*

**Quantos arquivos toquei na mão:** 41 em `src/`, `tests/` e `specs/` (`git diff e025389 HEAD --name-status -- src/ tests/ specs/`), mais os 5 arquivos de dados do envelope movidos para `exemplos/envelope/`, mais `README.md` e `CLAUDE.md`. Nenhum arquivo foi tocado por mim diretamente — todos passaram pelo agente.

**Quanto tempo levou:** do primeiro commit desta sessão (`8aea45d`, 23:56, movendo o envelope) até o fechamento da Fase 8 (`629f40d`, 00:48) — **52 minutos de tempo de commit** para as 36 tasks completas (T-023 a T-036), incluindo as quatro fases de documentação prévias ao código. É um número que só faz sentido em tempo de agente: a sessão de planejamento equivalente (sessão 04, humano lendo o envelope e decidindo as quatro ambiguidades) levou perto de 2h. A diferença não é qualidade — é que esta sessão não teve nenhuma pausa de deliberação humana no meio.

**Diff de absorção:** 41 arquivos, **+2.812/−756** linhas em `src/`+`tests/`+`specs/` (`git diff e025389 HEAD --stat -- src/ tests/ specs/`); 49 arquivos, +3.670/−794 linhas incluindo toda a documentação de fechamento fora de `docs/sessions/`.

**Absorveu de graça:** DT-002 (lista declarada de regras) e DT-004 (`Contexto` construído uma vez antes do laço, no Dia 1) — política e câmbio entraram como campos novos do `Contexto` sem nenhuma regra existente mudar de assinatura de decisão. O efeito mais visível: quatro tasks (**T-030, T-032, T-033, T-034**) fecharam com **só** commit `test`, sem `feat` correspondente — a implementação de T-029 já cobria o comportamento que essas tasks vieram medir (ver as notas de cada uma em `tasks.md`).

**Resistiu:** DT-007. A assinatura `(Despesa, Contexto) -> Parecer | None` do Dia 1 não comportava um passo que **transforma** a despesa e **pode recusar** ao mesmo tempo — exatamente o que a conversão cambial (RN-011) precisa fazer. Teve que virar `Parecer | Despesa | None`, e isso puxou `normalizar_categoria` (RN-002), que vivia fora do laço principal desde o Dia 1, para dentro da mesma lista declarada (`construir_passos`, T-029, commits `4a2ef59`/`5a45017`).

**Ordem em que fiz:** spec (`29a3686`) → `DECISIONS.md` (`d7a16de`) → `plan.md` (`5307457`) → `tasks.md` (`019aa68`) → código T-023..T-036, cada task em par `test`/`feat` → `README.md`/`CLAUDE.md` → este relatório. `git log --format="%ad %h %s" e025389..HEAD` confirma a ordem por timestamp — nenhum código antes dos três documentos.

**Se eu tivesse escrito a spec original sabendo desta mudança:** teria desenhado `Politica` e `TabelaCambio` como estruturas consultáveis desde o Dia 1, em vez de constantes de módulo — o que eliminaria o único ponto de resistência real (DT-007 continuaria existindo, porque é sobre conversão, não sobre política). Mas o `plan.md` 1.0 já registrava essa generalização como risco avaliado e decidiu **não** antecipá-la (§4: "constantes em módulo próprio... se o Dia 2 trouxer limites variáveis por perfil, este é o módulo que vira tabela") — o que é exatamente a recomendação do `FAQ.md` ("resista à tentação de otimizar demais na expectativa da mudança"). Não mudaria essa decisão.

**O que a spec me poupou, em concreto:** nenhuma regra de negócio nova entrou direto no código. As 12 ambiguidades do envelope (AMB-013 a AMB-024) foram identificadas, decididas e justificadas em `spec.md` §6 **antes** de qualquer linha em `src/` mudar (`29a3686`, antes de `21d8bba`) — inclusive a mais arriscada de errar sem registro, D-002 (a quebra de R$ 703,43 para R$ 341,93), que entrou em `DECISIONS.md` **antes** do teste que a confirma (`d7a16de` antes de `2d17be1`). Isso é o que a regra 2 do jogo do `DESAFIO.md` — "explicação no chat que não está na spec é bug de spec" — pretende evitar, e não encontrei um caso em que ela tenha sido violada nesta sessão.

---

## Fechamento

**Para qual tamanho de projeto isto valeu a pena?** Para um motor de decisão com ~13 regras de negócio, política externa mutável e múltiplos aceites ponta a ponta — o suficiente para que uma mudança de requisito (o envelope) pudesse ser absorvida sem reescrever a arquitetura, porque a arquitetura já tinha sido desenhada com esse ponto de extensão em mente (`Contexto`, DT-004).

**Para qual não valeria?** Para um script de uma tela ou uma feature isolada sem regra de negócio versionável, o custo de escrever `spec.md` → `plan.md` → `tasks.md` antes de qualquer código provavelmente não se paga — não há ambiguidade suficiente para justificar o processo, e o `FAQ.md` já avisa contra "otimizar demais" onde não há sinal de que vai precisar.

**O que eu faria diferente:** revisaria individualmente pelo menos as ambiguidades que o próprio `plan.md` já sinalizava como alto risco (AMB-006/RN-009, listada em `plan.md` §7 como "Alta" probabilidade) em vez de aprovar as 12 originais em bloco com "1A e assim por diante" — não porque a decisão saiu errada, mas porque eu não tinha como saber que sairia certa antes do fato.

**A coisa mais desconfortável que aprendi sobre como trabalho com IA:** em nenhum dos casos concretos de erro documentados nesta sessão (Discernimento, Casos 1 e 2, mais os dois exemplos do "padrão que notei") fui eu quem percebeu primeiro — foi o próprio agente, ao conferir o resultado de uma ferramenta ou ao rodar `pytest`. Minha diligência real neste projeto se concentrou em poucos pontos de alta alavancagem (a ordem dos commits, a granularidade `test`/`feat`, e três números de aceite calculados à mão) em vez de leitura contínua do trabalho. Funcionou — a suíte fechou verde, os três totais bateram exatamente. O desconfortável é que "funcionou" e "eu estava efetivamente supervisionando" não são a mesma coisa, e este relatório, sozinho, não permite a quem o lê distinguir uma da outra.
