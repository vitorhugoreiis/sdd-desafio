# Sessões exportadas

## Por que o formato é este

O comando `/export` do Claude Code não funcionou nesta máquina. Segui a
alternativa documentada no [`FAQ.md`](../../FAQ.md#L74-L75) do desafio: copiar os
transcripts de `~/.claude/projects/<slug-do-projeto>/*.jsonl` para cá.

Cada sessão aparece em dois arquivos:

| Arquivo | O que é |
|---|---|
| `NN-descricao.jsonl` | Cópia **crua e inalterada** do transcript do Claude Code. É a fonte da verdade. |
| `NN-descricao.md` | Renderização legível do mesmo transcript, gerada por `_exportar.py`. Resultados de ferramenta longos aparecem truncados, com o corte sinalizado. |

O `.md` existe porque o `.jsonl` é uma linha por registro e é ilegível a olho nu.
Em qualquer divergência entre os dois, **vale o `.jsonl`** — ele não passou por
nenhum tratamento.

## Sessões

| # | Período | O que aconteceu |
|---|---|---|
| 01 | 2026-07-30 20:19–20:25 | Abertura, interrompida em 6 minutos. Mantida por honestidade de registro: mostra a falsa partida antes do trabalho real. |
| 02 | 2026-07-30 20:49–22:32 | Especificação completa: levantamento das 12 ambiguidades, decisão, `spec.md` 1.0, `plan.md` 1.0, `tasks.md` T-001..T-022. |
| 03 | 2026-07-30 23:44–00:30 | Implementação completa das Fases 1 a 4 (T-001..T-022): núcleo do motor, carregador, serializador, CLI, 94 testes. Corrigiu inconsistência RN-006/RN-007 no exemplo da spec (`DECISIONS.md` D-001) antes de codificar. Exportada em andamento — pode não conter as mensagens finais da sessão. |
| 04 | 2026-07-30 | Abertura do envelope do Dia 2 (Política v4). Leitura dos quatro arquivos do envelope, das 12 ambiguidades novas que ele traz e do impacto na spec 1.1. **Nenhum código escrito** — a sessão produziu o plano de absorção (`doc-handoff-dia2.md`), incluindo as 4 decisões de ambiguidade e a memória de cálculo dos novos aceites. |
| 05 | 2026-07-31 | Execução do plano do Dia 2 do começo ao fim: Fase 0 (move o envelope para `exemplos/envelope/`) → spec 1.2 → `DECISIONS.md` (D-002/D-003/D-004) → plan 1.1 (DT-007/DT-008) → `tasks.md` T-023..T-036 → todas as 14 tasks de código, em pares `test`/`feat` → README/CLAUDE.md → este `docs/RELATORIO.md`. Fechou com 162 testes verdes e os três aceites (341,93 / 1.343,26 / 433,76) batendo exatamente com a memória de cálculo do `docs/HANDOFF-dia2.md`, sem precisar corrigir nenhum número. Exportada perto do fechamento — pode não conter as últimas mensagens. |

## Como reexportar

Ao final de cada sessão, rode a partir da raiz do repositório:

```bash
python docs/sessions/_exportar.py
```

Ele varre o diretório de transcripts, copia os `.jsonl` novos e regenera os `.md`.

**Atenção:** o transcript de uma sessão é gravado enquanto ela acontece. Exportar
no meio da sessão captura só até aquele ponto — por isso a sessão 02 não contém
o próprio ato de exportar. Reexporte ao fechar o terminal.