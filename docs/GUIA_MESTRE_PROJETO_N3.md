# GUIA MESTRE — PROJETO N3: OTIMIZAÇÃO DA IDENTIFICAÇÃO DE CHURN COM ALGORITMO GENÉTICO

> **Documento operacional para assistentes de IA e para orientar a implementação integral do projeto.**
> **Atualizado em:** 21/11/2026, horário de Brasília (UTC−03:00).
> **Estado:** planejamento consolidado; artigo, repositório e implementação ainda não foram confirmados como concluídos.
> **Fonte normativa inspecionada:** `Orientacao_projeto_N3.docx` (2 páginas, cabeçalho “Projeto N3”).
> **Entregáveis acordados:** artigo em 23/11 no **padrão SBC (Sociedade Brasileira de Computação)**; GitHub completo em 27/11; apresentação em 30/11.
> **Critério de leitura:** cada declaração é identificada por sua origem e seu grau de fixação. **Não atribuir à professora requisitos decididos pelo projeto.**

---

## 0. INSTRUÇÕES DE OPERAÇÃO PARA A IA — LEITURA PRIORITÁRIA

Este arquivo é a **referência central de continuidade**. O usuário não pretende lê-lo manualmente: sua utilidade é guiar a IA, evitar perda de contexto e permitir prosseguir com commits reais, entregáveis e avaliação metodológica.

### 0.1. Hierarquia de fontes e conflitos

1. **[ORIENTAÇÃO]** Texto literal/conteúdo do Word `Orientacao_projeto_N3.docx`, inclusive rubrica: autoridade máxima para requisitos oficiais escritos.
2. **[CONFIRMAÇÃO DA PROFESSORA VIA USUÁRIO]** Informações comunicadas pelo usuário após conversar com a professora: em especial, há **artigo/texto acadêmico a entregar em 23/11/2026**. Trata-se de requisito confirmado pela conversa, embora não esteja explicitado como prazo no Word.
3. **[REQUISITO DO USUÁRIO]** O artigo deve usar o **formato SBC brasileiro**, especificamente o modelo LaTeX de artigos de conferência da Sociedade Brasileira de Computação; a exigência de formato foi adicionada pelo usuário em 21/11/2026. Ela não consta do Word.
4. **[DECISÃO DO PROJETO]** Tema, abordagem técnica e fluxo incremental acordados pelo usuário.
5. **[PLANO TÉCNICO]** Arquitetura, parâmetros, caminhos, métricas e estratégias aqui sugeridos para execução. Podem mudar por evidência de testes, disponibilidade e limitações de prazo, sem violar os níveis anteriores.
6. **[PENDÊNCIA]** Informação ainda não confirmada: não presumir resposta nem inventar regra institucional.
Em caso de divergência, apontar o conflito e seguir a fonte de maior precedência. Uma decisão posterior do usuário pode atualizar decisões do projeto; somente instruções legítimas da professora podem alterar exigências oficiais.

### 0.2. Protocolo obrigatório em cada retomada da conversa

1. Ler este guia e a orientação original, quando disponíveis; consultar os últimos acordos no chat.
2. Identificar **data**, **entrega mais próxima**, **último commit real**, **arquivos existentes** e **etapas marcadas como concluídas**, sem supor que arquivos planejados já existem.
3. Se houver repositório conectado, verificar arquivos e histórico; se houver cópia local do repositório, inspecioná-la. **Não inventar links GitHub, commits, resultados, autorias ou datas de envio.**
4. Escolher a próxima unidade mínima verificável; implementar, testar e documentar; somente então propor/registrar o commit.
5. Atualizar as seções `Estado do projeto`, `Registro de decisões` e `Rastreabilidade` neste guia quando qualquer compromisso ou evidência mudar.
6. Respeitar sempre os três marcos: **artigo 23/11 → código completo e link 27/11 → apresentação 30/11**.
7. Nunca afirmar um benefício empírico do AG sem executar o experimento.
8. Não criar burocracia: **sem pull requests e sem wiki complexa**; usar uma branch `main` inicialmente, commits progressivos e README conciso.
9. Diferenciar **código desenvolvido**, **código executado/testado**, **resultado observado** e **resultado esperado**. A validade acadêmica depende dessa separação.
10. Em mudanças técnicas, atualizar artigo/README quando a metodologia formalizada deixar de refletir o código.

### 0.3. Vocabulário de status

- `[PENDENTE]`: não há evidência de execução.
- `[EM ANDAMENTO]`: iniciado, com trabalho remanescente.
- `[CONCLUÍDO]`: há arquivo/commit/resultado verificável.
- `[BLOQUEADO]`: depende de decisão ou recurso ausente.
- `[NÃO APLICÁVEL]`: etapa legitimamente retirada, com justificativa.

Não marcar `[CONCLUÍDO]` apenas porque esta especificação descreve a etapa.

---

## 1. FATOS CONFIRMADOS, ESCOPO E DEFINIÇÕES

### 1.1. Identidade e propósito

- **Tipo de atividade [ORIENTAÇÃO]:** Projeto N3 final de Aprendizagem de Máquina, desenvolvido em grupo, do preparo dos dados à demonstração de uso.
- **Problema [DECISÃO]:** otimização da identificação de clientes propensos ao cancelamento de serviços (*customer churn*).
- **Método em destaque [DECISÃO]:** algoritmo genético (AG).
- **Aplicação do AG [DECISÃO]:** selecionar subconjunto de características que serão fornecidas a um **classificador supervisionado**. O classificador é treinado de modo convencional; o AG realiza a **otimização combinatória de atributos**.
- **Dataset de referência inicial [PLANO ACORDADO, A CONFIRMAR NO ARQUIVO REAL]:** IBM Telco Customer Churn, publicado no Kaggle pelo usuário `blastchar`: https://www.kaggle.com/datasets/blastchar/telco-customer-churn .
- **Pergunta experimental [DECISÃO]:** “Em que medida a seleção de características por algoritmo genético modifica o desempenho e a complexidade de um classificador de cancelamento de clientes, em comparação com o mesmo classificador sem seleção genética?”
- **Hipótese a investigar [DECISÃO]:** o AG pode obter um subconjunto menor de variáveis com desempenho preditivo semelhante ou superior ao baseline. **Hipótese não equivale a resultado.**
- **Público potencial:** analistas e equipes de relacionamento/retenção de empresas prestadoras de serviços recorrentes, especialmente telecomunicações. Trata-se de cenário hipotético acadêmico, sem integração com empresa real.
- **Uso concreto demonstrável:** informar os atributos de um cliente e receber indicação/previsão de cancelamento em linguagem compreensível.
- **Desenvolvimento [DECISÃO]:** incremental e documentado com commits ao longo de vários dias; uma única branch `main` é suficiente; PR, wiki, CI complexa, sprints formais e deploy público não são obrigatórios.
- **Linguagem/framework [PLANO]:** Python, pandas, NumPy, scikit-learn, Matplotlib, joblib; Streamlit apenas se couber no prazo. O Word não impõe tecnologias.

### 1.2. Formulação acadêmica precisa

- **Problema de negócio:** identificar previamente perfis associados à saída de clientes, para apoiar priorização de ações de retenção.
- **Problema computacional:** classificação binária supervisionada, com alvo `Churn ∈ {0,1}`.
- **Subproblema de otimização:** buscar subconjunto `S` das características candidatas para maximizar um critério de validação preditiva e, secundariamente, reduzir a quantidade de variáveis usadas.
- **Modelo de referência (baseline):** mesmo classificador e protocolo, com todas as variáveis elegíveis.
- **Modelo otimizado:** mesmo classificador, treinado com as características escolhidas pelo AG.
- **Saída da demo:** previsão e, se o modelo tiver `predict_proba`, escore estimado de propensão; informar que não há garantia individual ou relação causal.

**Proibição conceitual:** evitar descrever o AG como “algoritmo que prevê sozinho o cancelamento” se a implementação fizer seleção de atributos. O AG é a busca/otimização; o classificador fornece a previsão. Essa explicação deve ser consistente no artigo, no código e na apresentação.

---

## 2. DATAS, DEPENDÊNCIAS E PRIORIDADES

| Data | Fonte | Entrega / evento | Condição de conclusão |
|---|---|---|---|
| 16/11/2026 (segunda; passado) | [ORIENTAÇÃO] | Exercícios desenvolvidos e apresentados em aula; parte dos 2,0 pontos do critério específico | Verificar com o grupo o que ocorreu; não atribuir conclusão sem evidência |
| **23/11/2026 (segunda)** | **[CONFIRMAÇÃO DA PROFESSORA VIA USUÁRIO + REQUISITO DE FORMATO DO USUÁRIO]** | **Artigo/texto acadêmico em LaTeX, padrão SBC** conforme estrutura sugerida pela rubrica e pelo conteúdo do Word | Arquivo escrito coerente, com título, introdução, conceitos/metodologia, considerações finais e referências; envio pelo canal definido pela professora |
| 23/11/2026 (segunda) | [ORIENTAÇÃO] | Segundo dia de exercícios desenvolvidos e apresentados em aula | Tratar como critério separado; confirmar se precisa incorporar material ao artigo |
| **27/11/2026 (sexta)** | **[ORIENTAÇÃO]** | **Link do GitHub com projeto completo** | Código, preparação, treinamento, AG, avaliação, README e nova-entrada funcional disponíveis; link efetivamente enviado até o prazo |
| **30/11/2026 (segunda)** | **[ORIENTAÇÃO]** | **Apresentação do projeto e demonstração** | Explicar escolhas, resultados, limitações e contribuições dos integrantes; demo testada |

**Horários e canais:** não constam da orientação anexada. **Não criar horário limite.** Obter confirmação se necessária, sem bloquear a produção.

**Estratégia temporal [PLANO]:**
- **21–22/11:** fixar modelo metodológico, redigir/revisar artigo, preparar referências. Se for possível, criar repositório e desenvolver esqueleto sem prejudicar o artigo.
- **23/11:** entregar artigo e cumprir exigências presenciais da aula. Registrar status de envio real.
- **24/11:** ingestão/exploração, pré-processamento, baseline, testes iniciais.
- **25/11:** implementar AG, rastrear aptidão e selecionar atributos.
- **26/11:** executar avaliação justa, gerar artefatos de resultados, demo e README final; teste de execução limpa.
- **27/11:** revisar o repositório, finalizar e **enviar link**; o código deve estar completo antes do envio.
- **28–29/11:** ensaio, revisão dos slides e dos papéis dos integrantes, sem depender de novas funcionalidades.
- **30/11:** socialização e demonstração.

O cronograma é uma sugestão operacional, não um prazo adicional da professora. Se houver atraso, preservar primeiro os requisitos técnicos do Word e a demonstração mínima; cortar customizações visuais, modelos extras e recursos opcionais.

---

## 3. EXTRAÇÃO FIEL DA ORIENTAÇÃO — REQUISITOS NÃO NEGOCIÁVEIS

### 3.1. Obrigações textuais do Word [ORIENTAÇÃO]

Documento original: duas páginas, título **“Projeto N3”**; enunciado: desenvolver solução de Aprendizagem de Máquina de problema de interesse, da preparação de dados à demonstração de uso; pode aprofundar aplicação anterior (possibilidade, não exigência).

**Passagens normativas (organizadas por seção):**
- **Problema e dados:** “definir o objetivo, indicar quem poderia utilizar a solução e apresentar a fonte do dataset”.
- **Preparação e modelagem:** “explorar os dados, justificar os tratamentos realizados, treinar o modelo e explicar as principais escolhas”.
- **Avaliação:** “utilizar uma estratégia adequada ao problema, interpretar os resultados e discutir erros e limitações”.
- **Demonstração de uso:** “permitir que uma nova entrada produza um resultado compreensível. Pode ser uma função, um script ou uma interface simples”.
- **GitHub:** “um README.md com objetivo, instruções de execução e principais resultados. Compartilhar o desenvolvimento”.
- **Entrega:** “repositório no GitHub e apresentação com demonstração da solução e contribuição de cada integrante”.
- **Avaliação geral:** coerência entre problema e solução, treinamento e avaliação do modelo, conclusões e apresentação.

### 3.2. Matriz de requisitos obrigatórios [ORIENTAÇÃO]

Os IDs a seguir são **internos**, criados para rastrear cumprimento.

| ID | Obrigação | Evidência de aceite | Local provável | Situação |
|---|---|---|---|---|
| R01 | Solução de Aprendizagem de Máquina | Treinamento + predição de classificador conectada ao problema | `src/models.py`, `train.py` | [PENDENTE] |
| R02 | Objetivo explicitado | Objetivo claro e testável | artigo, README | [PENDENTE] |
| R03 | Possíveis usuários identificados | Público-alvo e uso declarados | artigo, README | [PENDENTE] |
| R04 | Fonte do dataset declarada | Referência Kaggle e arquivo exato | artigo, README, `data/README.md` | [PENDENTE] |
| R05 | Exploração dos dados | Contagens, tipos, nulos, alvo, análises de atributos | `src/data.py`, resultados | [PENDENTE] |
| R06 | Tratamentos justificados | Conversões, codificações, ausência de dados, remoção de ID | artigo, README, código | [PENDENTE] |
| R07 | Modelo treinado e escolhas explicadas | Baseline treinado e versão otimizada integrada | `src/models.py`, `train.py`, README | [PENDENTE] |
| R08 | Estratégia de avaliação adequada | Separação de teste/validação, métricas consistentes | `src/evaluation.py` | [PENDENTE] |
| R09 | Resultados interpretados | Discussão da comparação observada | `results/`, README, apresentação | [PENDENTE] |
| R10 | Erros e limitações discutidos | FP, FN e limitações explicitados | README, resultados, apresentação | [PENDENTE] |
| R11 | Nova entrada produz resultado | Demo aceita cliente não pré-cadastrado | `app.py` ou CLI/função | [PENDENTE] |
| R12 | README objetivo + execução + resultados | Três itens presentes e reproduzíveis | `README.md` | [PENDENTE] |
| R13 | Compartilhar desenvolvimento | Histórico de commits e projeto acessível | GitHub | [PENDENTE] |
| R14 | Entrega de link GitHub completo + apresentação | Link enviado até 27/11 e apresentação em 30/11 | GitHub, entrega | [PENDENTE] |
| R15 | Contribuição de cada integrante | Slide/fala indicando atribuições reais | apresentação | [PENDENTE] |
| R16 | Conclusões/considerações finais | Síntese coerente com experimentos | artigo (provisório), README, slides | [PENDENTE] |
| R17 | Referências | Dataset e referências conceituais/documentação | artigo, README | [PENDENTE] |

### 3.3. Requisito posterior do artigo [CONFIRMAÇÃO]

| ID | Obrigação | Aceite | Situação |
|---|---|---|---|
| A01 | Entregar em **23/11** espécie de **artigo/texto escrito**, seguindo a estrutura assinalada no Word | Texto concluído, revisado e enviado pelo canal real | [PENDENTE] |
| A02 | Usar o **formato LaTeX SBC brasileiro** para o artigo, por exigência posterior do usuário | PDF compilado a partir do template SBC, mantendo padrão gráfico e estrutural | [PENDENTE] |

Importante: o arquivo Word **não declara literalmente** o prazo do artigo em 23/11; esse requisito foi confirmado posteriormente pelo usuário com base na professora. O Word refere-se à **“NOTA FINAL DA APRESENTAÇÃO ESCRITA - COLETIVA”**, reforçando a pertinência de conteúdo escrito, sem fixar extensão, formatação, ABNT, arquivo .docx, número de páginas ou canal de entrega.

### 3.4. Rubrica coletiva — apresentação escrita [ORIENTAÇÃO]

| Critério literal/fiel | Máximo | Consequência prática |
|---|---:|---|
| Pontualidade na entrega do trabalho desenvolvido no Github | **1,0** | Enviar link completo até 27/11 |
| Título, Introdução | **1,5** | Problema, contexto, objetivo, uso e motivação bem formulados |
| Conceitos, organização da atividade e criatividade | **4,0** | Fundamentação do AG, metodologia consistente e exposição organizada |
| Exercícios desenvolvidos e apresentados em aula (16/11 e 23/11) | **2,0** | Critério próprio; requer verificar atividades efetivamente realizadas |
| Considerações finais | **1,0** | Conclusões e limitações; no artigo pré-experimental, tratar como perspectivas fundamentadas |
| Referências | **0,5** | Citar origem e bibliografia adequada |
| **TOTAL** | **10,0** | |

**Regra de interpretação:** a rubrica não detalha a distribuição de seus pontos exclusivamente no artigo e não dá pesos aos dois componentes da nota final. Não prometer notas nem presumir redução automática por escolhas de ferramentas.

### 3.5. Rubrica individual — socialização [ORIENTAÇÃO]

| Critério | Máximo | Preparação |
|---|---:|---|
| Pontualidade na aula | **2,0** | Comparecimento pontual à apresentação |
| Conhecimento / Postura | **8,0** | Domínio do fluxo, justificativas, métricas, falhas e papel pessoal |
| **TOTAL** | **10,0** | |

### 3.6. Limitações e liberdades explícitas/implícitas

- **São obrigatórios:** problema/dataset/usuários/objetivo; exploração, tratamento justificado, treinamento, avaliação e análise; entrada inédita e resposta; GitHub completo/README; apresentação e contribuição de cada integrante; prazos; conclusão e referências na avaliação.
- **O Word permite:** demonstração como **função**, **script** ou **interface simples**. Uma aplicação web sofisticada é opcional.
- **O Word não exige:** tipo específico de algoritmo, número mínimo de gerações, taxa de acerto mínima, framework, cloud, deploy, app web, documentação extensa, PR, wiki, CI/CD, banco de dados, API, dashboard, competição Kaggle, algoritmos múltiplos ou notebooks.
- **Pendências sem resposta documental:** formato e número de páginas do artigo; canal/horário exatos de entrega; número e papéis dos integrantes; natureza dos exercícios em aula; tempo de apresentação; cálculo conjunto das duas notas.

---

## 4. FUNDAMENTAÇÃO TEÓRICA A SER USADA NO ARTIGO E NA APRESENTAÇÃO

> Esta seção combina conhecimento técnico e fontes verificadas. Não é transcrição da orientação. O texto do artigo final deve ser redigido em linguagem acadêmica apropriada e vinculado a bibliografia identificável.

### 4.1. Churn (cancelamento de clientes)

- Churn é a ocorrência de encerramento do vínculo/serviço pelo cliente no período considerado pelo dataset.
- Problema de negócio: a retenção pode demandar priorização, usando características de contrato, tempo de permanência e serviços.
- Problema de dados: exemplos históricos rotulados com `Churn` permitem estimar associação entre características e cancelamento.
- Limite: associação preditiva **não comprova causalidade** nem efetividade de campanhas de retenção.
- A base é um **conjunto de exemplo IBM**, utilizado academicamente; evitar alegar validação em operação real.

### 4.2. Aprendizagem supervisionada / classificação binária

- Par `(X,y)`: `X` reúne características disponíveis no momento da previsão; `y` é o cancelamento observado.
- O classificador aprende parâmetros a partir dos registros rotulados; depois produz `predição ∈ {0,1}` e, se aplicável, probabilidade estimada para novos perfis.
- Exemplo de classificador escolhido como baseline por clareza, interpretabilidade e custo: **regressão logística** (`sklearn.linear_model.LogisticRegression`).
- A comparação central mantém o classificador fixo nos dois cenários; a variável experimental é a **seleção genética de características**.
- Métrica principal a princípio: **F1-score da classe positiva** (`Churn=1`), por combinar precisão e revocação e ser mais informativa que acurácia isolada quando classes possuem frequências distintas.

### 4.3. Seleção de características (*feature selection*)

- Consiste em escolher subconjunto de atributos para reduzir complexidade/redundância e eventualmente melhorar generalização.
- Não pressupor melhora garantida; por vezes atributos removidos continham informação útil, e o AG pode aumentar custo de busca.
- Entre técnicas possíveis estão filtros, seleção sequencial, métodos embutidos e métodos de busca evolutiva. Nosso projeto estuda a última categoria.
- Referência conceitual: Guyon, I.; Elisseeff, A. (2003). *An Introduction to Variable and Feature Selection*. JMLR 3, 1157–1182: https://jmlr.org/papers/v3/guyon03a.html .

### 4.4. Algoritmos genéticos

- Meta-heurísticas de otimização inspiradas em processos evolutivos, envolvendo população, indivíduos/cromossomos, avaliação de aptidão, seleção de reprodutores, cruzamento, mutação e substituição entre gerações.
- **Representação binária:** cromossomo de tamanho `d`; bit `1` inclui um atributo e bit `0` o exclui.
- **Espaço de busca:** com `d` características elegíveis existem `2^d` subconjuntos teóricos (descartando solução vazia, `2^d−1`). Para 19 características iniciais potencialmente elegíveis, são 524.287 subconjuntos não vazios; validar `d` após inspeção do arquivo real.
- **Fitness:** desempenho do classificador treinado apenas com o subconjunto, medido em validação, com eventual penalização leve pelo número de atributos.
- Seleção favorece indivíduos melhores, cruzamento combina genes, mutação oferece diversidade e elitismo pode preservar a melhor solução.
- A otimização é **estocástica**: fixar sementes e registrar configurações; a melhor solução encontrada não é garantia de ótimo global.
- Referência fundacional: Holland, J. H. (1975). *Adaptation in Natural and Artificial Systems*. University of Michigan Press. https://openlibrary.org/books/OL5070129M/Adaptation_in_natural_and_artificial_systems .

### 4.5. A razão técnica de escolher AG neste problema

1. A seleção de um subconjunto de atributos é uma busca combinatória natural para codificação binária.
2. AG consegue buscar combinações de variáveis sem percorrer exaustivamente todas elas.
3. O processo evidencia conceitos de evolução por gerações e função de aptidão, alinhados à avaliação de conceitos/criatividade.
4. É possível comparar diretamente contra um classificador equivalente sem seleção, isolando o efeito do método.
5. Permite relatar também **custo computacional, redução de atributos e variabilidade entre execuções**.

Não utilizar justificativas exageradas do tipo “AG sempre fornece maior precisão” ou “é necessariamente superior a qualquer outro método”. Seu uso deve ser defendido por adequação à tarefa e resultados observados.

### 4.6. Validação e vazamento de dados

- Separar **teste final** antes de qualquer seleção orientada pelo alvo ou ajuste de parâmetros.
- Pré-processamento aprendido (`SimpleImputer`, `StandardScaler`, `OneHotEncoder` quando aprendido) deve ser **ajustado apenas em dados de treino dos respectivos folds**.
- Avaliar cromossomos por validação cruzada **somente no conjunto de desenvolvimento**; não consultar `y_test` para escolher atributos, hiperparâmetros, penalização ou melhor geração.
- Mesmos splits/mesma configuração básica nos dois modelos.
- Teste final é executado uma única vez após congelar as escolhas; não repetir modificações em resposta ao score do teste.
- Referências: documentação oficial scikit-learn — práticas e vazamento https://scikit-learn.org/stable/common_pitfalls.html e validação cruzada https://scikit-learn.org/stable/modules/cross_validation.html .

---

## 5. DATASET: FONTE, ESQUEMA E CRITÉRIOS DE PREPARAÇÃO

### 5.1. Identificação verificada externamente

- **Nome:** Telco Customer Churn / IBM Sample Data Sets.
- **Publicador no Kaggle:** blastchar.
- **Página estável:** https://www.kaggle.com/datasets/blastchar/telco-customer-churn .
- **Nome usual do arquivo:** `WA_Fn-UseC_-Telco-Customer-Churn.csv`.
- **Dimensões publicadas:** **7.043 linhas** e **21 colunas**, sendo `customerID` um identificador, `Churn` o alvo e as **19 restantes** características candidatas antes de análise/remoções adicionais.
- **Natureza:** dados tabulares com características demográficas, contratuais, serviços, cobranças e cancelamento.
- **Licença/direitos de redistribuição:** **não presumir**. Verificar na página Kaggle/termos antes de versionar CSV bruto em repositório público. Preferir inicialmente `data/README.md` com origem e instruções de download; `data/raw/` ignorada pelo Git.

### 5.2. Dicionário inicial de atributos (validar contra arquivo real)

| Coluna | Papel | Tratamento/cautela preliminar |
|---|---|---|
| `customerID` | Identificador | Remover da modelagem; não é atributo substantivo |
| `gender` | Categórico | Codificar; discutir viés/limitação se pertinente |
| `SeniorCitizen` | Binário 0/1 | Definir como categoria/binário ou numérico conscientemente |
| `Partner` | Binário categórico | Codificar |
| `Dependents` | Binário categórico | Codificar |
| `tenure` | Numérico | Quantidade de meses como cliente; considerar padronização |
| `PhoneService` | Categórico | Codificar |
| `MultipleLines` | Categórico | Preservar categorias como “No phone service” |
| `InternetService` | Categórico | Codificar |
| `OnlineSecurity` | Categórico | Preservar “No internet service” |
| `OnlineBackup` | Categórico | Preservar “No internet service” |
| `DeviceProtection` | Categórico | Preservar “No internet service” |
| `TechSupport` | Categórico | Preservar “No internet service” |
| `StreamingTV` | Categórico | Preservar “No internet service” |
| `StreamingMovies` | Categórico | Preservar “No internet service” |
| `Contract` | Categórico | Codificar sem presumir ordem artificial |
| `PaperlessBilling` | Binário categórico | Codificar |
| `PaymentMethod` | Categórico | Codificar |
| `MonthlyCharges` | Numérico | Normalização/escala dentro do pipeline |
| `TotalCharges` | Numérico armazenado como texto em cópias comuns | Converter com `pd.to_numeric(errors="coerce")` e tratar ausências conscientemente |
| `Churn` | Alvo (`Yes`/`No`) | `Yes→1`, `No→0`; nunca incluir em `X` |

**Verificar ao carregar**, inclusive a ocorrência conhecida, em diversas cópias, de **11 entradas vazias em `TotalCharges`** — tratar esta quantidade como expectativa a auditar, jamais como resultado já medido neste projeto.

### 5.3. EDA mínima exigida para R05/R06

Executar e registrar:

1. `shape`, nomes e tipos das colunas, `head` de forma não identificadora quando apresentar.
2. Quantidade de linhas duplicadas e duplicação de `customerID`.
3. Contagem de valores nulos/vazios, especialmente `TotalCharges`.
4. Frequência de `Churn=0/1` com contagens e proporções.
5. Distribuição básica de `tenure`, `MonthlyCharges`, `TotalCharges` e atributos relevantes.
6. Inspeção de categorias inesperadas e consistência dos campos de serviços.
7. Relações descritivas entre alguns atributos e `Churn` (sem alegar causalidade).
8. Tabela de decisões: transformação → problema que resolve → justificativa → impacto/amostras afetadas.

**Protocolo:** inspeções meramente descritivas do conjunto podem ser reportadas; decisões supervisionadas para modelagem/feature selection e imputadores/encoders aprendidos não podem usar conjunto de teste.

### 5.4. Pré-processamento [PLANO]

1. Verificar presença das colunas esperadas e target binário; mensagens explícitas de erro se faltar arquivo/coluna.
2. Converter `TotalCharges` para numérico mediante leitura da coluna (transformação determinística do tipo); verificar vazios.
3. Remover `customerID` do conjunto de características; manter seu uso apenas para auditoria de duplicatas se necessário.
4. Separar `X/y` e **holdout estratificado 80/20**, `random_state=42`; proporção pode mudar com justificativa, mantendo teste isolado.
5. Dentro de pipeline por fold de treino: `SimpleImputer(strategy="median")` para numéricos e `SimpleImputer(strategy="most_frequent")` para categóricos; `StandardScaler` para numéricos; `OneHotEncoder(handle_unknown="ignore")` para categóricos.
6. Agrupar o gene do AG por **coluna original**: ao selecionar `Contract`, entram todas as suas variáveis indicadoras; ao excluir, saem todas. Evita codificação instável de bits sobre colunas one-hot e mantém demo inteligível.
7. Ao treinar versões baseline/AG, usar o **mesmo construtor de pipeline** a partir das colunas selecionadas.
8. Para `TotalCharges` vazio, a escolha entre imputar/remover precisa ser justificada com contagem observada; imputação dentro do pipeline é a sugestão inicial por preservar as observações. **Não excluir 11 registros automaticamente por hábito**.
9. Não aplicar balanceamento/SMOTE antes de dividir dados; não é necessário adotá-lo na primeira versão.

---

## 6. ESPECIFICAÇÃO EXPERIMENTAL — BASELINE × ALGORITMO GENÉTICO

### 6.1. Perguntas a responder com evidência

- O AG encontrou um conjunto menor de atributos? Quantos e quais?
- Comparado com baseline, qual foi a diferença em **F1-score** no teste, e em precisão/recall?
- Quais erros ocorreram (falsos positivos e falsos negativos) e o que significam para retenção?
- Quanto tempo e quantas avaliações do classificador a busca genética exigiu?
- O desempenho foi estável entre gerações e, opcionalmente, entre sementes?
- A redução de atributos trouxe alguma vantagem justificada? Se o resultado foi inferior, explicar limitações honestamente.

### 6.2. Baseline padronizado [PLANO]

- Algoritmo proposto: `LogisticRegression(max_iter=2000, random_state=42)` com `Pipeline` de imputação/codificação/escalonamento.
- Inicialmente não ajustar hiperparâmetros em busca de aumentar o teste. `class_weight` pode ser experimentado **somente dentro da validação do conjunto de desenvolvimento** e deve ser aplicado de forma idêntica aos dois braços.
- Todas as colunas elegíveis, com exclusão fixa de identificador e alvo.
- Calcular pontuação de validação cruzada no desenvolvimento; reservar a avaliação no teste para comparação final.
- Estratégia alternativa em caso de problemas de convergência/custo: ajustar iterativamente `max_iter`, solver ou tolerância de maneira documentada e consistente.

### 6.3. Cromossomo e espaço de busca [PLANO]

```
genes = [coluna_1, coluna_2, ..., coluna_d]  # lista determinística, persistida
cromossomo = [1, 0, 1, ..., 0]
S = [coluna_i for i in range(d) if cromossomo[i] == 1]
```

- `d` é a quantidade de colunas candidatas **originais** após exclusões fixas.
- Máscara de todos zeros: inválida; reparar reativando pelo menos um gene ou atribuir fitness mínimo e excluir da seleção.
- A ordem das características deve ser congelada e salvar junto do artefato final.
- Inicializar população aleatória; considerar incluir máscara de todos `1` para referência de busca; contar genótipos únicos e armazenar avaliações em cache.

### 6.4. Função de aptidão [PLANO, a confirmar antes do experimento]

```
fitness(S) = media_CV_F1(S) - lambda_ * (len(S) / d)
```

Onde:
- `media_CV_F1(S)` é o F1 binário de classe positiva, calculado por `StratifiedKFold(n_splits=3, shuffle=True, random_state=42)` **no conjunto de desenvolvimento**.
- `len(S)/d` penaliza fração de características mantidas.
- `lambda_` é penalização pequena, **proposta inicial 0,02**; valor deve ser declarado *antes* do teste e, se calibrado, isso deve ocorrer somente no desenvolvimento.
- F1 usado na função de aptidão é estimativa de busca; **não é a nota final de generalização**.
- Se `S` vazio, rejeitar ou reparar consistentemente.
- `fit` do pré-processamento acontece em cada fold de treino; caches por máscara podem acelerar repetições.

**Não existe obrigação de usar essa função exata no Word.** A fórmula foi escolhida por compatibilizar desempenho e parcimônia.

### 6.5. Operadores e parâmetros iniciais [PLANO, ajustáveis antes do teste]

| Item | Valor inicial | Justificativa |
|---|---|---|
| Representação | vetor binário | Seleção de colunas |
| População | 20–30 indivíduos (sugestão: 24) | Computação moderada |
| Gerações | 10–20 (sugestão: 15) | Evidenciar evolução mantendo prazo |
| Seleção | torneio de 3 | Simplicidade e pressão seletiva controlada |
| Cruzamento | 1 ponto ou uniforme, prob. 0,8 | Recombinação de subconjuntos |
| Mutação | bit-flip, prob. por indivíduo 0,2 e prob. por gene ~`1/d` | Exploração do espaço |
| Elitismo | 1 indivíduo | Preservar melhor fitness |
| Parada | gerações ou ausência de melhoria por 5 gerações | Limitar custo |
| Semente | 42 | Reprodução inicial |
| Cache | fitness por tupla de bits | Evitar recomputar indivíduos repetidos |

**Escolha de implementação:** preferir AG próprio pequeno e legível (funções separadas) para evidenciar conceitos; `DEAP` seria alternativa se simplificar prazo. Se usar biblioteca, os operadores e aptidão ainda devem estar explícitos. Referência DEAP: https://deap.readthedocs.io/ .

### 6.6. Pseudocódigo esperado

```text
carregar dados e validar esquema
isolar X_test/y_test por separação estratificada
criar baseline fixo e protocolo de CV no desenvolvimento
inicializar população de máscaras de atributos
para cada geração:
    para cada cromossomo distinto ainda não avaliado:
        obter atributos ativos
        fazer cross-validation de pipeline + classificador apenas em treino
        calcular F1 médio e penalização por nº de atributos
    registrar melhor fitness e média da geração
    selecionar reprodutores, cruzar, mutar, reparar máscaras vazias
    preservar elite; formar próxima população
selecionar máscara final SEM consultar conjunto de teste
treinar baseline e classificador com atributos selecionados em todo o desenvolvimento
avaliar ambos UMA VEZ no holdout, com mesmas métricas
salvar resultados, máscara, modelo otimizado e metadados
executar demo usando pipeline salvo
```

### 6.7. Comparação final e métricas [PLANO]

**Primária:** F1-score para classe `Churn=1`, com limiar de classificação fixado antecipadamente (padrão `0,5`, salvo justificativa de validação).

**Secundárias:** precisão, recall, acurácia (contextual), matriz de confusão, ROC-AUC quando disponível, quantidade de atributos originais selecionados, tempo de busca e total de avaliações de fitness. Se suficiente, PR-AUC é métrica adicional relevante ao desbalanceamento.

**Tabela de resultados esperada — preencher somente com medidas efetivas:**

| Indicador | Baseline (todas) | AG (selecionadas) | Observação |
|---|---:|---:|---|
| Nº de características originais | a medir | a medir | Exclui ID e alvo |
| F1 no teste | a medir | a medir | Classe positiva |
| Precisão no teste | a medir | a medir | |
| Recall no teste | a medir | a medir | |
| ROC-AUC no teste | a medir | a medir | Se calculável |
| FP / FN | a medir | a medir | Erros de negócio |
| Custo da otimização | — | a medir | Tempo e avaliações |

**Interpretação necessária:** variação numérica e possível trade-off desempenho × número de atributos; não concluir superioridade com diferença diminuta ou isolada. Se houver tempo, repetir AG com 3 sementes **antes de olhar o teste**, relatar variação de fitness/CV e usar o critério de escolha previamente definido; não usar múltiplos testes como seleção informal.

### 6.8. Principais ameaças à validade

- **Vazamento:** pré-processamento ou seleção executados antes de separar treinamento/teste, incluindo consultas repetidas ao teste.
- **Sobreajuste da seleção:** AG testa muitas máscaras e pode encontrar combinação boa por sorte na validação. Teste intocado e comparação honesta mitigam.
- **Desbalanceamento:** acurácia alta pode esconder dificuldade com classe positiva; usar F1, recall, precisão e matriz.
- **Causalidade e decisão comercial:** previsão não prova causas nem efeito de oferecer desconto a certo cliente.
- **Representatividade:** base de exemplo com contexto limitado; desempenho real em outras empresas é desconhecido.
- **Mudança temporal:** base comum não define validação prospectiva; limitar alegações futuras.
- **Justiça e uso de características pessoais:** tratar atributos demográficos com cautela; mencionar limitações éticas sem inventar conformidade LGPD.
- **Variabilidade estocástica:** população e mutação podem mudar subconjuntos; registrar semente.
- **Custo computacional:** AG avalia muitos classificadores; ganho pequeno pode não justificar o custo operacional.
- **Interpretação da saída:** pontuação probabilística de modelo não é certeza, e modelos podem ser mal calibrados.

---

## 7. DEMONSTRAÇÃO DE USO — ESCOPO MÍNIMO E ACEITE

**R11 é obrigatório; Streamlit é opcional.** Preferência técnica: uma interface mínima Streamlit, **se não ameaçar os prazos**; fallback plenamente válido: script CLI interativo ou função `predict_customer(data: dict)` com exemplo de nova entrada.

### 7.1. Fluxo recomendado

1. Executar `python train.py` previamente para criar artefato treinado (ou versionar o artefato gerado se tecnicamente e juridicamente apropriado).
2. Usuário informa valores das colunas originais selecionadas, com categorias exatamente contempladas no esquema; caso a interface use formulário maior, filtrar internamente os atributos selecionados.
3. Validação de campo obrigatório, categoria aceitável e tipos numéricos; exibir mensagens compreensíveis para erros.
4. Carregar **o pipeline treinado** (imputação, encoding e classificador juntos); nunca estimar em dados pré-processados manualmente com ordem divergente.
5. Exibir `Churn: Sim/Não` e, se disponível, `Escore estimado de cancelamento: XX%`, com aviso de caráter demonstrativo.
6. Demonstrar ao menos dois perfis plausíveis fornecidos manualmente; sem afirmar que são casos observados do dataset.

### 7.2. Critérios de aceite da demo

- [ ] Funciona sem consultar a resposta verdadeira da linha testada.
- [ ] Aceita nova entrada diferente dos registros de treino.
- [ ] Produz valor calculado pelo **modelo realmente treinado**.
- [ ] Usa as mesmas transformações do treinamento.
- [ ] Tem instrução de execução no README.
- [ ] Não quebra com espaços, categorias inesperadas ou campo numérico inválido sem explicação.
- [ ] Foi executada com ambiente e instruções reproduzíveis.

**Cuidado:** persistir com `joblib`/`pickle` somente artefatos próprios confiáveis; não carregar modelos externos desconhecidos.

---

## 8. ARTIGO ACADÊMICO — ENTREGA EM 23/11

### 8.1. Natureza e prioridade

- **[CONFIRMAÇÃO]** A professora espera espécie de “artigo” ou texto acadêmico em **23/11** seguindo estrutura descrita na orientação/rubrica.
- **[ORIENTAÇÃO]** Critérios associados a título/introdução, conceitos/organização/criatividade, considerações finais e referências; também há exercícios de aula com critérios separados.
- **[REQUISITO DO USUÁRIO]** O artigo deve seguir o **padrão SBC brasileiro**, utilizando o modelo LaTeX de conferências da SBC. A regra foi esclarecida posteriormente e substitui a sugestão anterior de classe `article` livre ou `abnTeX2` como formatação final.
- **[PENDÊNCIA]** Quantidade de páginas, canal exato de entrega e eventuais exigências adicionais da professora não foram informados; não inventar.
- **[PLANO]** Redigir no Overleaf com o modelo SBC, compilar em PDF, preservar fontes `.tex`, `.bib`, `.sty` e `.bst`, e registrar no GitHub. O envio deve respeitar o canal real comunicado pela professora.
- **Regra central:** como o artigo antecede a implementação completa, escrever **metodologia proposta** e **resultados esperados**, sem inventar resultados de treinamento, tabelas de métricas ou conclusões empíricas.

### 8.2. Estrutura sugerida, alinhada aos tópicos do Word

1. **Título** — “Otimização da Identificação de Cancelamento de Clientes por Seleção de Características com Algoritmo Genético” (provisório).
2. **Introdução** — contexto de churn, relevância, problema específico, usuários, objetivo geral, objetivos específicos, motivação da escolha do método, apresentação da fonte do dataset.
3. **Fundamentação teórica / Conceitos** — Aprendizagem de Máquina supervisionada, churn como classificação binária, seleção de atributos, algoritmo genético (cromossomo, aptidão, seleção, cruzamento, mutação, elitismo), avaliação e sobreajuste.
4. **Organização da atividade / Metodologia proposta** — fonte/estrutura da base, exploração e tratamentos previstos, split/validação, baseline fixo, AG de seleção de atributos, fitness, métricas, demonstração com nova entrada e reprodução GitHub.
5. **Considerações finais** — pertinência do problema, potencial do desenho experimental, limitações já identificadas e ressalva de que o desempenho empírico ainda será apurado; não usar verbos de conclusão factual do tipo “foi comprovado”.
6. **Referências** — Kaggle, livros/artigos científicos, scikit-learn e bibliotecas efetivamente mencionadas; padronização bibliográfica consistente.

**Padrão SBC:** incluir **`abstract` (em inglês) e `resumo` (em português)** na primeira página para artigo em português, conforme o template SBC Conferences; o modelo recomenda que cada texto tenha até 10 linhas. Palavras-chave podem ser incluídas como elemento editorial, sem atribuir exigência ao Word.

### 8.2.1. Fonte e regras tipográficas do template SBC [REQUISITO DO USUÁRIO + PADRÃO EXTERNO]

- **Modelo exato:** [SBC Conferences Template — updated sbc-template.sty v2017](https://pt.overleaf.com/latex/templates/sbc-conferences-template/blbxwjwzdngr), disponibilizado no Overleaf com autoria identificada como Sociedade Brasileira de Computação.
- **Estrutura base:** `\documentclass[12pt]{article}`, `\usepackage{sbc-template}`, `\usepackage[brazil]{babel}`, `\usepackage{graphicx,url}`; não substituir por `abntex2` nem impor margem manual com `geometry`.
- **Bibliografia do template:** `\bibliographystyle{sbc}` e `\bibliography{referencias}` com `referencias.bib` e `sbc.bst` presentes no projeto. Não usar `plainnat` como estilo final.
- **Estilo tipográfico definido pelo modelo:** página A4, coluna única, Times 12 pt, margem superior 3,5 cm, inferior 2,5 cm, laterais 3 cm, sem numeração de páginas/cabeçalho/rodapé. Evitar personalização que quebre o padrão.
- **Primeira página:** título, autores, instituição, abstract (inglês), resumo (português). No template para artigos em português, os dois resumos devem ficar na primeira página e ter até 10 linhas cada.
- **Seções principais:** introdução, fundamentação, metodologia proposta, considerações finais, referências, ajustadas ao Word; o template não exige que sejam em inglês.
- **Arquivos iniciais previstos:** `docs/artigo/main.tex`, `docs/artigo/referencias.bib`, `docs/artigo/sbc-template.sty`, `docs/artigo/sbc.bst`; manter PDF final/figuras se houver. Evitar criar arquivos inexistentes artificialmente.
- **Limite de páginas:** o template remete às regras do evento; como não há evento SBC nem limite fixado no Word, não presumir total específico.
- **Fonte verificada em 21/11/2026:** https://pt.overleaf.com/latex/templates/sbc-conferences-template/blbxwjwzdngr .
- **Distinção de proveniência:** formato SBC foi exigido pelo usuário; os detalhes acima vêm do template SBC, e não do documento `Orientacao_projeto_N3.docx`.

### 8.3. Checklist editorial do artigo (gate A01)

- [ ] Utiliza o template LaTeX SBC; fontes `.tex/.bib` e dependências do estilo disponíveis, PDF compilado.
- [ ] Título, autores, vínculo institucional, abstract e resumo em conformidade com o template SBC.
- [ ] Título identifica método e problema.
- [ ] Introdução define claramente objetivo, público e dataset.
- [ ] Explica por que AG é plausível para busca combinatória de características.
- [ ] Distingue AG de classificador supervisionado.
- [ ] Documenta método esperado sem implicar experimento já executado.
- [ ] Define como treinamento, avaliação e demonstração acontecerão.
- [ ] Considerações finais coerentes com fase de planejamento.
- [ ] Referências reais com nomes e links verificáveis; sem bibliografia inventada.
- [ ] Clareza, correção linguística e consistência de conceitos.
- [ ] Arquivo exportado no formato/canal confirmado, entregue até 23/11.
- [ ] Evidência/status da entrega anotado neste guia após envio.

### 8.4. Modelos de enunciado (sem resultados inventados)

**Objetivo geral:** “Investigar a utilização de um algoritmo genético na seleção de características para um classificador supervisionado de cancelamento de clientes, comparando desempenho preditivo e número de atributos utilizados com um modelo sem otimização genética.”

**Objetivos específicos:** identificar/justificar a base; explorar e preparar dados; treinar modelo de referência; implementar cromossomo, aptidão e operadores genéticos; treinar versão com subconjunto selecionado; avaliar ambos em protocolo comum; construir demonstração com entrada inédita; discutir resultados e limitações.

**Delimitação:** “O algoritmo genético será empregado como método de otimização de características de entrada; a classificação será realizada por modelo supervisionado. A avaliação final será obtida após desenvolvimento e treinamento, respeitando separação entre seleção/validação e teste.”

**Fecho pré-experimental aceitável:** “Espera-se que o estudo permita compreender o comportamento da seleção evolutiva de atributos e seus trade-offs em relação a um modelo de referência. A existência de ganhos de desempenho dependerá da avaliação experimental futura.”

---

## 9. REPOSITÓRIO GITHUB — ESCOPO MÍNIMO, ESTRUTURA E REGRAS

### 9.1. Organização sugerida [PLANO]

> O nome do repositório não foi confirmado. `churn-genetic-optimization` é apenas **slug provisório**. Não atribuir URL inexistente.

```text
churn-genetic-optimization/
├── README.md                       # Obrigatório: objetivo, execução, principais resultados
├── requirements.txt                # Dependências verificadas, com versões testadas
├── .gitignore
├── train.py                        # Comando de ponta a ponta: baseline + AG + avaliação + artefatos
├── app.py                          # Demo simples Streamlit ou CLI, conforme escolha real
├── data/
│   ├── README.md                   # Fonte Kaggle, licença/instruções de download
│   └── raw/                        # CSV local, normalmente ignorado pelo Git
├── src/
│   ├── __init__.py
│   ├── data.py                     # Leitura, esquema, EDA e preparo
│   ├── models.py                   # Pipeline e classificador baseline
│   ├── genetic_algorithm.py        # Operadores, avaliação, busca e logs
│   └── evaluation.py               # Métricas, comparação, gráficos/tabelas
├── results/
│   ├── metrics.json                # Gerado após execução real
│   ├── selected_features.json      # Ordem/máscara final documentadas
│   └── fitness_history.csv         # Melhor/média por geração, gerado realmente
├── models/
│   └── churn_pipeline.joblib       # Opcional versionar após treinar: pesa/licença/ambiente
├── docs/
│   ├── GUIA_MESTRE_PROJETO_N3.md   # Este documento central, se integrado ao repo
│   └── ARTIGO_N3.md                # Fonte textual do artigo, opcional
└── tests/
    └── test_smoke.py               # Testes mínimos importantes
```

**Não criar arquivos vazios artificialmente para corresponder a árvore.** Adicionar somente quando a etapa chegar; manter estrutura ajustável se for simplificada. O projeto deve permanecer pequeno e executável.

### 9.2. README obrigatório — sumário mínimo

1. Título e resumo (problema + solução).
2. Objetivo e quem poderia utilizá-la.
3. Dataset e referência Kaggle + como obter CSV.
4. Metodologia: pré-processamento, classificador, AG, fitness, split, métricas.
5. Requisitos do ambiente e versões Python/bibliotecas testadas.
6. Instruções concretas de instalação e execução de treino e demonstração.
7. **Resultados efetivamente medidos** (tabela baseline × AG, atributos selecionados, principais erros/limitações), após execução.
8. Limitações, conclusões e referências.
9. Contribuições do grupo, se útil para apresentação; formato não imposto pelo Word.

**README de etapa inicial:** pode conter “resultados: pendentes” enquanto não houver experimento. Na entrega de 27/11, deve conter **principais resultados reais**.

### 9.3. Políticas Git/commits

- Iniciar `git init`, criar `main`, configurar `.gitignore`, registrar estrutura e escopo.
- Efetuar commits em **unidades coerentes de avanço**. Ex.: `docs: formaliza problema e metodologia`, `feat: prepara dataset`, `feat: treina classificador base`, `feat: implementa selecao genetica`, `test: valida operadores geneticos`, `feat: compara modelos`, `feat: demonstra previsao para novo cliente`, `docs: consolida resultados e execucao`.
- **Commits refletem modificações verdadeiras**. Não criar histórico fictício, não ajustar datas de commits e não registrar “funciona” sem testar.
- Branch `main` suficiente; push ao GitHub quando repositório estiver configurado. PR/wiki e formalidades de equipe desnecessários.
- Guardar segredos fora do Git (tokens Kaggle, senhas, chaves). `.env`, `.venv/`, `__pycache__/`, arquivos locais de grandes volumes e cache devem estar ignorados.
- Resultados leves e reprodutíveis podem ser versionados; artefatos grandes requerem análise antes de commit.
- Fazer `git status`, executar testes e validar README antes de cada commit importante.

### 9.4. Comandos-alvo (confirmar caminhos definitivos durante o desenvolvimento)

```bash
# Ambiente virtual (Windows PowerShell)
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# O arquivo CSV deve estar na pasta indicada em data/README.md
python train.py --data "data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv"

# Se app Streamlit for adotado:
streamlit run app.py

# Ou, se demo CLI for adotada:
python app.py

# Testes mínimos, se pytest constar das dependências:
python -m pytest -q
```

**Ainda são comandos pretendidos, não testados.** Quando implementar, atualizar para refletir exatamente o software que funciona. Não prometer instalação limpa sem efetuar teste.

---

## 10. ROTEIRO DE IMPLEMENTAÇÃO E MARCOS DE COMMIT

### M0 — Consolidação de escopo e exigências (21/11)

**Dependências:** Word inspecionado + confirmações da professora via usuário.

- [x] Problema de churn definido.
- [x] Algoritmo genético selecionado para seleção de características.
- [x] Dataset Kaggle indicado.
- [x] Entrega de artigo 23/11 confirmada pelo usuário.
- [x] Prazos 27/11 e 30/11 conferidos no Word.
- [x] Fluxo de commits sem PR/wiki definido.
- [x] Guia mestre escrito (este arquivo; confirmar antes de marcar como versionado no Git).
- [x] Repositório GitHub criado e URL verificada: https://github.com/bredleyb/churn-genetic-optimization.

**Gate:** todos os requisitos conhecidos rastreados; próximo foco artigo.

### M1 — Artigo acadêmico (prioridade máxima até 23/11)

- [ ] Redigir introdução/objetivos.
- [ ] Redigir fundamentação de ML, churn, feature selection e AG com referências.
- [ ] Fixar metodologia planejada sem resultados fictícios.
- [ ] Redigir considerações finais prospectivas e limitações.
- [ ] Revisar nomenclatura e bibliografia.
- [ ] Exportar conforme instrução da professora; entregar por canal real e registrar confirmação.

**Gate:** A01 entregue no prazo. Se o repositório já existir, fazer commit `docs: registra artigo e fundamentacao inicial` com o material apropriado.

### M2 — Estrutura, dados e EDA (até 24/11)

- [ ] Criar GitHub verdadeiro; confirmar URL e visibilidade adequada ao compartilhamento.
- [ ] `.gitignore`, `requirements.txt`, README inicial, dados/README, fontes.
- [ ] Obter CSV real do Kaggle, conferir nome/dimensões/esquema/licença.
- [ ] Implementar leitura com erros informativos.
- [ ] Medir alvo, nulos, duplicatas, tipos, variáveis e registrar tratamento justificado.
- [ ] Testar divisões estratificadas.

**Gate:** R02–R06 documentados; dados carregam e divisão funciona sem vazamento.

**Commits sugeridos:** `chore: inicializa repositório`; `feat: explora e prepara dados do churn`.

### M3 — Modelo de referência (até 24/11)

- [ ] Criar construtor de pipeline por lista de atributos originais.
- [ ] Implementar `fit/predict/predict_proba` sobre conjunto de desenvolvimento.
- [ ] Fixar CV e métrica de busca sem tocar no teste.
- [ ] Conferir se o pipeline suporta categorias inéditas e nulos.
- [ ] Salvar resumo do baseline em CV/desenvolvimento.

**Gate:** modelo de ML efetivamente treinado; R07 iniciado; baseline reproduzível.

**Commit sugerido:** `feat: implementa classificador de referencia`.

### M4 — Algoritmo genético (até 25/11)

- [ ] Implementar cromossomo, população e correção de máscaras vazias.
- [ ] Implementar fitness CV+penalização, cache e controle de semente.
- [ ] Implementar seleção, cruzamento, mutação e elitismo.
- [ ] Registrar melhor/média fitness e quantidade de características por geração.
- [ ] Integrar busca ao `train.py` e entregar máscara final.
- [ ] Testes mínimos: máscara não vazia, comprimento fixo, mutação/cruzamento válidos, determinismo com seed, nenhum acesso ao teste em fitness.

**Gate:** AG evolui soluções com logs verificáveis e integra classificador; sem resultados de teste ainda.

**Commits sugeridos:** `feat: implementa algoritmo genetico`; `test: cobre operadores e fitness`.

### M5 — Comparação e resultados (até 26/11)

- [ ] Fixar metodologia e hiperparâmetros antes de testar.
- [ ] Ajustar baseline e AG-selected em todo o conjunto de desenvolvimento.
- [ ] Rodar avaliação final no holdout **uma única vez após decisão**.
- [ ] Gerar matriz de confusão, métricas, curva de melhor fitness, atributos escolhidos, custo de busca.
- [ ] Preencher tabela real no README; incluir interpretação e erros.
- [ ] Documentar limitações e eventuais ganhos/perdas sem esconder resultados desfavoráveis.
- [ ] Salvar artefato treinado e esquema de entrada; validar leitura.

**Gate:** R08–R10, R16; resultados reproduzíveis e honestos.

**Commit sugerido:** `feat: avalia e compara modelos com e sem AG`.

### M6 — Demo e documentação final (até 26/11)

- [ ] Criar função/script/interface de nova entrada usando pipeline final.
- [ ] Testar ao menos dois perfis novos e erros básicos de entrada.
- [ ] README completo: objetivo, execução e principais resultados reais.
- [ ] Conferir fonte Kaggle, referências e justificativas em todas as páginas.
- [ ] Fazer instalação limpa ou simulação fiel; executar treino e demo conforme instruções.
- [ ] Revisar consistência entre README, artigo, código e apresentação.

**Gate:** R11–R13, R17 concluídos e projeto pronto para compartilhamento.

**Commits sugeridos:** `feat: disponibiliza demonstracao funcional`; `docs: consolida resultados e instrucoes`.

### M7 — Entrega GitHub (27/11)

- [ ] Confirmar repositório íntegro e visível a quem avaliará.
- [ ] Confirmar `main` remota atualizada; copiar **URL real**.
- [ ] Testar instruções de execução do README e demo final.
- [ ] Confirmar que nenhum segredo ou dataset sem permissão foi publicado.
- [ ] **Enviar link pelo canal solicitado pela professora** dentro do prazo.
- [ ] Guardar confirmação da entrega e registrar horário observado, se disponível.

**Gate:** R14 entrega efetiva; pontualidade protegida. **Push sem envio do link não comprova o requisito “link ... deve ser disponibilizado”.**

### M8 — Socialização (28–30/11)

- [ ] Preparar apresentação curta centrada em problema → dados → AG → treino → métricas → limitações → demo.
- [ ] Reservar demonstração com modelo local e entrada nova; plano B com função/script se UI falhar.
- [ ] Cada integrante domina conceitos, operadores, divisão de dados, fitness, diferenças entre modelos, erros e conclusão.
- [ ] Identificar contribuições **verdadeiras** de cada integrante; não inventar número de pessoas ou divisão de tarefas.
- [ ] Ensaiar tempo de inicialização da demo; não depender de novo download Kaggle ao vivo.
- [ ] Comparecer pontualmente e realizar demonstração em 30/11.

**Gate:** R14 apresentação e R15; rubrica individual conhecimento/postura e pontualidade atendidas na medida controlável.

---

## 11. TESTES E CRITÉRIOS MÍNIMOS DE QUALIDADE

**Prioridade:** garantir que o código executa de ponta a ponta antes de ampliar testes. Recomendações técnicas, não obrigações textuais.

### 11.1. Testes de dados

- CSV ausente produz erro com caminho esperado e instrução de download.
- Colunas faltantes geram erro compreensível.
- `TotalCharges` em branco é convertido/tratado sem quebrar.
- `customerID` e `Churn` **nunca** entram como genes.
- Divisão de treino/teste mantém distribuição aproximada do alvo; sem duplicações deliberadas.

### 11.2. Testes de AG

- Comprimento do cromossomo igual a `d`, bits 0/1; população de tamanho previsto.
- Indivíduo vazio é reparado/rejeitado.
- Cruzamento, mutação, seleção e elitismo preservam indivíduos válidos.
- Função de aptidão devolve valor finito para máscaras válidas.
- `random_state` produz resultado repetível em execução semelhante.
- A implementação de fitness aceita **somente** o conjunto de desenvolvimento.
- Logs de gerações apresentam evolução de melhor e média aptidão; não exigir melhoria monotônica da média.

### 11.3. Testes de integração

- Com mesmo split, as duas versões usam o mesmo pipeline básico.
- Teste final não é usado para parâmetros/atributos.
- `train.py` gera resultados e modelo carregável.
- A demo prevê pelo menos um registro novo com esquema válido.
- O comando do README corresponde ao comando real que foi testado.

---

## 12. ARTEFATOS MÍNIMOS E EVIDÊNCIAS PARA AVALIAÇÃO

| Artefato | Momento | Finalidade | Obrigatoriedade |
|---|---|---|---|
| Artigo/texto acadêmico | **23/11** | Título, introdução, fundamentação, metodologia, considerações finais e referências | **Confirmada pela professora via usuário** |
| Código de leitura/exploração/preparação | Até 27/11 | R05–R06 | Obrigação funcional do Word |
| Classificador treinável | Até 27/11 | R01/R07 | Obrigação funcional |
| Implementação AG integrada | Até 27/11 | Método escolhido pelo projeto | Decisão do projeto, necessária à sua coerência |
| Comparação/métricas/resultados | Até 27/11 | R08–R10/R16 | Obrigação funcional |
| Demo com entrada inédita | Até 27/11 | R11 | Obrigação explícita |
| `README.md` com objetivo/execução/resultados | Até 27/11 | R12 | Obrigação explícita |
| **Link verdadeiro do repositório entregue** | **27/11** | R13–R14, pontualidade | Obrigação explícita |
| Slides/roteiro + fala + demonstração | **30/11** | R14–R15 e rubrica individual | Obrigação de apresentação; formato de slides não especificado |
| Histórico de commits progressivos | Durante desenvolvimento | Compartilhar desenvolvimento | Decisão organizacional que satisfaz espírito do Word |
| Este guia mestre | Uso interno | Continuidade e rastreabilidade da IA | Controle interno, não exigência da professora |

**Exercícios de aula 16/11 e 23/11:** têm pontuação específica. Não considerar cobertos automaticamente pelo artigo, repositório ou demo. Verificar o que efetivamente foi realizado/solicitado.

---

## 13. O QUE NÃO FAZER: ANTIPADRÕES E DESVIOS

1. **Não** substituir silenciosamente o problema de churn, o dataset ou a estratégia AG por outra sem autorização do usuário.
2. **Não** desenvolver apenas um otimizador isolado sem classificador treinado; desrespeitaria a exigência de solução de ML e treinamento.
3. **Não** tratar a demonstração de nova entrada como captura estática ou simples leitura de linha já rotulada.
4. **Não** construir interface sofisticada antes de implementar treino e avaliação.
5. **Não** executar imputação estatística/encoding aprendido no conjunto total antes de CV.
6. **Não** escolher cromossomos usando o teste; **não** modificar escolhas depois de ler métrica final do teste.
7. **Não** inflar resultados, prometer melhora de precisão ou antecipar conclusões.
8. **Não** criar requisitos inexistentes (ABNT mandatória, relatório de tamanho fixo, acurácia mínima, wiki, PR, cloud).
9. **Não** colocar CSV Kaggle publicamente sem verificar permissões.
10. **Não** confundir o artigo entregue dia 23 com README completo exigido dia 27.
11. **Não** deixar link do GitHub para depois de 27/11 imaginando que a apresentação de 30/11 cobrirá a entrega.
12. **Não** inventar nomes/contribuições dos integrantes ou situação de atividades de 16/11 e 23/11.
13. **Não** usar acurácia isolada como argumento de qualidade em classe possivelmente desbalanceada.
14. **Não** colocar `joblib` em projeto sem registrar versão das dependências; tampouco desserializar arquivos não confiáveis.
15. **Não** converter este guia em burocracia a ser mostrada ao professor: ele serve para consistência interna.

---

## 14. RISCOS, PRIORIDADES E PLANOS DE CONTINGÊNCIA

| Risco | Impacto | Mitigação | Plano B |
|---|---|---|---|
| Artigo consumir tempo demais antes do dia 23 | Perda de prazo próprio | Fixar escopo, usar estrutura da rubrica, revisão objetiva | Entregar versão coerente e integral antes de embellishment |
| Dataset não baixado por autenticação Kaggle | Bloqueio de treino | Informar download manual, testar caminho cedo | Utilizar fonte oficial equivalente **somente com confirmação de equivalência e citação correta** |
| AG lento por CV dentro do fitness | Compromete demo | Cache de máscaras, população/gerações moderadas, 3-fold, classificador leve | Reduzir parâmetros de busca antes do teste; documentar |
| F1 do AG igual ou inferior ao baseline | Conclusão desfavorável à hipótese | Interpretar trade-off de atributos/custo com honestidade | Resultado negativo continua válido academicamente |
| Pipeline incompatível com novos dados | Demo falha | Preservar schema, persistir pipeline completo, testes com nova entrada | Script mínimo que use o pipeline diretamente |
| Ausência de internet na apresentação | Falha externa | Execução local, modelo salvo | Demo CLI local com perfil de exemplo |
| Desvio de metodologia entre artigo e código | Incoerência na avaliação | Registrar alterações e justificativas no README/apresentação | Expor claramente mudanças após fase propositiva |
| Falta de tempo para testes extensos | Software instável | Priorizar smoke test e execução completa de instalação/treino/demo | Cortar refinos cosméticos e extras |
| Exercícios de aula interpretados incorretamente | Possível perda de 2 pontos | Verificar critério e evidências com o grupo/professora | Não alegar que artigo automaticamente equivale aos exercícios |
| Link não enviado apesar de repositório pronto | Risco direto em pontualidade | Checklist de envio e confirmação | Enviar cedo em 27/11 após validação |

**Ordem de prioridades em emergência:** (1) cumprir entrega com requisitos mínimos; (2) consistência metodológica; (3) métricas e interpretação; (4) nova entrada funcional; (5) documentação correta; (6) visual extra/expansões.

---

## 15. DECISÕES CONSOLIDADAS E PENDÊNCIAS REAIS

### 15.1. Registro de decisões (até 21/11/2026)

| Código | Decisão | Origem | Estado |
|---|---|---|---|
| D01 | Problema de otimização para identificar churn | Usuário | Confirmada |
| D02 | AG como técnica de seleção de características | Discussão validada pelo usuário | Confirmada |
| D03 | Dataset Telco Customer Churn do Kaggle | Proposta adotada como referência na conversa | Fonte inicial; confirmar aquisição/arquivo real |
| D04 | Comparar classificador sem seleção e com AG | Metodologia proposta e aceita no alinhamento | Diretriz experimental |
| D05 | GitHub por commits progressivos, sem PR/wiki complexa | Usuário | Confirmada |
| D06 | Artigo/texto acadêmico em 23/11 | Professora, conforme usuário | Confirmada |
| D07 | Link GitHub completo em 27/11 | Word | Obrigatória |
| D08 | Apresentação/demonstração em 30/11 | Word | Obrigatória |
| D09 | Python + scikit-learn + regressão logística | Planejamento técnico | Proposta operacional, ajustável |
| D10 | Interface Streamlit pequena ou CLI | Planejamento técnico | Opcional; fallback CLI plenamente válido |
| D11 | Holdout estratificado, CV no desenvolvimento, F1 | Planejamento técnico | Recomendação metodológica prioritária |
| D12 | Artigo em padrão SBC brasileiro via LaTeX/Overleaf | Usuário (21/11/2026); formato indicado no Overleaf da SBC | Obrigatório para o artigo |

### 15.2. Informações ainda não conhecidas

- `[CONFIRMADO]` Repositório público: https://github.com/bredleyb/churn-genetic-optimization ; branch principal `main`, arquivos iniciais publicados e verificados.
- `[PENDÊNCIA]` Número de integrantes, nomes e distribuição real do trabalho (não inventar).
- `[PENDÊNCIA]` Canal de envio do artigo de 23/11 e do link em 27/11, limite de páginas e horários; formato gráfico do artigo **já definido como SBC** pelo usuário.
- `[PENDÊNCIA]` Conteúdo específico dos exercícios de 16/11 e 23/11, e estado de sua realização.
- `[PENDÊNCIA]` Tempo e meio de apresentação de 30/11; acesso a computador/internet no local.
- `[PENDÊNCIA]` CSV efetivamente baixado, licença exata, estatísticas reais e resultados do projeto.
- `[PENDÊNCIA]` Modelo e parâmetros definitivos após testes de desenvolvimento; não confundir parâmetros sugeridos com decisões irreversíveis.

Essas pendências devem ser resolvidas na execução quando necessário, priorizando trabalho útil sem interromper etapas por perguntas cosméticas.

### 15.3. Estado atual verificável — snapshot 21/11/2026

```
DOCUMENTO_ORIENTACAO_INSPECIONADO = SIM
PRAZOS_OFICIAIS_VERIFICADOS = SIM
ARTIGO_23_CONFIRMADO_PELO_USUARIO = SIM
FORMATO_ARTIGO_SBC_CONFIRMADO_PELO_USUARIO = SIM
PROBLEMA_DEFINIDO = SIM
DATASET_DE_REFERENCIA_DEFINIDO = SIM (Telco Customer Churn; ainda sem CSV explorado neste projeto)
METODO_AG_DEFINIDO = SIM
METODOLOGIA_EXPERIMENTAL_PROPOSTA = SIM
REPOSITORIO_REMOTO_CRIADO = SIM (https://github.com/bredleyb/churn-genetic-optimization ; arquivos iniciais verificados)
ESTRUTURA_INICIAL_PUBLICADA = SIM (README, .gitignore, guia mestre, artigos .tex/.bib e README próprio)
ARTIGO_ESCRITO_E_ENTREGUE = NÃO VERIFICADO
CODIGO_IMPLEMENTADO = NÃO VERIFICADO
MODELO_TREINADO = NÃO VERIFICADO
RESULTADOS_EMPIRICOS = INEXISTENTES / NÃO VERIFICADOS
DEMONSTRACAO_EXECUTADA = NÃO VERIFICADA
LINK_GITHUB_ENVIADO = NÃO VERIFICADO
APRESENTACAO_REALIZADA = NÃO (futura em 30/11)
```

---

## 16. GUIA DE PREPARAÇÃO PARA APRESENTAÇÃO E PERGUNTAS ORAIS

### 16.1. Narrativa recomendada (sem tempo preestabelecido)

1. Apresentar a pergunta e sua relevância.
2. Descrever fonte e estrutura do dataset; alvo `Churn` e principais cuidados de tratamento.
3. Justificar classificador supervisionado e problema combinatório de seleção.
4. Mostrar representação do cromossomo, fitness, população, seleção, cruzamento, mutação e curva de evolução.
5. Explicar split, CV e teste isolado em linguagem acessível.
6. Comparar resultados medidos e número de características; discutir falsos positivos e negativos.
7. Apresentar perfil novo e executar o modelo.
8. Explicitar limitações, considerações finais e contribuição verdadeira de cada integrante.

### 16.2. Perguntas de conhecimento a dominar

- Por que churn é classificação supervisionada?
- Por que usar AG e qual objetivo sua busca otimiza?
- O que representa um gene `1` e um gene `0`?
- O algoritmo genético treina diretamente os parâmetros do classificador neste trabalho?
- Como o fitness é calculado? O que significa a penalização pelo nº de atributos?
- Qual a diferença entre precisão e recall para cancelamento de clientes?
- Por que usar F1 em vez de somente acurácia?
- Por que dividir treino/teste antes da seleção de características?
- Como demonstramos que o método selecionado melhora, mantém ou piora o baseline?
- Qual o custo computacional? Quais limitações de dataset, generalização e ética?
- Quem fez o quê e quais decisões cada integrante consegue justificar?

### 16.3. Plano de falha da demo

- Primeira preferência: modelo já treinado carregado localmente, sem acesso ao Kaggle ou a APIs.
- Segunda preferência: CLI com entrada de dicionário válida que execute `predict`.
- Capturas/gráficos previamente gerados servem de evidência auxiliar, **não substituem** a exigência de demonstração funcional do software no projeto.

---

## 17. REFERÊNCIAS REAIS PARA ARTIGO, README E DEFESA

**Referências usadas como base de fundamentação (verificadas em fontes externas; adequar formatação à entrega):**

1. **KAGGLE / BLASTCHAR.** *Telco Customer Churn*. Dataset, IBM Sample Data Sets. https://www.kaggle.com/datasets/blastchar/telco-customer-churn . Fonte da base, com arquivo usual `WA_Fn-UseC_-Telco-Customer-Churn.csv`.
2. **HOLLAND, John H.** *Adaptation in Natural and Artificial Systems: An Introductory Analysis with Applications to Biology, Control, and Artificial Intelligence*. University of Michigan Press, 1975. https://openlibrary.org/books/OL5070129M/Adaptation_in_natural_and_artificial_systems . Referência fundacional de algoritmos genéticos.
3. **GUYON, Isabelle; ELISSEEFF, André.** An Introduction to Variable and Feature Selection. *Journal of Machine Learning Research*, v. 3, p. 1157–1182, 2003. https://jmlr.org/papers/v3/guyon03a.html . Fundamentos de seleção de atributos.
4. **SCIKIT-LEARN DEVELOPERS.** *Common pitfalls and recommended practices*. https://scikit-learn.org/stable/common_pitfalls.html . Fundamentos sobre vazamento e pipelines.
5. **SCIKIT-LEARN DEVELOPERS.** *Cross-validation: evaluating estimator performance*. https://scikit-learn.org/stable/modules/cross_validation.html . Avaliação cruzada e conjunto holdout.
6. **SCIKIT-LEARN DEVELOPERS.** *f1_score*. https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html . Definição da métrica F1.
7. **SCIKIT-LEARN DEVELOPERS.** *LogisticRegression*. https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html . Referência técnica para baseline se de fato utilizado.
8. **DEAP DEVELOPERS.** *DEAP documentation*. https://deap.readthedocs.io/ . Adicionar à bibliografia do artigo apenas se o texto realmente discutir/usar a biblioteca; caso contrário, não incluir como fonte metodológica central.

**Princípios bibliográficos:** citar no corpo do artigo os conceitos que dependem dessas fontes; não declarar que um artigo “prova vantagem do AG para churn” se apenas fundamenta seleção de variáveis; não inventar DOI, número de edição, páginas ou ano para documentos não verificados; usar data de acesso se solicitada pela professora/formatação escolhida.

---

## 18. MATRIZ DE RASTREABILIDADE FINAL (FECHAMENTO NO DIA 27/11)

| Elemento | Evidência mínima | IDs ligados | Status inicial |
|---|---|---|---|
| Artigo 23/11 | PDF compilado no template SBC e texto entregue com seções da rubrica | A01, A02, R02, R03, R04, R16, R17 | [PENDENTE] |
| Contextualização e público | Introdução/README | R01–R04 | [PENDENTE] |
| Exploração/tratamento | Código + explicação | R05–R06 | [PENDENTE] |
| Treinamento convencional | Baseline executável | R07 | [PENDENTE] |
| Evolução genética | Código + log de gerações | R01, R07 | [PENDENTE] |
| Teste comparativo | Métricas e interpretação | R08–R10 | [PENDENTE] |
| Demo perfil novo | Script/função/UI executável | R11 | [PENDENTE] |
| README executável | Objetivo, comandos, resultados reais | R12 | [PENDENTE] |
| Commits e link | Repo verificável, link enviado | R13–R14 | [PENDENTE] |
| Considerações e referências | Documentação coerente | R16–R17 | [PENDENTE] |
| Apresentação/contribuições | Exposição e demo real | R14–R15 | [PENDENTE] |
| Exercícios em aula | Evidência conforme professora | Rubrica coletiva: 2,0 | [PENDÊNCIA] |

### Condição inequívoca de finalização

**Projeto pronto para o dia 27:** o repositório real está acessível; dataset e execução estão explicados; código de dados/modelo/AG/métricas foi executado; existe comparação de resultados reais com discussão de erros/limitações; há demonstração com nova entrada; README atende aos três tópicos explícitos; referências estão presentes; link foi efetivamente enviado.

**Projeto pronto para o dia 30:** além do anterior, cada participante conhece e consegue demonstrar a solução, com suas contribuições verdadeiras explicitadas e presença pontual.

---

## 19. PROTOCOLO DE ATUALIZAÇÃO DESTE GUIA

Ao finalizar qualquer etapa, a IA deve:

1. Atualizar o status `[PENDENTE] → [CONCLUÍDO]` somente com evidência real.
2. Escrever no registro a **data observada**, arquivos relevantes, comandos executados, resultados e **hash ou referência real do commit** se disponível.
3. Alterar decisões apenas com justificativa e registrar quando foi mudada a metodologia da versão do artigo.
4. Revisar as pendências afetadas; confirmar fidelidade ao Word.
5. Manter prioridade do próximo prazo. Não transformar extensões opcionais em bloqueios.

### Registro de progresso (preencher conforme execução)

| Data | Marco | Ação / evidência | Arquivos / commit real | Resultado / pendência |
|---|---|---|---|---|
| 21/11/2026 | M0 | Word relido integralmente, requisitos e decisões consolidados | `GUIA_MESTRE_PROJETO_N3.md` | Artigo de 23/11 é próxima prioridade |
| 21/11/2026 | M1 | Usuário definiu padrão LaTeX SBC brasileiro; template SBC Conferences do Overleaf identificado | Guia mestre atualizado | Artigo ainda não escrito; formato definido |
| 21/11/2026 | M0/M1 | Repositório remoto criado, primeiro commit e arquivos iniciais do artigo SBC publicados | `https://github.com/bredleyb/churn-genetic-optimization` ; commit inicial `f10835a` | Estrutura verificada no GitHub; artigo ainda pendente |
| 21/11/2026 | M2 (preparação local) | Estrutura inicial montada com README, .gitignore, guia e arquivos-fonte iniciais SBC | Pacote local `churn-genetic-optimization/`; SEM remoto/commit | Criar repositório no GitHub e concluir artigo |

---

**FIM DO GUIA MESTRE.** Este documento é instrumento interno de continuidade para a IA. A fonte normativa permanece sendo o Word original e as confirmações da professora transmitidas pelo usuário.