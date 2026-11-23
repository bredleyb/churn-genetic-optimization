# Resultados experimentais — previsão de cancelamento de clientes

## Procedimento

A comparação foi realizada com o conjunto [Telco Customer Churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn), contendo 7.043 registros e 19 características candidatas. A variável `Churn = Yes` foi considerada a classe positiva.

A divisão estratificada, com semente aleatória 42, reservou 5.634 registros (80%) para desenvolvimento e 1.409 (20%) para teste. O conjunto de teste contém 374 cancelamentos e 1.035 permanências. A regressão logística foi utilizada nos dois modelos, com o mesmo pré-processamento: imputação de valores ausentes, codificação *one-hot* para categorias e padronização de variáveis numéricas. A preparação foi ajustada exclusivamente nos dados de treinamento.

A busca genética utilizou 24 indivíduos, 15 gerações, torneios de três indivíduos, probabilidade de cruzamento de 0,8, probabilidade de mutação por indivíduo de 0,2, inversão de cada bit com probabilidade de `1/19`, elitismo de um indivíduo e penalização `λ = 0,02`. A aptidão combinou o F1-score médio obtido em validação cruzada estratificada de três partições com a penalização por quantidade de características. A seleção ocorreu somente nos dados de desenvolvimento.

Após a escolha do subconjunto, ambos os modelos foram ajustados aos 5.634 registros de desenvolvimento e avaliados no mesmo conjunto de teste, usando o limiar padrão de classificação da regressão logística.

## Comparação dos modelos

| Métrica no teste | Regressão logística (19 características) | Regressão logística com seleção genética (9 características) |
|---|---:|---:|
| F1-score | **0,6040** | 0,5869 |
| Precisão | **0,6572** | 0,6463 |
| Revocação | **0,5588** | 0,5374 |
| Acurácia | **0,8055** | 0,7991 |
| ROC-AUC | **0,8419** | 0,8401 |

### Matriz de confusão

| Tipo de resultado | Referência | Seleção genética |
|---|---:|---:|
| Verdadeiros negativos | 926 | 925 |
| Falsos positivos | 109 | 110 |
| Falsos negativos | 165 | 173 |
| Verdadeiros positivos | 209 | 201 |

Os **falsos negativos** correspondem a clientes que cancelaram e foram classificados como permanentes. O modelo com seleção genética deixou de identificar oito cancelamentos adicionais em relação ao classificador com todas as características. Também apresentou um falso positivo a mais.

## Características selecionadas

O algoritmo genético selecionou nove das 19 características originais, uma **redução de 52,63%**:

- `SeniorCitizen`
- `tenure`
- `MultipleLines`
- `InternetService`
- `OnlineBackup`
- `Contract`
- `PaperlessBilling`
- `PaymentMethod`
- `TotalCharges`

O F1-score médio da regressão logística de referência na validação cruzada foi **0,5952**. O subconjunto escolhido pelo algoritmo genético apresentou F1-score médio de **0,6059** na validação utilizada durante a busca, com aptidão **0,596442** após penalização. Foram avaliados **121 subconjuntos distintos** ao longo das 15 gerações. A execução da busca levou **9,689 segundos** no ambiente utilizado; o tempo depende do computador e da versão das bibliotecas.

## Discussão

O modelo com todas as características apresentou o maior F1-score no teste. A seleção genética reduziu a quantidade de variáveis por mais da metade, acompanhada de uma redução absoluta de **0,0172** no F1-score e de **0,0214** na revocação. A diferença de ROC-AUC foi pequena, aproximadamente **0,0018**.

Durante a validação, a combinação escolhida pelo algoritmo genético obteve F1-score superior ao da referência. Essa vantagem não se repetiu no teste reservado. A busca avalia sucessivamente muitos subconjuntos sobre a validação e pode favorecer combinações que se ajustam às suas particularidades; por isso, o teste separado é importante para interpretar o resultado.

Os resultados evidenciam um compromisso entre a simplificação das entradas do modelo e a identificação de cancelamentos. A escolha prática entre os modelos dependeria do custo de coletar as características e das consequências de não identificar um cliente propenso a cancelar.

Este experimento utilizou uma única divisão dos dados e uma execução da busca genética. Os resultados podem variar com outras sementes e amostras. O conjunto de dados também representa uma situação específica; associações entre características e cancelamento não demonstram causalidade.

## Limitações de representatividade

A coluna `gender` do Telco Customer Churn apresenta exclusivamente `Female` e `Male`, categorias reproduzidas como Feminino e Masculino na interface. Essa delimitação binária corresponde ao esquema do dataset e não contempla outras identidades de gênero. Não é possível avaliar a qualidade ou a equidade das previsões para categorias não representadas. O modelo de referência utiliza as 19 características originais, incluindo `gender`; o algoritmo genético selecionou nove características e excluiu `gender` de seu subconjunto final. Isso não elimina a limitação de representatividade do conjunto de dados utilizado para treinar e avaliar a solução.

## Reprodução

Com o CSV original salvo em `data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv` e as dependências instaladas, execute a partir da raiz do repositório:

```powershell
python -m scripts.compare_models
```

O comando gera `results/comparacao_modelos.json`, `results/comparacao_modelos.md`, `results/baseline.joblib` e `results/genetic.joblib`. Esses arquivos são produzidos localmente; o código e os parâmetros necessários à reprodução estão no repositório.
