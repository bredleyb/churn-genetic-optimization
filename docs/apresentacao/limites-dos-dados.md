# Conteúdo para apresentação — limites do conjunto de dados

## Slide: Representatividade e limitações

**Variável `gender` — delimitação do Telco Customer Churn**

- O dataset fornece apenas as categorias `Male` e `Female`.
- A interface apresenta Masculino e Feminino para corresponder às categorias originais.
- Outras identidades de gênero não estão representadas nos dados; não é possível avaliar o desempenho dos modelos nesses grupos.
- O modelo de referência usa as 19 características; o genético selecionou nove, sem incluir `gender`. O limite da amostra continua relevante.

**Comentário oral sugerido:** “O formulário mantém as categorias de gênero presentes na base de treinamento para reproduzir fielmente o experimento. Sabemos que essas duas categorias não abrangem todas as identidades de gênero. Por isso, reconhecemos essa restrição como uma limitação do conjunto de dados e evitamos extrapolar os resultados para grupos que não foram representados.”

**Referências internas:** [Fonte e análise exploratória](../analise_exploratoria.md) e [limitações dos resultados](../resultados_experimentais.md).

Este arquivo fornece o texto do slide e da fala. O repositório ainda não contém um arquivo de apresentação editável a atualizar.
