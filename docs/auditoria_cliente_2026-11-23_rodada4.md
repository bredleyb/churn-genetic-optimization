# Quarta auditoria do painel Cliente — 23/11/2026

## Evidências examinadas

Arquivos locais recebidos: `Texto colado(8).txt` e
`testes-visuais-para-revisao(20261123-053250).zip`.

- **pytest:** 76 aprovados em 17,44 s.
- **Playwright:** 37 aprovados, 3 falhos, 0 ignorados, 0 instáveis;
  duração 7,5 min (um timeout de 240 s).
- **CL-L01 em 1280×720:** aprovado; a centralização do título corrigiu-se.
- **CL-B03:** previsão real, conclusão e estado alterado aprovados.
- As demais cinco resoluções, campos de Cobrança, perfis, scroll e cores
  também passaram novamente.

## Três falhas atuais

| Cenário | Evidência | Hipótese técnica e intervenção |
|---|---|---|
| CL-F02 e CL-F08 | Ctrl+A seguido de 1 produz `31 meses` em vez de `1 mês` | A reprodução isolada do editor nativo funciona; o problema depende de atualizações do componente v2. O renderer agora usa o texto válido do próprio input enquanto ele está focado e só reatribui `input.value` quando o texto precisa realmente mudar. Uma atualização atrasada do backend não deve desfazer a seleção do usuário. |
| CL-F03 | Após alterações em Perfil e clique em Extras, `Streaming de filmes` nunca aparece; o snapshot final mostra Perfil selecionado | O seletor de abas anterior não rastreava o estado ativo durante os reruns dos campos. A navegação agora usa `st.tabs(..., key="dashboard_client_active_tab", on_change="rerun")`, recurso nativo da versão exigida de Streamlit. |

No CL-F03, o timeout de 240 s dificulta a análise. O helper agora exige
que o campo da aba atual fique visível em até 15 s e o teste confirma a aba
Extras selecionada antes da edição.

## Testes adicionados e preservados

- **CL-F09:** um teste de navegador que reutiliza a implementação real do
  componente de Tempo, reproduz uma montagem v2 com valor desatualizado
  enquanto Ctrl+A mantém selecionada a parte numérica, digita `1` e
  verifica o resultado `1 mês`. Verifica também que atualizações externas
  continuam válidas quando o campo perde o foco.
- **CL-F02 / CL-F08:** testes ponta a ponta mantidos, com seleção e escrita
  no formulário Streamlit real.
- **CL-F03:** seleção e retenção da aba Extras após alterações anteriores,
  além dos valores do Perfil.
- **pytest:** contratos para preservar a montagem do editor com seleção ativa
  e a seleção de abas entre reruns.

## Escopo preservado

Nenhuma alteração nas 19 características, algoritmo genético, regressão
logística, métricas, dados, perfis ou fluxo de cálculo. A mudança de navegação
usa a API de tabs disponível em `streamlit>=1.67,<2`.

**Importante:** os resultados acima pertencem à versão anterior a estas
correções. A sintaxe e as invariantes estáticas foram conferidas. O aceite
funcional da nova versão requer nova execução local do Streamlit.

    git pull
    python -m pytest -q
    npm run test:visual

O total esperado de testes Playwright passa a **41**, pelo CL-F09.
