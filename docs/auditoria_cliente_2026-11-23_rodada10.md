# Décima auditoria do painel Cliente — ciclo dos seletores

**Data:** 23/11/2026

## Solicitação

Após padronizar a cor clara (`#F5F5F5`) da borda dos campos,
foi observado que um `st.selectbox` continuava com borda clara depois
da escolha de opção ou do fechamento do menu. A seta de expansão também
deveria inverter para indicar recolhimento, com uma animação breve.

## Causa

A regra anterior incluía `:focus-within` e
`[data-focus-within="true"]` no grupo do seletor. O Streamlit React Aria
pode preservar o foco no combobox quando a lista é fechada; portanto,
esses seletores CSS mantinham a borda em `#F5F5F5` após o fechamento.

## Correção

1. A borda do `st.selectbox` muda para `#F5F5F5` **somente quando**
   existe um descendente com `aria-expanded="true"`.
2. Com a lista fechada, a borda volta imediatamente à cor normal
   `#55585D`, mesmo se o foco DOM ainda estiver no campo.
   A largura permanece **1 px** e o raio permanece **4 px**.
3. O SVG do botão de expansão mantém orientação normal (seta para
   baixo) quando fechado e recebe `rotate(180deg)` quando aberto.
   A transição é de **160 ms**, `ease-in-out`.
4. `prefers-reduced-motion:reduce` desativa a transição mantendo o
   indicador de estado.
5. Campos numéricos e o componente Tempo preservam a regra própria
   de `:focus-within`; perfis, cálculos e algoritmos não são alterados.

## Cobertura adicionada

- **CL-F15** foi adaptado: foco isolado com menu fechado mantém borda
  cinza; abertura muda para clara; escolha e Esc devolvem cinza.
  Os seletores das quatro abas são percorridos em 1440 e 390 px.
  Cobrança e Total cobrado permanecem ativos com foco normal.
- **CL-F16**, novo em 1440 e 390 px: estado da seta, rotações
  de 0°/180°, transição de 160 ms, seleção de opção,
  fechamento com Esc e `prefers-reduced-motion`.
- **pytest:** contrato CSS garante que a borda dos seletores não dependa
  de `:focus-within`, que a seta use `aria-expanded` e que a opção
  de movimento reduzido esteja presente.

## Estado de validação

A publicação e a sintaxe dos arquivos podem ser conferidas remotamente.
A execução completa no Streamlit exige o ambiente Windows com as
dependências e o dataset original.

A última execução integral compartilhada, **77 pytest e 45 Playwright**,
pertence a uma versão anterior às auditorias 9 e 10. Esses resultados
não validam as alterações novas.

    git pull
    python -m pytest -q
    npm run test:visual

**Coleta esperada: 79 testes pytest e 53 testes Playwright.**
O aceite requer todos aprovados e conferência das capturas da seta
nos dois estados.
