# Validação da aplicação

## Execução local

Com o ambiente virtual ativado na raiz do repositório e o CSV original em `data/raw/`:

```powershell
python -m pip check
python -m pytest -q
npm run test:visual
```

O último comando gera o ZIP local com relatório JSON, HTML, capturas e configurações. O relatório identifica o HEAD e se havia alterações nos arquivos versionados no início da execução. Dados brutos, modelos e artefatos de treinamento não são versionados.

## Verificações

| Área | Evidência |
|---|---|
| Ciência | Pytest e CLI: divisão estratificada, CV somente no desenvolvimento, regressão logística, configuração genética e avaliação reservada |
| Estado | Pytest e Playwright: espera, execução, conclusão, dados alterados, recuperação do snapshot, erro parcial e retry |
| Cliente | CL-F, CL-L, CL-P, CL-S e CL-V: campos, dependências, perfis, layout, rolagem e feedback |
| Previsão | CL-B e PR-G: P1 e P2 com CSV real, status, probabilidades, gráfico, genes, impacto e separação dos cartões |
| Abas | PR-N e PR-T: navegação, métricas, histórico, log e download UTF-8 |
| Acessibilidade | PR-A e PR-R: fontes, ícones, foco, teclado, toque, tooltips, limites e redimensionamento |

## Demonstração

1. Abrir a GUI em espera, conferir o CSV e selecionar Exemplo 1.
2. Executar e mostrar o status, os dois modelos, genes e gráfico. Probabilidades de cancelamento esperadas: 82,04% e 76,66%.
3. Mostrar Métricas e Terminal: F1 de teste 0,6040 e 0,5869; 19 para 9 características; 165 e 173 falsos negativos.
4. Alterar um campo efetivo e observar a indisponibilidade das probabilidades. Voltar ao valor anterior e verificar a recuperação do snapshot.
5. Selecionar Exemplo 2 e executar: 0,37% e 0,71%.
6. Explicar a diferença entre validação cruzada e teste reservado e a limitação de uma única divisão/busca.

Contingência: gerar os modelos com `python -m scripts.compare_models` e usar `python -m scripts.predict --cliente examples/cliente_exemplo.json` e `python -m scripts.predict --cliente examples/cliente_exemplo_2.json`.

## Limites de validação

As asserções de navegador verificam comportamento e geometria; capturas complementam a análise visual. Testes simulados de falha e validação não substituem as execuções reais com o CSV original. Os testes automatizados não certificam conformidade integral WCAG nem equivalência pixel a pixel ao Figma. O modo Presentation do protótipo e o ensaio de apresentação são verificações separadas.
