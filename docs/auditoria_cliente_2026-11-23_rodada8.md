# Oitava auditoria do painel Cliente — foco e hover dos steppers

**Data:** 23/11/2026

## Evidências recebidas

A captura `image(20261123-065712).png` apresenta o campo
**Tempo como cliente** focado, com o botão `+` em cinza de hover e uma
interrupção visível na borda branca superior e inferior.

O pacote `testes-visuais-para-revisao(20261123-065806).zip` confirma:

- **pytest: 77/77 aprovados**.
- **Playwright: 45/45 aprovados**, sem falhas, ignorados ou testes instáveis.
- **CL-F11** e **CL-F12** aprovados (colagem e proteção contra listeners
  duplicados); o algoritmo completo CL-B03 também passou.

## Causa visual

O foco de Tempo era estilizado com
`box-shadow: inset 0 0 0 1px` no container. Os steppers filhos desenhavam
seus fundos de hover acima dessa sombra e podiam ocultar a borda branca.
O CSS `button:hover` também dependia do estado de hover nativo, que pode
ficar associado a um irmão quando o Streamlit remonta/atualiza o campo sob
um ponteiro imóvel.

O mesmo comportamento era possível no `st.number_input` de Cobrança,
que tinha `button:hover` sem controle de intenção do ponteiro.

## Ajuste estrutural

1. A camada de foco pertence à caixa: `::after` absoluto, `inset:0`,
   borda branca de 2 px, `border-radius:inherit`, `z-index:3`,
   `pointer-events:none`. O conteúdo permanece recortado com
   `overflow:hidden`, preservando os quatro cantos.
2. Os steppers de Tempo recebem a marca `data-n3-pointer-hover="true"`
   apenas quando ocorre `pointermove` sobre o botão correspondente.
   `pointerdown`, `pointerleave` e uma remontagem limpam a marca.
3. Os steppers de Cobrança recebem o mesmo tratamento, por delegação de
   eventos no componente JS de interface já existente, sem enviar novos
   estados ao Python.
4. A paleta é preservada: `#0E1013` no estado comum, `#202124` no
   hover e `#F5F5F5` no ring de foco.

## Regressões adicionadas

- **CL-F02:** atualiza a prova de foco para verificar a borda branca do
  pseudo-elemento, sua posição superior e ausência de interceptação do mouse.
- **CL-F13 (1440/390):** foco, curvatura, hover exclusivo por movimento do
  ponteiro e limpeza após clicar em `+` e `−` do Tempo.
- **CL-F14 (1440/390):** os mesmos critérios para a Cobrança nativa.
- **pytest:** contrato CSS+JS de ambas as implementações.

O total esperado é **78 testes pytest e 49 testes Playwright**.

## Estado de validação

A suíte 77/45 aprovada pertence à versão anterior. A nova versão requer
execução local para confirmar as alterações e inspecionar as screenshots
adicionadas:

    git pull
    python -m pytest -q
    npm run test:visual

Os modelos e resultados de ML, dados, perfis e demais componentes não foram
alterados por essa correção.
