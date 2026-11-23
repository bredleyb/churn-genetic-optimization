# Roteiro de testes — painel Cliente (N3)

## Escopo e método

Auditoria do painel Cliente na versão final: perfis 1–5, campos, regras de serviços,
responsividade, rolagem, sombras e cálculo. Os resultados científicos
(treinamento, algoritmo genético, avaliação) mantêm seus testes próprios.

- **pytest:** contratos e estados da aplicação Python, dados e persistência.
- **Playwright:** navegador Streamlit real, interação, geometria, cores,
  foco, rolagem, tipografia e estados transitórios.
- **Evidência:** screenshots CL-* anexadas a cada cenário visual, relatório
  HTML/JSON, traces e ZIP. Capturas são inspecionáveis; os critérios de
  aprovação dependem de asserções, sem aceitar automaticamente snapshots novos.
- **Resoluções:** 1440×900, 1366×768, 1280×720, 1024×768, 768×900, 390×900.
- **Precisão geométrica:** centros, limites e larguras ±2 px;
  tolerância de 3 px para a relação externa scroller/rodapé.
  Altura dos campos 42 ±2 px e dimensões dos botões iguais ±1 px.
- **Padrões visuais:** tokens de cores e fontes são lidos do estilo
  efetivamente computado, sem inferi-los apenas da existência de CSS.

## Matriz de rastreabilidade — pytest

| ID | Requisito | Verificação |
|---|---|---|
| CL-U01 | Variáveis e rótulos | 19 variáveis únicas; gender Female/Male conforme dataset; tradução correta |
| CL-U02 | Exemplos originais | 1 e 2 válidos para o modelo, originais e valores independentes |
| CL-U03 | Estrutura | Containers Cliente, perfil, campos, abas, footer e componentes v2 |
| CL-U04 | Grade rápida | Mesma definição (0,55 / 0,45) nas duas linhas |
| CL-U05 | Serviços | Telefonia e internet sincronizam campos dependentes e reversão |
| CL-U06 | Validação | Ausência de TotalCharges, valores negativos e combinações inválidas |
| CL-U07 | Meses | Um único input de dígitos e unidade não editável na mesma caixa, limites 0–999, Ctrl+A nativo e sincronização numérica v2 |
| CL-U08 | CSS compartilhado | Cores, tipografia, dimensões, recuo do footer, scroll e sombras |
| CL-U09 | Criação | 3 a 5 copiam valores atuais, limite máximo de 5 |
| CL-U10 | Restauração | Snapshot próprio, sem efeito sobre outros exemplos |
| CL-U11 | Exclusão | 1 e 2 protegidos, exclusão imediata, renumeração sem perdas e volta do + |
| CL-U12 | Persistência | Alterações preservadas ao alternar abas e perfis |
| CL-U13 | Compatibilidade | Migração de sessão antiga com rascunho preservado |
| CL-U14 | Botão | Calcular, Calculando, Recalcular, um processamento por clique |
| CL-U15 | Exceções | Erro de entrada, liberação do botão e previsão obsoleta após edição |
| CL-U16 | Observador | Sombras e hover atualizados somente no navegador |
| CL-U17 | Ícones de perfil | Restaurar com seta de retorno e Excluir com lixeira, estados inativos e callbacks corretos |

Arquivos: tests/client/test_client_contracts.py, test_client_profiles.py e
test_client_prediction.py; fixture isolada em tests/client/conftest.py.
Esta camada não substitui verificações reais de renderização.

## Matriz de rastreabilidade — Playwright

| ID | Requisito | Evidência / limite |
|---|---|---|
| CL-L01 | Layout geral | 6 resoluções; título centralizado na coluna completa do Cliente, cores, círculos, campos, margens e screenshots |
| CL-L02 | Quatro abas | Campos visíveis, alinhados ao botão e sem overflow lateral; screenshots |
| CL-L03 | Texto e seletores | Familjen Grotesk carregada; rótulos 15 px; valores 14 px; centros ±2 px; hover |
| CL-L04 | Teclado | Abas acessíveis, foco sem barras laterais cinzas |
| CL-P01 | Perfis completos | Criar, editar, alternar, restaurar, excluir, renumerar, adicionar novamente; capturas |
| CL-P02 | Perfil responsivo | Dois botões quadrados, mesmo tamanho dos círculos e mesmo eixo em 4 larguras |
| CL-P03 | Seleção | Botões identificáveis, estado ativo e proteção dos exemplos originais |
| CL-F01 | Mês | 0/1/2/999, singular/plural e substituição de dígitos |
| CL-F02 | Controle de meses | Input numérico único, unidade separada visualmente contígua, botões, limites, foco interno e captura |
| CL-F03 | Categorias | Gênero limitado aos dados originais, campos Perfil e Extras persistentes |
| CL-F04 | Dependências | Telefone e Internet desabilitam e restauram dependentes |
| CL-F05 | Cobrança | Número decimal e Total cobrado indisponível |
| CL-F06 | Consistência visual | Fundo, raios, fontes, cor e hover do Tempo, Cobrança e seletores; wrapper real React Aria |
| CL-F07 | Ações da Cobrança | Dois botões −/+ visíveis nas seis resoluções, com a mesma paleta e hover do Tempo |
| CL-F08 | Edição rápida de Tempo | Ctrl+A seguido de digitação após stepper usa seleção nativa sem concatenar dígitos |
| CL-F09 | Montagem v2 com atualização tardia | Input numérico nativo preserva seleção com props antigas; sem foco, aceita mudança externa; nova revisão recria controle válido |
| CL-F10 | Geometria da unidade | Dígitos e sufixo contíguos na mesma caixa, seleção restrita ao número, em 1440 e 390 px |
| CL-F11 | Entrada inválida e colagem | Rejeita letras, aceita colagem numérica com unidade e normaliza campo vazio no blur |
| CL-S01 | Sombra matemática | Inicial, meio, fim, ausência de overflow e conteúdo curto |
| CL-S02 | Sombra visual | Calhas bilaterais, gradientes 52 px, rodapé fixo, capturas 1024/390 |
| CL-S03 | Rodapé | Foco do botão dentro da área visível |
| CL-B01 | Estados JS | idle/running/complete/unavailable |
| CL-B02 | Feedback | Branco, hover cinza claro, execução cinza médio, reticências, reduced-motion e volta ao branco |
| CL-B03 | Execução E2E | Algoritmo real 1 vez, conclusão, Recalcular, comparação e estado Dados alterados |

As screenshots anexadas no relatório são CL-L01, CL-L02, CL-P01, CL-P02,
CL-F02, CL-S02, CL-B02 e CL-B03. Os valores cromáticos e as posições são
medidos no DOM, e as capturas complementam a revisão humana.

## Procedimento

Pré-requisitos: Python e Node instalados, ambiente virtual ativo, dependências
instaladas e navegador Chromium do Playwright. Execute na raiz do projeto:

    git pull
    python -m pip install -r requirements.txt
    npm install
    npx playwright install chromium

    python -m pytest -q
    python -m pytest -q tests/client
    npm run test:visual
    npm run test:visual:report

O runner de navegador inicia o Streamlit isoladamente na porta 8517.
O ZIP é gerado mesmo que ocorram falhas, em
results/testes-visuais-para-revisao.zip (ou variante com timestamp, caso o
anterior esteja aberto no Windows).

As auditorias estão documentadas em
[primeira rodada](auditoria_cliente_2026-11-23.md),
[segunda rodada](auditoria_cliente_2026-11-23_rodada2.md) e
[terceira rodada](auditoria_cliente_2026-11-23_rodada3.md) e
[quarta rodada](auditoria_cliente_2026-11-23_rodada4.md).
Os casos corrigidos nos testes precisam ser reexecutados; requisitos
que revelaram problemas visuais permanecem reprováveis.

O cenário **CL-B03 exige o CSV original** em
data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv. Se estiver ausente, esse
teste registra skipped. Nesse caso, a auditoria E2E fica **pendente**, mesmo
com os demais testes aprovados.

Esta nova suíte não depende das imagens antigas mono-* nem exige
test:visual:update. Se futuros screenshots comparativos forem adotados,
deverão ter novas referências client-* revisadas conscientemente.

## Aceite

A auditoria só está concluída com pytest sem falhas, Playwright sem falhas
nem flakiness, CL-B03 executado com dataset, screenshots CL-* revisadas e
evidências do ZIP correspondendo ao mesmo HEAD Git. Um teste ignorado,
mesmo que proposital, deve permanecer explicitamente registrado no relatório.
