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

O transformador é criado sem ajuste prévio e ajustado dentro de cada partição de treinamento da validação cruzada. A seleção genética opera sobre as 19 características originais, incluindo integralmente o grupo one-hot quando uma característica categórica é selecionada.

## Instalação e execução

Requer Python 3.10 ou superior. No PowerShell, a partir da raiz do repositório:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m scripts.analyze_data
python -m scripts.compare_models
python -m scripts.predict --cliente examples/cliente_exemplo.json
```

O comando de análise gera `results/analise_dados.json` e `results/analise_dados.md`, com estatísticas agregadas de qualidade, distribuição de classes e cancelamentos por contrato e tipo de conexão. Pode-se alterar o destino por `--output outro-diretorio`.

Para executar os testes automatizados:

```powershell
python -m pytest -q
```

O código de preparação está em `src/data.py`, o transformador reutilizável está em `src/preprocessing.py` e os indicadores exploratórios estão em `src/analysis.py`.

## Análise exploratória

A inspeção do CSV identificou **1.869 cancelamentos (26,54%)**, **5.174 permanências (73,46%)**, nenhum identificador duplicado e **11 valores ausentes em `TotalCharges`**, todos com `tenure = 0`. Esses registros são preservados para imputação durante o treinamento. Os indicadores descritivos e as justificativas estão em [docs/analise_exploratoria.md](docs/analise_exploratoria.md).

## Metodologia do experimento

O estudo compara a regressão logística de referência com a mesma técnica após a seleção de atributos por algoritmo genético. A função de aptidão considera o F1-score médio em validação cruzada estratificada e uma penalização proporcional à quantidade de características. O conjunto de teste é utilizado exclusivamente na avaliação final dos modelos.

## Classificador de referência

A regressão logística utiliza todas as 19 características originais, com imputação,
*one-hot encoding* e padronização dentro de um único pipeline do scikit-learn.
A avaliação é feita com validação cruzada estratificada em três partições somente
nos 80% reservados ao desenvolvimento. O conjunto de teste (20%) permanece
intocado para a comparação final com a seleção genética.

Após obter o CSV e instalar as dependências, execute:

```powershell
python -m scripts.train_baseline
```

O comando apresenta as médias e os desvios-padrão de F1-score, precisão,
revocação, acurácia e ROC-AUC. Também salva o relatório de validação cruzada em
`results/baseline_cv.json` e o classificador treinado em
`results/baseline.joblib`. Esses arquivos são gerados localmente e podem ser
reproduzidos pelo comando acima. O classificador permanece disponível para a
comparação posterior com as características selecionadas pelo algoritmo genético.

## Seleção de características por algoritmo genético

O algoritmo genético representa as 19 características originais como um
cromossomo binário. Cada bit indica se a característica será utilizada na
regressão logística. A aptidão combina o F1-score médio em validação cruzada
estratificada (três partições) e uma penalização proporcional à quantidade de
características. O conjunto de teste permanece reservado para a comparação final.

A configuração padrão utiliza 24 indivíduos, 15 gerações, seleção por torneio
de três participantes, cruzamento de um ponto (probabilidade 0,8), mutação por
indivíduo (probabilidade 0,2, seguida de inversão de cada bit com chance de `1/d`),
elitismo de um indivíduo e penalização `λ = 0,02`. A busca utiliza semente 42,
impede cromossomos vazios e reutiliza avaliações de subconjuntos já calculadas.

Com o CSV na pasta indicada, execute:

```powershell
python -m scripts.run_genetic
```

O comando apresenta o desempenho do melhor indivíduo de cada geração, salva
`results/genetic_selection.json` com a seleção e o histórico da busca e treina
`results/genetic.joblib` com o subconjunto selecionado, usando os dados de
desenvolvimento. Os arquivos podem ser reproduzidos pelo comando acima.

É possível verificar o funcionamento com uma execução reduzida:

```powershell
python -m scripts.run_genetic --population 6 --generations 2
```

O experimento principal utiliza os parâmetros padrão.

## Comparação dos modelos

A avaliação final utiliza a mesma divisão estratificada para os dois modelos.
A regressão logística de referência e a busca genética são ajustadas apenas
com os dados de desenvolvimento. Depois da seleção, os dois classificadores
são treinados novamente nesses dados e avaliados no mesmo conjunto de teste.

```powershell
python -m scripts.compare_models
```

O comando apresenta o F1-score de cada modelo e registra em `results/`:

- `comparacao_modelos.md`: tabela de métricas, matrizes de confusão, atributos
  selecionados e limitações da avaliação;
- `comparacao_modelos.json`: métricas e parâmetros para reprodução;
- `baseline.joblib` e `genetic.joblib`: classificadores treinados.

O relatório apresenta F1-score, precisão, revocação, acurácia e ROC-AUC, além
da quantidade de características e do tempo da busca genética. A análise
interpreta falsos positivos e falsos negativos. Os arquivos de `results/` são
gerados localmente e ficam fora do versionamento; os resultados experimentais estão descritos na seção seguinte.

## Resultados experimentais

A comparação foi executada com os 7.043 registros do conjunto Telco Customer Churn, mantendo 20% dos dados reservados para teste. A seleção genética reduziu o número de características originais de 19 para 9 (52,63%). No conjunto de teste, a regressão logística completa alcançou **F1-score de 0,6040** e o modelo com seleção genética obteve **0,5869**. A redução das variáveis foi acompanhada de uma pequena perda de desempenho preditivo.

As demais métricas, matrizes de confusão, características selecionadas e limitações estão descritas em [Resultados experimentais](docs/resultados_experimentais.md).

## Demonstração com um novo cliente

O script de previsão recebe um cliente em formato JSON, valida as 19 características
originais e utiliza os classificadores treinados para indicar cancelamento ou
permanência, acompanhados da probabilidade estimada de cancelamento.

Após executar `python -m scripts.compare_models` para gerar os modelos na pasta
`results/`, utilize um dos perfis de exemplo:

```powershell
python -m scripts.predict --cliente examples/cliente_exemplo.json
python -m scripts.predict --cliente examples/cliente_exemplo_2.json
```

Por padrão, o programa mostra as previsões **dos dois modelos** para o mesmo
cliente. É possível selecionar apenas um:

```powershell
python -m scripts.predict --cliente examples/cliente_exemplo.json --modelo genetico
python -m scripts.predict --cliente examples/cliente_exemplo.json --modelo baseline
```

Para testar outro perfil, faça uma cópia de um dos JSONs em `examples/` e altere os
valores das características. Os nomes e as categorias seguem o dataset original;
`tenure` indica meses, `MonthlyCharges` e `TotalCharges` são valores numéricos,
e `SeniorCitizen` utiliza 0 ou 1. `TotalCharges` também aceita `null`, tratado
pela imputação do modelo. Os exemplos são fictícios e não possuem `customerID`
nem a resposta `Churn`.

Na execução dos modelos utilizados no experimento, `cliente_exemplo.json` recebeu
previsão de **cancelamento** (82,04% na referência e 76,66% no genético). O perfil
`cliente_exemplo_2.json` recebeu previsão de **permanência** (0,37% e 0,71% de
probabilidade de cancelamento, respectivamente).

Os percentuais representam estimativas dos classificadores para esses perfis, não
garantias individuais de cancelamento. Os modelos `.joblib` são gerados localmente
e devem ser carregados apenas quando provenientes do próprio treinamento do projeto.

## Interface de demonstração

A interface local permite selecionar um perfil fictício, editar as 19 características
originais e comparar as probabilidades estimadas pelos dois modelos. Os campos
dependentes de telefonia e internet são ajustados quando o serviço correspondente
é alterado. O desempenho no teste é lido de `results/comparacao_modelos.json`.

Após instalar as dependências e gerar os modelos com `python -m scripts.compare_models`,
execute na raiz do projeto:

```powershell
python -m streamlit run streamlit_app.py
```

A interface abre no navegador e funciona localmente, sem publicar dados na internet.
Se os modelos ainda não tiverem sido treinados, o programa informa o comando
necessário. A demonstração pelo terminal, em `scripts/predict.py`, continua
disponível.

## Artigo

O [artigo acadêmico em PDF](docs/artigo/artigo-n3.pdf) apresenta a fundamentação
teórica e a metodologia do estudo, seguindo o padrão da Sociedade Brasileira
de Computação (SBC).
