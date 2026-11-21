# Análise exploratória — Telco Customer Churn

## Fonte e características

O conjunto [Telco Customer Churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) apresenta informações sobre 7.043 clientes de telecomunicações. A análise foi reproduzida com o arquivo CSV do conjunto original, seguindo o procedimento descrito neste repositório.

A base possui 21 colunas: `customerID`, `Churn` e 19 características candidatas. O cancelamento (`Churn = Yes`) é a classe positiva.

## Qualidade e distribuição das classes

| Indicador | Resultado |
|---|---:|
| Registros | 7.043 |
| Colunas | 21 |
| Identificadores duplicados | 0 |
| Registros integralmente duplicados | 0 |
| Valores ausentes em `TotalCharges` | 11 |
| Desses, com `tenure = 0` | 11 |
| Cancelaram (`Yes`) | 1.869 (26,54%) |
| Permaneceram (`No`) | 5.174 (73,46%) |

As demais colunas não apresentam valores vazios no arquivo analisado. A classe positiva é minoritária, o que fundamenta o uso de F1-score, precisão e revocação durante a avaliação.

## Distribuições descritivas

| Variável numérica | Mínimo | Mediana | Média | Máximo | Observações válidas |
|---|---:|---:|---:|---:|---:|
| `tenure` | 0 | 29 | 32,37 | 72 | 7.043 |
| `MonthlyCharges` | 18,25 | 70,35 | 64,76 | 118,75 | 7.043 |
| `TotalCharges` | 18,80 | 1.397,30 | 2.283,30 | 8.684,80 | 7.032 |

**Cancelamentos por tipo de contrato**

| Contrato | Clientes | Cancelamentos | Taxa de cancelamento |
|---|---:|---:|---:|
| Mensal (`Month-to-month`) | 3.875 | 1.655 | 42,71% |
| Anual (`One year`) | 1.473 | 166 | 11,27% |
| Bienal (`Two year`) | 1.695 | 48 | 2,83% |

**Cancelamentos por serviço de internet**

| Serviço | Clientes | Cancelamentos | Taxa de cancelamento |
|---|---:|---:|---:|
| Fibra óptica (`Fiber optic`) | 3.096 | 1.297 | 41,89% |
| DSL | 2.421 | 459 | 18,96% |
| Sem internet (`No`) | 1.526 | 113 | 7,40% |

As diferenças entre os grupos descrevem associações observadas na base e não estabelecem relações causais.

## Tratamentos e justificativas

| Tratamento | Justificativa |
|---|---|
| Excluir `customerID` das características | É um identificador sem conteúdo preditivo pertinente ao problema. |
| Codificar `Churn`: `Yes → 1`, `No → 0` | Estabelece a classe positiva de cancelamento. |
| Converter `TotalCharges` para numérico e manter seus 11 valores ausentes | Valores em branco não representam cobrança igual a zero; preserva os registros para imputação. |
| Tratar `SeniorCitizen` como variável categórica | Seus valores 0/1 representam categorias, não uma grandeza contínua. |
| Imputar numéricos pela mediana e categóricos pela moda | Permite utilizar observações com valores ausentes sem remover registros. |
| Aplicar one-hot e padronização em pipelines | Adapta os tipos de atributos à regressão logística e evita aprender parâmetros fora do treino. |
| Dividir em 80% desenvolvimento e 20% teste, de forma estratificada | Reserva um conjunto independente para a comparação final. |
| Selecionar atributos antes do one-hot | Cada gene do algoritmo genético representa uma característica original. |

As imputações, a padronização e a codificação serão ajustadas somente nos exemplos de treinamento de cada partição da validação cruzada. A seleção genética e a escolha dos parâmetros do modelo utilizarão exclusivamente os dados de desenvolvimento.

## Reprodução

Depois de obter o arquivo `WA_Fn-UseC_-Telco-Customer-Churn.csv` e colocá-lo em `data/raw/`, execute:

```powershell
python -m scripts.analyze_data
```

O script gera relatórios agregados em JSON e Markdown e verifica a divisão estratificada dos dados. Os perfis são descritivos; os resultados da avaliação dos modelos estão disponíveis em [Resultados experimentais](resultados_experimentais.md).
