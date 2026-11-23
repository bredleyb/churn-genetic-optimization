# Segunda auditoria do painel Cliente — 23/11/2026

## Evidência recebida
Arquivos: `Texto colado(6).txt` e `testes-visuais-para-revisao(20261123-045525).zip`.

- Python: **76 aprovados** (17,08 s).
- Playwright: **29 aprovados, 6 falhas, nenhum ignorado** (7,6 min).
- CL-B03 (execução real da previsão) **aprovado**.
- Regressões resolvidas em relação à primeira rodada: layout desktop,
  alinhamento/perfis, sintaxe e seletores de campos, foco nas abas.

## Seis falhas e causas

| Cenário | Causa verificada | Intervenção |
|---|---|---|
| CL-F02 e CL-F08 | A rotina `settleCaret` programava `requestAnimationFrame(placeCaret)` após o clique; o frame desfazia o `Ctrl+A`, produzindo `31 meses` ao substituir 3 por 1 | Removido o reposicionamento assíncrono. Sufixo continua imutável e caret é protegido sincronicamente no evento |
| CL-F05 | O Playwright clicava diretamente no `input` do checkbox React Aria; o `label` clicável interceptava o evento | Teste usa clique sobre o texto/rótulo e verifica `checked`, seguido de Space por teclado |
| CL-F07 | A coluna de Cobrança mensal era estreita; o `st.number_input` omitia os controles − e + | Layout rápido agora se adapta à largura **do painel Cliente** por `@container`, empilhando as colunas quando houver menos de 335 px de conteúdo. Teste F07 agora percorre as seis resoluções |
| CL-L01, 1024×768 | O rótulo Tipo de contrato ocupava duas linhas (40 px), desalinhando os campos | O mesmo breakpoint por largura útil evita a quebra e preserva a simetria de Tempo/Serviço e Contrato/Cobrança |
| CL-L01, 390×900 | Media query móvel declarava 44 px; seletor mais específico mantinha a altura de 48 px do botão | Altura unificada pelo token `--n3-client-action-height` (48 px padrão, 44 px no móvel), sem sobrescrita concorrente |

O CSS de `number_input` passa a considerar tanto `stNumberInputContainer`
(estrutura React Aria encontrada no navegador) quanto `data-baseweb="input"`
(compatibilidade), dentro da regra compartilhada de campos.

## Critérios preservados

- Cinco perfis, criação, restauração, exclusão e renumeração.
- Quatro abas, 19 características, valores e serviços dependentes.
- Fundo, fontes, alinhamento vertical, rótulos e foco.
- Duas sombras dinâmicas, rolagem e rodapé fixo.
- Calcular → Calculando → Recalcular com estados de cor, animação e hover.
- Treinamento, seleção genética, resultados e documentação científica não foram alterados.

As correções **não foram executadas no Chromium integrado nesta sessão**.
A verificação estática e a publicação no GitHub precedem a próxima rodada
local. A auditoria completa depende do novo relatório.

## Próxima execução

    git pull
    python -m pytest -q
    npm run test:visual

Analisar CL-F02, CL-F05, CL-F07 nas seis resoluções, CL-F08 e CL-L01
em 1024×768 e 390×900. Inspecionar as capturas CL-* anexadas e confirmar
ausência de regressões nas áreas já aprovadas.
