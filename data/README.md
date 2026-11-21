# Conjunto de dados

O projeto utiliza [Telco Customer Churn — blastchar (Kaggle)](https://www.kaggle.com/datasets/blastchar/telco-customer-churn), baseado em dados de exemplo da IBM.

1. Acesse a página do conjunto de dados e faça o download do CSV `WA_Fn-UseC_-Telco-Customer-Churn.csv`.
2. Crie a pasta `data/raw/`, se necessário.
3. Salve o CSV original em `data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv`, mantendo o nome das colunas.

O arquivo original possui 7.043 registros e 21 colunas. O CSV não é versionado no Git; os relatórios agregados podem ser reproduzidos a partir dele.

A preparação preserva os registros com `TotalCharges` vazio. A imputação ocorrerá somente no pipeline dos modelos, sem utilizar informações do conjunto de teste na estimação dos parâmetros.
