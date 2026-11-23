# Nona auditoria — foco de todos os campos do painel Cliente

**Data:** 23/11/2026

## Evidências e requisito

As três capturas recebidas mostram:
- **Tempo como cliente:** a última intervenção produziu uma borda de foco
  excessivamente espessa e uma segunda linha branca sobre a borda.
- **Tipo de contrato:** o foco do campo deve permanecer claro enquanto a
  lista estiver aberta e retornar ao cinza após o fechamento/perda de foco.
- **Perfil de exemplo:** o estado selecionado já utiliza a cor `#F5F5F5`
  em uma borda de **1 px** e serve de referência cromática para os campos.

A regra de interação deve abranger Tempo, Cobrança mensal, Total cobrado
e todos os seletores das quatro abas, independentemente da resolução.

## Correção integrada

1. O campo Tempo preserva uma única borda CSS de **1 px**.
   O estado `:focus-within` altera somente `border-color` para
   `var(--n3-text,#F5F5F5)`. O pseudo-elemento `::after` com borda
   de 2 px da oitava auditoria foi removido.
2. Os `st.number_input` nativos usam a mesma borda de 1 px quando
   recebem foco interno. Removido o ring `::after` de 2 px e anulados
   contornos/sombras adicionais na caixa.
3. Os `st.selectbox` React Aria usam a mesma borda clara quando o grupo
   contém o foco. A condição `[aria-expanded="true"]` mantém o destaque
   durante a abertura da lista, inclusive se o foco estiver no portal
   do menu. O botão de abertura deixa de usar fundo elevado somente
   por `:focus-visible`; o hover continua independente.
4. Os botões internos de incremento, decremento e abertura de opções
   usam a borda da caixa como indicador de foco, sem outlines próprios.
5. O padrão `--n3-text` é compartilhado com o perfil ativo. Fundo,
   tipografia, espaçamentos, alturas, raios e comportamento de hover
   exclusivo dos steppers permanecem inalterados.

## Critérios de regressão

- **CL-F02:** foco de Tempo com borda branca de 1 px e ausência de
  pseudo-ring, box-shadow ou outline adicionais.
- **CL-F13/F14:** borda de 1 px e cantos de 4 px durante o hover
  dos botões, mantendo o comportamento exclusivo após clicar.
- **CL-F15:** percorre os seletores das quatro abas em 1440 e 390 px,
  verificando a borda branca de 1 px no foco, inclusive com menu aberto;
  confirma a volta ao cinza e avalia Cobrança mensal/Total cobrado.
- **pytest:** contratos exigem borda única nos três tipos de campos e
  rejeitam o retorno dos pseudo-elementos de 2 px.

## Estado da validação

A última execução compartilhada anterior a esta mudança aprovou
**77/77 pytest e 45/45 Playwright**. A oitava auditoria adicionou novos
testes, ainda sem resultado de execução local enviado. A nona substitui
as expectativas de ring espesso por borda de 1 px e adiciona CL-F15
parametrizado.

A regra CSS de `:focus-within` e seletor aberto foi reproduzida em
Chromium isolado: borda cinza `rgb(85,88,93)` em repouso, branca
`rgb(245,245,245)` quando focada ou expandida e novamente cinza
após o fechamento. A largura computada permaneceu em `1px`, sem
`box-shadow`.

A aprovação da integração completa depende de uma execução local:

    git pull
    python -m pytest -q
    npm run test:visual

Expectativa: **78 testes pytest e 51 cenários Playwright**. O teste
de interação real continua obrigatório antes do aceite final.
