## Seleção de características com algoritmo genético para previsão de churn

Este estudo verifica se um **algoritmo genético** consegue reduzir as variáveis de entrada de uma
**regressão logística** que prevê o cancelamento de clientes (*customer churn*) sem perder poder preditivo.
Os dados vêm do setor de telecomunicações.

Projeto de Aprendizagem de Máquina de **Bredley Bauer**, **Gabriel Coelho** e **Gustavo Haiduk Pereira**.

---

## Resultado em resumo

A busca genética reduziu as variáveis de **19 para 9 (−52,6%)**, com perda pequena de desempenho no conjunto de teste reservado (1.409 clientes).

| Métrica (teste) | Referência — 19 características | Seleção genética — 9 características |
|---|---:|---:|
| **F1-score** | **0,6040** | 0,5869 |
| Precisão | 0,6572 | 0,6463 |
| Revocação | 0,5588 | 0,5374 |
| Acurácia | 0,8055 | 0,7991 |
| ROC-AUC | 0,8419 | 0,8401 |

Na validação cruzada, o subconjunto genético superou a referência (F1 0,6059 contra 0,5952), mas essa vantagem
não se manteve no teste. Por isso o teste fica separado até o fim. O modelo reduzido deixou de identificar
8 cancelamentos a mais que a referência.

Matrizes de confusão, variáveis escolhidas e discussão: **[docs/resultados_experimentais.md](docs/resultados_experimentais.md)**.

---

## Como funciona

```
CSV Telco (7.043 clientes)
  └─ divisão estratificada 80/20 (seed 42)
       ├─ desenvolvimento (5.634) ─┬─ referência: regressão logística com as 19 características
       │                           └─ algoritmo genético: escolhe o subconjunto (CV estratificada, 3 partições)
       └─ teste (1.409) ─────────── avaliação final dos dois modelos, usada uma única vez
```

- **Pré-processamento:** um `ColumnTransformer` ajustado só nas partições de treino. Faz imputação pela mediana e padronização nas variáveis numéricas (`tenure`, `MonthlyCharges`, `TotalCharges`) e imputação pela moda com *one-hot* nas 16 categóricas. `SeniorCitizen` é tratada como categórica.
- **Cromossomo:** 19 bits, um por característica original. Quando uma característica categórica é selecionada, todas as colunas *one-hot* dela entram juntas.
- **Aptidão:** F1 médio na validação cruzada menos `λ = 0,02` vezes a fração de características usadas.
- **Parâmetros:** 24 indivíduos, 15 gerações, torneio de 3, cruzamento de um ponto (p = 0,8), mutação por indivíduo (p = 0,2, com inversão de cada bit a `1/19`), elitismo de 1. Cromossomos vazios são proibidos e avaliações repetidas ficam em cache.

---

## Início rápido

É preciso ter **Python 3.10+**. Os comandos abaixo são para PowerShell e devem ser executados na raiz do repositório.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

**Dados:** baixe o [Telco Customer Churn (Kaggle, blastchar)](https://www.kaggle.com/datasets/blastchar/telco-customer-churn)
e salve o arquivo em `data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv`. O CSV não é versionado. Detalhes em [data/README.md](data/README.md).

Depois rode o experimento completo e abra o dashboard:

```powershell
python -m scripts.compare_models          # treina, seleciona e avalia os dois modelos
python -m streamlit run streamlit_app.py  # dashboard interativo
```

### Todos os comandos

| Comando | O que faz | Saída em `results/` |
|---|---|---|
| `python -m scripts.analyze_data --data <csv>` | Análise exploratória (qualidade, classes, churn por contrato e conexão) | `analise_dados.{json,md}` |
| `python -m scripts.train_baseline` | Validação cruzada da regressão logística completa | `baseline_cv.json`, `baseline.joblib` |
| `python -m scripts.run_genetic` | Busca genética e treino com o subconjunto escolhido | `genetic_selection.json`, `genetic.joblib` |
| `python -m scripts.compare_models` | Comparação final no conjunto de teste | `comparacao_modelos.{json,md}`, `*.joblib` |
| `python -m scripts.predict --cliente <json>` | Previsão para um cliente novo (`--modelo baseline\|genetico`) | — |

Para um teste rápido do algoritmo genético: `python -m scripts.run_genetic --population 6 --generations 2`.
Os artefatos em `results/` são gerados localmente e não são versionados.

---

## Previsão para um novo cliente

Os arquivos em [examples/](examples/) trazem perfis fictícios com as 19 características originais, sem `customerID` e sem `Churn`.

```powershell
python -m scripts.predict --cliente examples/cliente_exemplo.json
```

| Perfil | Referência | Seleção genética | Previsão |
|---|---:|---:|---|
| `cliente_exemplo.json` | 82,04% | 76,66% | Cancelamento |
| `cliente_exemplo_2.json` | 0,37% | 0,71% | Permanência |

Os percentuais são a probabilidade de cancelamento estimada pelo modelo, não uma garantia sobre o cliente.
Para testar outro perfil, copie um dos JSONs e altere os valores: `tenure` é dado em meses, `SeniorCitizen` vale 0 ou 1
e `TotalCharges` aceita `null`. Carregue apenas arquivos `.joblib` gerados pelo próprio projeto.

---

## Dashboard

[streamlit_app.py](streamlit_app.py) reúne a previsão e o experimento em um painel monocromático pensado para projeção
(resolução prioritária: 1280 × 720). O verde e o vermelho aparecem só nos estados Permanência e Cancelamento.

- **Cliente:** formulário com as 19 características em abas (Perfil, Conta, Serviços, Extras) e até 5 perfis por sessão. Os perfis 1 e 2 são protegidos.
- **Comparação:** probabilidades de cancelamento dos dois modelos para o cliente atual.
- **Gráfico:** evolução do melhor F1 em validação cruzada ao longo das gerações.
- **Características e teste:** cromossomo de 19 bits, F1 de teste, ΔF1 e taxa de redução.
- **Monitor:** eventos reais do algoritmo genético, com download do log completo.

**Calcular previsão** executa o experimento inteiro com a configuração original, sem sobrescrever os modelos salvos em `results/`.

---

## Testes

```powershell
python -m pytest -q                 # dados, modelo, algoritmo genético, avaliação e painel Cliente

npm install
npx playwright install chromium
npm run test:visual                 # testes de navegador no painel Cliente (porta 8517)
npm run test:visual:report          # abre o relatório HTML
```

Os testes Playwright cobrem layout, tipografia, foco, rolagem, interação e responsividade em seis resoluções.
Cada rodada salva as evidências em `results/testes-visuais-para-revisao.zip`. O teste E2E `CL-B03` precisa do CSV
original e é marcado como *skipped* quando o arquivo não existe. Os requisitos e critérios de aceite estão em [docs/roteiro_testes_cliente.md](docs/roteiro_testes_cliente.md).

---

## Estrutura

```
├── src/                 # dados, pré-processamento, modelo, algoritmo genético, avaliação, previsão, UI
├── scripts/             # pontos de entrada da linha de comando (python -m scripts.<nome>)
├── streamlit_app.py     # dashboard
├── examples/            # perfis de cliente fictícios
├── tests/               # pytest (raiz e client/) e Playwright (visual/)
├── docs/                # análise, resultados, roteiro de testes, artigo e apresentação
├── data/                # instruções para obter o CSV (data/raw/ fica fora do Git)
└── static/              # fonte Familjen Grotesk (SIL OFL 1.1)
```

## Documentação

- [Análise exploratória](docs/analise_exploratoria.md): 26,54% de churn e 11 valores ausentes em `TotalCharges`, todos com `tenure = 0`
- [Resultados experimentais](docs/resultados_experimentais.md): métricas completas, matrizes de confusão e discussão
- [Artigo (PDF, padrão SBC)](docs/artigo/artigo-n3.pdf): fundamentação teórica e metodologia
- [Roteiro de testes do painel Cliente](docs/roteiro_testes_cliente.md)

## Limitações

- Os resultados vêm de **uma única divisão** dos dados e de **uma execução** da busca, então podem mudar com outras sementes.
- As associações encontradas entre características e churn **não indicam causalidade**.
- No dataset, `gender` tem apenas `Male` e `Female`. A aplicação mantém essas duas categorias para que o experimento seja reprodutível, mas elas não representam todas as identidades de gênero e não permitem avaliar o modelo para outros grupos. Veja a [nota metodológica](docs/artigo/nota-representatividade.md) e o [texto para a apresentação](docs/apresentacao/limites-dos-dados.md).
