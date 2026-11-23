# Auditoria inicial do painel Cliente — 23/11/2026

## Execução analisada

Origem: arquivo `testes-visuais-para-revisao(20261123-043737).zip`
e registro de PowerShell enviados após o commit `f501501`.
O resultado reflete aquela execução local, antes da revisão da suíte abaixo.

- pytest: **76 aprovados** em 17,48 s.
- Playwright: **18 aprovados / 15 falhos / 0 ignorados / 0 instáveis**, em 8,4 min.
- O cenário CL-B03 de execução real do algoritmo genético **passou**.
- Os 15 erros concentram-se em 7 IDs-base: F02, F05, F06,
  L01 (seis resoluções), L04, P01 e P02 (quatro resoluções).

## Classificação das falhas

| ID | Evidência | Diagnóstico | Correção na suíte |
|---|---|---|---|
| CL-L01 desktop | Espera borda direita do Cliente em 12 px da janela; encontra 1048 px em 1440 | Referência errada: Cliente ocupa a coluna esquerda; comparar a direita do **workspace** ao limite da janela | Passou a medir os dois painéis e sua relação |
| CL-L01 390 | Espera 44 px; mede 48 px | Incompatibilidade real entre media query de 44 px e regra mais específica com altura mínima 48 px | **Permanece como falha legítima** até corrigir a aplicação |
| CL-L01, 1024 | Rótulos Contrato e Cobrança quebram linha na captura | Problema visual real ainda não coberto pelo teste anterior | Adicionada verificação explícita de uma linha nos rótulos rápidos |
| CL-F02 | Ctrl+A imediatamente após clicar resulta em 31 meses ao tentar digitar 1 | Possível disputa com requestAnimationFrame que reposiciona o cursor | Helper passa a sincronizar antes de substituir; CL-F08 testa a interação rápida separadamente |
| CL-F05 | Espera 95,50 e encontra 95.50 | `input type=number` guarda ponto como separador no DOM | Passa a validar o valor interno 95.50 e edição 101.50 |
| CL-F06 | Espera pelo wrapper BaseWeb durante 4 minutos | Streamlit instalado usa `data-testid=stNumberInputContainer` (React Aria) | Atualizado seletor; mede o container efetivamente presente |
| CL-F06/F07 | Captura mostra cobrança sem ações −/+ | Ausência real de stepper na versão atual do número | CL-F07 exige explicitamente dois controles, sem tolerar ausência |
| CL-L04 | Regex acusa `0px -2px` como barra lateral | Falso positivo do sublinhado inferior da aba | Regex passa a rejeitar sombras **laterais**, preservando sublinhado legítimo |
| CL-P01 | Consulta encontra 10 botões após cinco perfis; captura mostra cinco | O seletor também contempla elementos não visíveis | Localizadores compartilhados filtram `:visible` |
| CL-P02 | Primeiro elemento não possui boundingBox nas quatro larguras | Localizador escolhe botão não visível da árvore | Mesmo filtro de visibilidade dos perfis e ações |

**Divergência CSS identificada:** o código da aplicação ainda define a caixa
do número com o seletor `[data-baseweb="input"]`, enquanto o DOM efetivo
contém `[data-testid="stNumberInputContainer"]`. A suíte precisa validar
a aparência real desse widget e detectar eventuais diferenças de altura,
raio, fundo e ícones. O problema não deve ser escondido por tolerâncias maiores.

## Intervenção nesta revisão

Alterações exclusivamente em testes e documentação, preservando
`streamlit_app.py`, componentes, dados e modelos. As verificações que
partiam de hipóteses incorretas foram ajustadas; os problemas visuais
confirmados mantêm asserções capazes de falhar.

O primeiro retorno da suíte revisada ainda precisa ser executado no
Windows com o CSV local. Esse retorno dirá quais hipóteses de defeito
persistem. Nenhum cenário corrigido foi declarado aprovado sem execução.

## Próxima execução sugerida

    git pull
    python -m pytest -q
    npm run test:visual

Revisar especialmente CL-L01, CL-F02, CL-F06, CL-F07 e CL-F08;
anexar o novo ZIP com screenshots e traces.
