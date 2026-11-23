# Sétima auditoria — controle Tempo do Cliente (23/11/2026)

## Evidências da execução anterior

Arquivos recebidos: imagem `image(20261123-064452).png`, log da execução
e pacote `testes-visuais-para-revisao(20261123-064630).zip`.

- **pytest:** 77/77 aprovados.
- **Playwright:** 43/44 aprovados (um único erro em CL-F11).
- CL-F02 e CL-F08, que falhavam com `31 meses`, **passaram** depois da
  separação do número e da unidade.
- CL-F11 esperava `24` após colar `24 meses`, recebeu `242`.
- A imagem mostra a unidade ligeiramente acima da base óptica dos dígitos.

## Análise de causa

O evento do teste CL-F11 é uma única colagem sintética. A lógica atual usa
`setRangeText()` e emite um `input` para sincronizar. Em Chromium,
foi reproduzido exatamente o valor **242** com **dois listeners de paste/input
no mesmo input**: a primeira instância insere 24; a segunda insere outra vez;
o sanitizador corta para três dígitos.

Este experimento demonstra um mecanismo que produz exatamente o erro
observado. A execução completa não registra a lista de listeners, portanto
o trace isoladamente não identifica qual remontagem deixou um listener
anterior ativo.

A nova implementação impede a duplicidade na origem: um símbolo
`Symbol.for("n3.tenure.activeMount")` identifica o controller ativo
**no próprio root HTML**. A montagem seguinte aborta os listeners da
montagem anterior mesmo que o Streamlit ainda não tenha executado o cleanup.
Quando o cleanup antigo chega, ele não remove a instância mais nova.

## Ajuste tipográfico

A unidade continua fora do input, com a mesma fonte, 14 px e line-height
de 20 px. O `translateY` do `span` agora recebe **+1 px em relação ao
input**, para alinhar a base óptica da palavra aos dígitos. Não modifica
altura do campo, margens nem o espaçamento horizontal.

## Cobertura

- **CL-F11** continua validando colagens de `24 meses` e `1 mês`,
  caracteres inválidos e valor vazio.
- **CL-F12**, novo, remonta o componente sem chamar o cleanup anterior,
  executa uma única colagem e verifica uma única atualização no estado.
  Também executa um cleanup antigo fora de ordem para conferir a
  sobrevivência da montagem atual. Esse teste teria falhado com o mecanismo
  duplicado.
- **CL-F10** (1440 e 390 px) agora verifica diferença vertical computada
  de 1 px entre dígitos e unidade, preservando fonte e line-height.
- **pytest** exige o contrato de montagem única com AbortController.

## Validação e aceite

O caso duplicado foi reproduzido em Chromium isolado, com o valor 242, e o
padrão de montagem única produziu 24 e uma única atualização. A verificação
estática dos arquivos foi realizada. Os resultados de pytest e Playwright
relatados acima pertencem à **versão anterior**.

A aprovação da nova versão depende de uma execução local completa:

    git pull
    python -m pytest -q
    npm run test:visual

**Expectativa:** pytest com os mesmos 77 casos e Playwright com
**45 cenários** (44 anteriores mais CL-F12). Não declarar a auditoria
aprovada enquanto houver casos falhos ou capturas sem inspeção.
