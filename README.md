# Seleção de Características com Algoritmo Genético para Previsão de Cancelamento de Clientes

Projeto de Aprendizagem de Máquina desenvolvido por Bredley Bauer, Gabriel Coelho e Gustavo Haiduk Pereira.

## Objetivo

Investigar o uso de um algoritmo genético na seleção de características para prever o cancelamento de clientes (*customer churn*). O estudo compara uma regressão logística com todas as características elegíveis e o mesmo classificador treinado com um subconjunto selecionado pelo algoritmo genético.

A solução é voltada à análise de clientes de serviços recorrentes, especialmente telecomunicações.

## Dados

O conjunto [Telco Customer Churn (Kaggle — blastchar)](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) contém 7.043 registros e 21 colunas. Após excluir `customerID` (identificador) e `Churn` (resposta), restam 19 características candidatas.

O arquivo CSV deve ser obtido na fonte indicada e colocado em `data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv`. Consulte [data/README.md](data/README.md). Os dados brutos permanecem fora do versionamento.

## Preparação dos dados

A leitura valida o esquema, codifica `Churn` como 1 (cancelamento) e 0 (permanência) e converte `TotalCharges` para numérico. A variável `SeniorCitizen` é tratada como categórica, preservando a distinção entre código binário e grandeza numérica.

A divisão dos dados é estratificada, com 80% para desenvolvimento e 20% para teste (`random_state=42`). Os procedimentos que aprendem parâmetros são definidos em um `ColumnTransformer`:

- **Numéricos (`tenure`, `MonthlyCharges`, `TotalCharges`):** imputação pela mediana e padronização.
- **Categóricos (16 colunas):** imputação pela categoria mais frequente e codificação one-hot, ignorando categorias desconhecidas na transformação.

O transformador é criado sem ajuste prévio; sua estimação deverá ocorrer dentro de cada partição de treinamento da validação cruzada. A seleção genética opera sobre as 19 características originais, incluindo integralmente o grupo one-hot quando uma característica categórica é selecionada.

## Executar a análise exploratória

Requer Python 3.10 ou superior. No PowerShell, a partir da raiz do repositório:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m scripts.analyze_data --data data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv
```

O comando gera `results/analise_dados.json` e `results/analise_dados.md`, com estatísticas agregadas de qualidade, distribuição de classes e cancelamentos por contrato e tipo de conexão. Pode-se alterar o destino por `--output outro-diretorio`.

Para executar os testes automatizados:

```powershell
python -m pytest -q
```

O código de preparação está em `src/data.py`, o transformador reutilizável está em `src/preprocessing.py` e os indicadores exploratórios estão em `src/analysis.py`.

## Análise exploratória

A inspeção do CSV identificou **1.869 cancelamentos (26,54%)**, **5.174 permanências (73,46%)**, nenhum identificador duplicado e **11 valores ausentes em `TotalCharges`**, todos com `tenure = 0`. Esses registros são preservados para imputação durante o treinamento. Os indicadores descritivos e as justificativas estão em [docs/analise_exploratoria.md](docs/analise_exploratoria.md).

## Metodologia do experimento

O estudo compara a regressão logística de referência com a mesma técnica após a seleção de atributos por algoritmo genético. A função de aptidão considera o F1-score médio em validação cruzada estratificada e uma penalização proporcional à quantidade de características. O conjunto de teste será utilizado exclusivamente na avaliação final dos modelos.

## Artigo

O [artigo acadêmico em PDF](docs/artigo/artigo-n3.pdf) segue o padrão da Sociedade Brasileira de Computação (SBC). Os arquivos-fonte estão disponíveis em [main.tex](docs/artigo/main.tex) e [referencias.bib](docs/artigo/referencias.bib). A compilação utiliza os arquivos oficiais `sbc-template.sty` e `sbc.bst` do [SBC Conferences Template](https://www.overleaf.com/latex/templates/sbc-conferences-template/blbxwjwzdngr).
