# Complemento metodológico para o artigo N3 — representatividade do dataset

O artigo acadêmico foi publicado no repositório como `artigo-n3.pdf`, sem arquivo-fonte editável versionado. Este texto registra a observação metodológica a ser integrada à discussão de limitações em uma revisão do documento.

## Redação para a seção de limitações

A característica `gender` do conjunto Telco Customer Churn contém exclusivamente as categorias `Male` e `Female`, reproduzidas na interface como Masculino e Feminino. Essa classificação binária corresponde à estrutura original dos dados e não contempla outras identidades de gênero, limitando a representatividade da amostra. Dessa forma, o experimento não permite avaliar o comportamento dos modelos para grupos ausentes do conjunto de treinamento e teste. O classificador de referência considera as 19 características originais; a seleção genética reduziu esse conjunto a nove e não incluiu `gender` no subconjunto final. A exclusão dessa variável do segundo classificador não elimina a restrição de representatividade dos dados empregados no estudo.

## Consistência editorial

- Manter o número de características candidatas em 19 e o subconjunto selecionado em nove, conforme os resultados já reproduzidos.
- Conservar `Male`/`Female` como categorias registradas no dataset; evitar atribuir a elas uma representação completa das identidades de gênero.
- Distinguir limitação de representatividade dos dados de conclusões de desempenho: não há avaliação por outras identidades.
- O site e os classificadores continuam operando com as mesmas categorias e resultados experimentais.
