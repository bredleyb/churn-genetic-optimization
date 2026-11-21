# Otimização da identificação de cancelamento de clientes com algoritmo genético

Projeto acadêmico N3 de Aprendizagem de Máquina.

## Objetivo

Investigar se a seleção de características por **algoritmo genético** modifica o desempenho e a complexidade de um classificador supervisionado para identificar cancelamento de clientes (*customer churn*), em comparação com o mesmo classificador utilizando todas as características elegíveis.

## Dados

Dataset inicialmente definido: [Telco Customer Churn (Kaggle — blastchar)](https://www.kaggle.com/datasets/blastchar/telco-customer-churn). O arquivo ainda não foi importado ou analisado no projeto. A fonte e o esquema serão verificados na etapa de preparação.

## Método proposto

- Construir um classificador de referência (*baseline*) com todas as características elegíveis.
- Empregar algoritmo genético para selecionar um subconjunto de características.
- Treinar o mesmo classificador sobre as características selecionadas.
- Comparar os modelos com um protocolo consistente de validação e métricas de classificação.
- Permitir previsão para um novo perfil de cliente.

**Situação:** planejamento concluído; implementação e resultados experimentais pendentes. Este README será atualizado com instruções de execução e resultados reais antes de 27/11/2026.

## Entregas

| Data | Entregável |
| --- | --- |
| 23/11/2026 | Artigo acadêmico em formato SBC |
| 27/11/2026 | Repositório completo e link entregue à professora |
| 30/11/2026 | Apresentação e demonstração |

## Documentação

- [`docs/GUIA_MESTRE_PROJETO_N3.md`](docs/GUIA_MESTRE_PROJETO_N3.md): requisitos, metodologia planejada, limitações, cronograma e rastreabilidade.
- [`docs/artigo/`](docs/artigo/): fontes LaTeX para o artigo SBC e instruções de uso no Overleaf.

## Execução

A implementar após a etapa de desenvolvimento. Nenhum modelo foi treinado até o momento.

## Resultados

Aguardando execução e avaliação experimental. Nenhum valor de desempenho é reivindicado nesta versão.