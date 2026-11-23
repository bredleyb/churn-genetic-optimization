# Décima primeira auditoria — menu abre antes da animação da seta

**Data:** 23/11/2026

## Defeito observado

Após a atualização da seta dos `st.selectbox`, a rotação de 160 ms
parecia ocorrer integralmente antes da exibição da lista. O requisito
de interface é abrir as opções no clique, mantendo a rotação como um
efeito visual independente.

## Análise da integração

O `st.selectbox` da versão atual do Streamlit utiliza um
`StyledOpenButton` dentro de um `ComboBox` e renderiza as opções por
meio de `StyledPopover`, com `data-testid="stSelectboxVirtualDropdown"`,
em um portal separado. O código anterior iniciava a rotação quando
`aria-expanded="true"` era aplicado ao combobox. Isso podia começar
antes de a lista ter sido montada.

## Alteração

O CSS agora exige simultaneamente:

1. O combobox contém `aria-expanded="true"`.
2. O popover `[data-testid="stSelectboxVirtualDropdown"]` existe no DOM.

Só então o SVG recebe `rotate(180deg)` e inicia a transição de
160 ms. Assim, a orientação não inicia antecipadamente enquanto a
lista ainda está sendo montada. A abertura e a seleção continuam
sob o controle nativo do Streamlit/React Aria, sem interceptação de
cliques ou temporizadores adicionais.

O fechamento continua devolvendo a seta para 0°, e a configuração
`prefers-reduced-motion:reduce` permanece respeitada. As regras de
borda clara somente com o menu expandido e de borda cinza ao fechar
também foram preservadas.

## Verificação

- **CL-F16 (1440 e 390 px):** registra por `MutationObserver` a
  inserção do popover e mede o ângulo da seta naquele instante.
  Exige que a lista esteja montada antes de a rotação terminar.
  Continua conferindo a orientação final, fechamento com escolha
  de opção, Esc e preferência por movimento reduzido.
- **pytest:** garante que a regra de rotação está condicionada à
  presença real do popover.
- **Chromium isolado:** com montagem artificial do popover atrasada
  em 230 ms, a seta permaneceu a 0° até a inserção da lista e
  girou depois da montagem.

## Aceite

A reprodução controlada confirma a ordem CSS dos eventos; a
latência real do menu no Streamlit requer a execução integral.
Se o popover continuar demorando a ser montado, a investigação
deverá analisar o componente nativo de dropdown separadamente da
animação da seta.

    git pull
    python -m pytest -q
    npm run test:visual

A coleta esperada permanece em **79 pytest e 53 Playwright**.
