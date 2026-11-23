# Terceira auditoria do painel Cliente — 23/11/2026

## Evidências recebidas

Arquivos: `Texto colado(7).txt` e
`testes-visuais-para-revisao(20261123-051515).zip`.

- Python: **76 testes aprovados**, em 17,07 s.
- Playwright: **37 aprovados, 3 falhos, 0 ignorados, 0 instáveis**, em 3,5 min.
- CL-B03 (previsão real, conclusão e dados alterados): **aprovado**.
- CL-F05 (checkbox), CL-F07 (controles da Cobrança em seis resoluções),
  CL-L01 em 1024×768 e 390×900: **aprovados** após a segunda rodada.

## Três falhas restantes

| Caso | Evidência | Causa investigada | Correção |
|---|---|---|---|
| CL-F02 e CL-F08 | `Ctrl+A`, seguido de `1`, converte `3 meses` em `31 meses` | O `render()` inicial do componente v2 ainda chamava `placeCaret()`, mesmo sem edição. Uma reexecução do JS entre as teclas pode desfazer a seleção numérica; a remoção anterior do `requestAnimationFrame` não resolvia esse caminho | O posicionamento do cursor passa a ocorrer em eventos de foco, clique e `commit`; `render()` atualiza o valor e o estado dos botões sem interferir na seleção |
| CL-L01, 1280×720 | Centro do título: 173,664 px; centro do Cliente: 184,797 px; deslocamento 11,133 px à esquerda | O grid do painel definia linhas, mas mantinha a coluna implícita, permitindo que a largura de seu conteúdo afetasse o espaço atribuído ao título | Declarada uma coluna explícita `minmax(0,1fr)` e largura total para o wrapper compartilhado dos títulos |

A primeira falha foi reproduzida em duas modalidades do Playwright. O
mecanismo de perda de seleção na reexecução foi adicionalmente isolado em
Chromium: atualizar o valor do input sem reposicionar o cursor preserva
`selectionStart=0`, `selectionEnd=1` e permite substituir `3` por `1`.

A captura de 1280×720 comprova o desalinhamento do título, enquanto os
campos e o botão seguem a margem compartilhada do Cliente.

## Alterações e garantias

- `src/tenure_control.mjs`: separação de renderização e posicionamento de
  cursor. `Ctrl+A` continua selecionando apenas os dígitos; a unidade
  permanece no mesmo `input` e protegida.
- `streamlit_app.py`: definição explícita da coluna completa do grid
  Cliente e largura do wrapper dos títulos; sem compensações em pixels.
- `tests/client/test_client_contracts.py`: novas asserções para garantir
  que `render()` não reposicione o cursor e que o título ocupe a coluna completa.
- Os testes de navegador CL-F02, CL-F08 e CL-L01 permanecem sem relaxamento:
  devem validar o comportamento real após o `git pull`.

A lógica dos perfis, os 19 campos, os dados, o treinamento e o algoritmo
genético não foram modificados.

## Situação e próxima execução

Os resultados **37/40** descrevem a versão anterior à correção desta rodada.
A suíte completa da nova versão ainda precisa ser executada no ambiente do
usuário. A aprovação exige:

    git pull
    python -m pytest -q
    npm run test:visual

Inspecionar os logs CL-F02, CL-F08 e CL-L01 (1280×720), conferindo também
os 37 cenários que já haviam passado. Anexar o ZIP do relatório atualizado.
