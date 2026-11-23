# Sexta auditoria do painel Cliente — diagnóstico estrutural

**Data:** 23/11/2026  
**Evidências:** `Texto colado(10).txt` e
`testes-visuais-para-revisao(20261123-060807).zip`.

## Resultado recebido

- pytest: **77/77 aprovados**.
- Playwright: **39/41 aprovados**.
- Falhas persistentes: **CL-F02** e **CL-F08**.
- Todos os demais casos passaram, inclusive CL-B03 (algoritmo real),
  CL-F03 (abas), CL-F07 (steppers da Cobrança) e as seis resoluções de layout.

## Investigação do defeito

Os snapshots do trace Playwright mostram:

1. Antes de Ctrl+A: input com valor `3 meses`.
2. Depois de Ctrl+A: os atributos `data-select-all-digits="true"`
   aparecem **tanto no input quanto no host** do componente v2.
3. Após inserir o dígito `1`: input com valor `31 meses`;
   os atributos de intenção de seleção já foram consumidos/removidos.
4. O teste sintético CL-F09 anterior aprovava, mesmo com a aplicação real
   falhando repetidamente. Portanto, ele não reproduzia o ciclo completo
   de edição e sincronização do Streamlit.

O trace confirma a divergência entre a intenção de seleção e o resultado
da inserção. Ele **não registra qual callback exato** apagou ou contornou
a seleção; atribuir o evento a uma chamada específica seria especulação.

A revisão do código identificou o problema arquitetural: o input textual
concentrava ao mesmo tempo `3` e ` meses` no valor editável. Isso exigia
interceptar Ctrl+A, `beforeinput`, remoções, seleção, colagens, posicionamento
do cursor, `input` de fallback e estados temporários do host. Cada
`setStateValue` do componente v2 também dispara um rerun Python, aumentando
a superfície para competição de estados.

## Reestruturação implementada

| Camada | Versão anterior | Nova versão |
|---|---|---|
| Modelo do input | Texto `3 meses` | String numérica `3` |
| Unidade | Sufixo dentro do valor editável | Elemento `<span>` não editável, na mesma caixa visual |
| Ctrl+A | Evento cancelado e seleção manual de dígitos | Seleção nativa do navegador |
| Cursor e Backspace | Cálculo, correção e reposicionamento manuais | Operações nativas em texto numérico |
| Antes da digitação | Interceptação de toda edição | Apenas bloqueio de caracteres não numéricos |
| Eventos enviados ao Python | Inteiro 0–999 | Exatamente o mesmo contrato |
| Atualizações v2 | Flags artificiais para preservar seleção | DOM numérico ativo prevalece sobre prop antiga durante foco |
| Regressão | Input acoplado à unidade | Número e unidade testados separadamente, mantendo aparência |

A estrutura de perfis, a key por revisão, os estados de previsão, os
19 campos e o algoritmo genético permanecem inalterados.

## Validação disponível

Em Chromium isolado, com o novo renderer real e host simulado, foram
verificados: incremento/decremento; Ctrl+A seguido de `1`;
Backspace/Delete; singular/plural; valor máximo; rascunho vazio;
rerun com prop antiga durante o foco; e atualização externa sem foco.
O resultado `3` → Ctrl+A → `1` foi **`1 mês`**.

Os testes do repositório foram ajustados conforme a semântica nova:

- **CL-F02 e CL-F08:** continuam exigindo que Ctrl+A substitua o número
  no Streamlit real; verificam também o sufixo visível.
- **CL-F09:** reproduz rerun v2, rascunho focado, atualização legítima e
  nova revisão do nó DOM.
- **CL-F10:** verifica visualmente a adjacência número/unidade e a
  seleção exclusivamente numérica em 1440 e 390 px.
- **CL-F11:** bloqueio de caracteres não numéricos, colagem válida e
  rascunho vazio normalizado quando o foco sai.
- **CL-P01:** verifica meses por número e unidade ao trocar/restaurar perfis.
- **pytest:** contrato estrutural exige um único input com sufixo separado
  e rejeita a volta das rotinas de seleção artificiais.

## Aceite pendente

A nova implementação foi validada no navegador isolado e por sintaxe.
Não há nesta sessão um ambiente Streamlit com dependências instaladas
e o dataset original para executar a suíte de ponta a ponta.
A próxima execução local deve conter **44 cenários Playwright**
(41 anteriores + 2 parametrizações CL-F10 + 1 CL-F11).

    git pull
    python -m pytest -q
    npm run test:visual

**Critério de conclusão:** CL-F02 e CL-F08 aprovados na interface real,
CL-F09/F10/F11 aprovados, sem regressões nos 39 cenários previamente
aprovados. Os screenshots continuam obrigatórios para conformidade visual.
