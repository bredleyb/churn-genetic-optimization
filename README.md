# Seleção de Características com Algoritmo Genético para Previsão de Cancelamento de Clientes

Projeto de Aprendizagem de Máquina desenvolvido por Bredley Bauer, Gabriel Coelho e Gustavo Haiduk Pereira.

## Objetivo

Investigar o uso de um algoritmo genético na seleção de características para prever o cancelamento de clientes (*customer churn*). O estudo compara o desempenho de um classificador treinado com todas as variáveis elegíveis ao de outro, da mesma arquitetura, treinado com um subconjunto selecionado pelo algoritmo genético.

A aplicação considera o uso de previsões por equipes de análise e retenção de clientes de serviços recorrentes.

## Conjunto de dados

O estudo utiliza como referência o [Telco Customer Churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn), disponibilizado no Kaggle. A base reúne informações sobre contratos, serviços contratados, cobranças e permanência de clientes de telecomunicações, além da variável-alvo `Churn`, que indica o cancelamento do serviço.

## Metodologia

A abordagem descrita no artigo compreende:

1. Exploração dos dados e preparação das variáveis numéricas e categóricas.
2. Treinamento de um modelo de referência por regressão logística.
3. Seleção de características por algoritmo genético, com cromossomos binários e função de aptidão baseada em F1-score de validação cruzada e penalização pela quantidade de atributos.
4. Treinamento e avaliação comparativa dos modelos com e sem seleção genética, utilizando um conjunto de teste reservado.
5. Previsão de cancelamento para uma nova entrada por meio de um script Python.

A avaliação considera F1-score, precisão, revocação, matriz de confusão, redução de atributos e custo computacional da busca genética.

## Artigo

O artigo acadêmico utiliza o padrão da Sociedade Brasileira de Computação (SBC):

- [Texto-fonte em LaTeX](docs/artigo/main.tex)
- [Referências bibliográficas em BibTeX](docs/artigo/referencias.bib)

Para compilação, os arquivos devem ser utilizados com os estilos `sbc-template.sty` e `sbc.bst` do [SBC Conferences Template](https://www.overleaf.com/latex/templates/sbc-conferences-template/blbxwjwzdngr).
