import { expect, test } from '@playwright/test';

// Inclui a proporção usual de projetor e os formatos desktop, tablet e celular.
const viewports = [
  { width: 1440, height: 900 },
  { width: 1366, height: 768 },
  { width: 1280, height: 720 },
  { width: 1024, height: 768 },
  { width: 768, height: 900 },
  { width: 390, height: 900 },
];

async function geometry(page, stage, testInfo) {
  const layout = await page.evaluate(() => {
    const bounds = selector => {
      const element = document.querySelector(selector);
      if (!element) return null;
      const box = element.getBoundingClientRect();
      const css = getComputedStyle(element);
      return {
        x: box.x, y: box.y, right: box.right, bottom: box.bottom,
        width: box.width, height: box.height, overflowY: css.overflowY, position: css.position, display: css.display,
        scrollHeight: element.scrollHeight, clientHeight: element.clientHeight,
        scrollWidth: element.scrollWidth, clientWidth: element.clientWidth,
        marginBottom: css.marginBottom,
      };
    };
    const root = document.scrollingElement || document.documentElement;
    return {
      width: window.innerWidth, height: window.innerHeight,
      scrollWidth: root.scrollWidth, clientWidth: root.clientWidth,
      scrollHeight: root.scrollHeight, clientHeight: root.clientHeight,
      row: bounds('[data-testid="stHorizontalBlock"]:has(.st-key-dashboard-client):has(.st-key-dashboard-workspace)'),
      client: bounds('.st-key-dashboard-client'),
      workspace: bounds('.st-key-dashboard-workspace'),
      clientTitle: bounds('.st-key-dashboard-client .churn-panel-heading'),
      workspaceTitle: bounds('.st-key-dashboard-workspace .churn-workspace-heading .churn-panel-heading'),
      comparisonTop: bounds('.st-key-dashboard-workspace .churn-comparison'),
      clientFieldsTop: bounds('.st-key-dashboard-client-fields'),
      tenureInput: null, // Campo encapsulado no Shadow DOM do componente v2.
      tenureControl: bounds('.st-key-dashboard-tenure-control'),
      internetInput: bounds('.st-key-dashboard-quick-fields [aria-label="Serviço de internet"]'),
      contractInput: bounds('.st-key-dashboard-quick-fields [aria-label="Tipo de contrato"]'),
      monthlyInput: bounds('.st-key-dashboard-quick-fields [aria-label="Cobrança mensal"]'),
      fields: bounds('.st-key-dashboard-client-fields'),
      footer: bounds('.st-key-dashboard-client-footer'),
      button: bounds('.st-key-dashboard-client-footer button'),
      clientColumn: bounds('[data-testid="stColumn"]:has(.st-key-dashboard-client)'),
      workspaceColumn: bounds('[data-testid="stColumn"]:has(.st-key-dashboard-workspace)'),
      clientBlock: bounds('[data-testid="stColumn"]:has(.st-key-dashboard-client) > [data-testid="stVerticalBlock"]'),
      clientWrapper: bounds('[data-testid="stColumn"]:has(.st-key-dashboard-client) > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"]'),
      workspaceBlock: bounds('[data-testid="stColumn"]:has(.st-key-dashboard-workspace) > [data-testid="stVerticalBlock"]'),
      workspaceWrapper: bounds('[data-testid="stColumn"]:has(.st-key-dashboard-workspace) > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"]'),
      comparison: bounds('.churn-comparison'),
      tabs: bounds('.st-key-dashboard-mobile-detail'),
      chart: bounds('.st-key-dashboard-desktop-detail .churn-chart'),
      chartPlot: bounds('.st-key-dashboard-desktop-detail .churn-chart-plot'),
      chartCaption: bounds('.st-key-dashboard-desktop-detail .churn-chart-caption'),
      chartAxisX: bounds('.st-key-dashboard-desktop-detail .churn-chart-axis-x'),
      technical: bounds('.st-key-dashboard-desktop-detail .churn-technical'),
      chromosome: bounds('.st-key-dashboard-desktop-detail .churn-chromosome'),
      chromosomeMarkdown: bounds('.st-key-dashboard-selection-section [data-testid="stMarkdownContainer"]:has(.churn-chromosome)'),
      technicalMarkdown: bounds('.st-key-dashboard-selection-section [data-testid="stMarkdownContainer"]:has(.churn-technical)'),
      monitor: bounds('.st-key-dashboard-desktop-detail .churn-console'),
      consoleMarkdown: bounds('.st-key-dashboard-desktop-detail .st-key-dashboard-monitor-section [data-testid="stMarkdownContainer"]:has(.churn-console)'),
      monitorTitle: bounds('.st-key-dashboard-desktop-detail .churn-monitor-title'),
      monitorProgress: bounds('.st-key-dashboard-desktop-detail [data-testid="stProgress"]'),
      logDownload: bounds('.st-key-dashboard-desktop-detail [data-testid="stDownloadButton"] button'),
      selection: bounds('.st-key-dashboard-desktop-detail .st-key-dashboard-selection-section'),
      monitorSection: bounds('.st-key-dashboard-desktop-detail .st-key-dashboard-monitor-section'),
      analysisSection: bounds('.st-key-dashboard-desktop-detail .st-key-dashboard-analysis-section'),
      mobileWrapper: bounds('.st-key-dashboard-workspace > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-mobile-detail)'),
      desktopDetail: bounds('.st-key-dashboard-desktop-detail'),
    };
  });
  // Os locators do Playwright atravessam Shadow DOM, document.querySelector não.
  const tenureBox = await page.getByRole('textbox', { name: 'Tempo como cliente' }).boundingBox();
  layout.tenureInput = tenureBox && {
    x:tenureBox.x, y:tenureBox.y, width:tenureBox.width, height:tenureBox.height,
    right:tenureBox.x + tenureBox.width, bottom:tenureBox.y + tenureBox.height,
  };
  await testInfo.attach(`geometria-${stage}-${layout.width}x${layout.height}.json`, {
    body: JSON.stringify(layout, null, 2), contentType: 'application/json',
  });
  expect(layout.row, `${stage}: grade principal ausente`).toBeTruthy();
  expect(layout.row.position, `${stage}: grade deve ficar ancorada à viewport`).toBe('fixed');
  expect(layout.row.y, `${stage}: espaço vazio acima da grade`).toBeLessThanOrEqual(16);
  expect(layout.row.bottom, `${stage}: grade extrapola a altura da janela`)
    .toBeLessThanOrEqual(layout.height - 4);
  expect(layout.client, `${stage}: Cliente ausente`).toBeTruthy();
  expect(layout.workspace, `${stage}: Previsão ausente`).toBeTruthy();
  expect(layout.clientTitle, `${stage}: título Cliente ausente`).toBeTruthy();
  expect(layout.workspaceTitle, `${stage}: título Previsão ausente`).toBeTruthy();
  const pagePad = layout.width <= 620 ? 8 : layout.width <= 900 ? 10 : 12;
  for (const [edge, measured] of [
    ['superior',layout.row.y], ['inferior',layout.height - layout.row.bottom],
    ['esquerda',layout.row.x], ['direita',layout.width - layout.row.right],
  ]) {
    expect(Math.abs(measured - pagePad), `${stage}: margem ${edge} desigual`).toBeLessThanOrEqual(2);
  }
  expect(layout.clientFieldsTop, `${stage}: conteúdo Cliente ausente`).toBeTruthy();
  expect(layout.comparisonTop, `${stage}: comparação abaixo de Previsão ausente`).toBeTruthy();
  for (const [panel, heading, content] of [
    ['Cliente', layout.clientTitle, layout.clientFieldsTop],
    ['Previsão', layout.workspaceTitle, layout.comparisonTop],
  ]) {
    const gap = content.y - heading.bottom;
    expect(gap, `${stage}: conteúdo invade a faixa de título em ${panel}`).toBeGreaterThanOrEqual(-2);
    const box = panel === 'Cliente' ? layout.client : layout.workspace;
    const topGap = heading.y - box.y;
    expect(Math.abs(gap - topGap), `${stage}: espaços acima e abaixo do título diferem em ${panel}`)
      .toBeLessThanOrEqual(2);
  }
  expect(layout.clientTitle.y - layout.client.y, `${stage}: título Cliente muito distante do topo`)
    .toBeLessThanOrEqual(27);
  expect(layout.workspaceTitle.y - layout.workspace.y, `${stage}: título Previsão muito distante do topo`)
    .toBeLessThanOrEqual(27);
  // O texto mantém o centro de cada painel independentemente do indicador de execução.
  for (const [panelName, headingName] of [['client', 'clientTitle'], ['workspace', 'workspaceTitle']]) {
    const panel = layout[panelName], heading = layout[headingName];
    expect(Math.abs(heading.x + heading.width / 2 - panel.x - panel.width / 2),
      `${stage}: título descentralizado em ${panelName}`).toBeLessThanOrEqual(2);
  }
  expect(layout.scrollHeight, `${stage}: página com rolagem vertical`).toBeLessThanOrEqual(layout.clientHeight + 2);
  expect(layout.scrollWidth, `${stage}: página com rolagem horizontal`).toBeLessThanOrEqual(layout.clientWidth + 2);
  for (const name of ['client', 'workspace']) {
    const element = layout[name];
    expect(element.x, `${stage}: ${name} sai à esquerda`).toBeGreaterThanOrEqual(-2);
    expect(element.y, `${stage}: ${name} sai acima`).toBeGreaterThanOrEqual(-2);
    expect(element.right, `${stage}: ${name} sai à direita`).toBeLessThanOrEqual(layout.width + 2);
    expect(element.bottom, `${stage}: ${name} sai abaixo`).toBeLessThanOrEqual(layout.height + 2);
    expect(element.height, `${stage}: ${name} sem espaço útil`).toBeGreaterThan(100);
    expect(element.overflowY).toMatch(/auto|hidden|scroll/);
  }
  for (const name of ['fields', 'footer', 'button']) {
    expect(layout[name], `${stage}: ${name} ausente`).toBeTruthy();
    expect(layout[name].y, `${stage}: ${name} acima do Cliente`).toBeGreaterThanOrEqual(layout.client.y - 2);
    expect(layout[name].bottom, `${stage}: ${name} abaixo do Cliente`).toBeLessThanOrEqual(layout.client.bottom + 2);
  }
  expect(layout.fields.overflowY, `${stage}: campos devem ter rolagem própria`).toMatch(/auto|scroll/);
  expect(layout.tenureInput, `${stage}: campo de meses ausente`).toBeTruthy();
  expect(layout.tenureInput.width, `${stage}: campo de meses estreito demais`)
    .toBeGreaterThanOrEqual(85);
  if (layout.width === 768) {
    for (const name of ['internetInput', 'contractInput', 'monthlyInput']) {
      expect(layout[name], `${stage}: campo rápido ausente: ${name}`).toBeTruthy();
      expect(layout[name].right, `${stage}: ${name} ultrapassa o formulário`)
        .toBeLessThanOrEqual(layout.fields.right + 2);
      expect(layout[name].width, `${stage}: ${name} continua comprimido`)
        .toBeGreaterThanOrEqual(165);
    }
  }
  if (layout.width <= 620) {
    expect(layout.client.bottom, `${stage}: painéis móveis sobrepostos`).toBeLessThanOrEqual(layout.workspace.y + 2);
    for (const [wrapper, column] of [
      ['clientBlock', 'clientColumn'], ['clientWrapper', 'clientColumn'],
      ['workspaceBlock', 'workspaceColumn'], ['workspaceWrapper', 'workspaceColumn'],
    ]) {
      expect(layout[wrapper], `${stage}: ${wrapper} ausente`).toBeTruthy();
      expect(layout[wrapper].bottom, `${stage}: ${wrapper} ultrapassa sua coluna`)
        .toBeLessThanOrEqual(layout[column].bottom + 2);
    }
    expect(layout.tabs.height, `${stage}: abas móveis sem altura útil`).toBeGreaterThan(100);
  } else {
    // A visualização móvel não pode ocupar a quarta linha da grade desktop.
    expect(layout.mobileWrapper, `${stage}: wrapper móvel ausente`).toBeTruthy();
    expect(layout.mobileWrapper.display, `${stage}: wrapper móvel ocupa a grade desktop`).toBe('none');
    expect(layout.comparison.width, `${stage}: comparação usa pouco espaço horizontal`)
      .toBeGreaterThan(layout.workspace.width * 0.80);
    for (const name of ['comparison', 'chart', 'technical', 'monitor', 'selection', 'monitorSection', 'analysisSection']) {
      expect(layout[name], `${stage}: ${name} ausente`).toBeTruthy();
      expect(layout[name].bottom, `${stage}: ${name} extrapola área analítica`)
        .toBeLessThanOrEqual(layout.workspace.bottom + 2);
    }
    // Validar se o conteúdo está dentro do trilho a que pertence, inclusive
    // quando um overflow hidden poderia esconder uma sobreposição.
    expect(layout.chart.bottom, `${stage}: gráfico invade a seleção`)
      .toBeLessThanOrEqual(layout.selection.y + 2);
    if (layout.width === 1024 && layout.height === 768) {
      for (const part of ['chartPlot', 'chartAxisX', 'chartCaption']) {
        expect(layout[part], `${stage}: parte do gráfico ausente: ${part}`).toBeTruthy();
        expect(layout[part].bottom, `${stage}: gráfico recortado em ${part}`)
          .toBeLessThanOrEqual(layout.chart.bottom + 2);
      }
      expect(layout.chart.scrollHeight, `${stage}: conteúdo do gráfico excede sua altura`)
        .toBeLessThanOrEqual(layout.chart.clientHeight + 2);
    }
    expect(layout.consoleMarkdown, `${stage}: contêiner Markdown do console ausente`).toBeTruthy();
    expect(layout.consoleMarkdown.marginBottom, `${stage}: margem negativa desloca o console`).toBe('0px');
    expect(layout.monitor.bottom, `${stage}: console fica oculto ou cortado`)
      .toBeLessThanOrEqual(layout.monitorSection.bottom + 2);
    expect(layout.monitorTitle.bottom, `${stage}: título do monitor sobrepõe console`)
      .toBeLessThanOrEqual(layout.monitor.y + 2);
    if (stage !== 'Inicial') {
      expect(layout.monitorProgress, `${stage}: progresso do monitor ausente`).toBeTruthy();
      expect(layout.monitorTitle.bottom + 2, `${stage}: título e progresso sobrepostos`)
        .toBeLessThanOrEqual(layout.monitorProgress.y);
    }
    expect(layout.monitorSection.scrollHeight, `${stage}: monitor excede sua seção`)
      .toBeLessThanOrEqual(layout.monitorSection.clientHeight + 2);
    expect(layout.technical.bottom, `${stage}: métricas saem da seleção`)
      .toBeLessThanOrEqual(layout.selection.bottom + 2);
    expect(layout.selection.scrollHeight, `${stage}: seleção oculta conteúdo técnico`)
      .toBeLessThanOrEqual(layout.selection.clientHeight + 2);
    if (stage === 'Concluído' || stage === 'Editado') {
      expect(layout.logDownload, `${stage}: download do log ausente`).toBeTruthy();
      expect(layout.logDownload.y, `${stage}: download do log acima do monitor`)
        .toBeGreaterThanOrEqual(layout.monitorSection.y - 2);
      expect(layout.logDownload.bottom, `${stage}: download do log cortado`)
        .toBeLessThanOrEqual(layout.monitorSection.bottom + 2);
      expect(layout.logDownload.right, `${stage}: download do log excede o monitor`)
        .toBeLessThanOrEqual(layout.monitorSection.right + 2);
      const downloadButton = page.getByRole('button', { name: 'Baixar log', exact: true });
      await expect(downloadButton).toBeVisible();
      const downloadStyle = await downloadButton.evaluate(el => ({
        whiteSpace: getComputedStyle(el).whiteSpace,
        scrollHeight: el.scrollHeight, clientHeight: el.clientHeight,
      }));
      expect(downloadStyle.whiteSpace, `${stage}: texto do download quebra linha`).toBe('nowrap');
      expect(downloadStyle.scrollHeight, `${stage}: botão de download cortado`)
        .toBeLessThanOrEqual(downloadStyle.clientHeight + 2);
      if (layout.width >= 1000 && layout.height <= 760) {
        expect(layout.monitorSection.scrollHeight, `${stage}: conteúdo do monitor excede a altura disponível`)
          .toBeLessThanOrEqual(layout.monitorSection.clientHeight + 2);
      }
    }
    if (layout.width >= 1000) {
      expect(Math.abs(layout.selection.y - layout.monitorSection.y),
        `${stage}: seleção e monitor devem compartilhar a faixa inferior`).toBeLessThanOrEqual(2);
      expect(layout.chart.height, `${stage}: gráfico sem altura suficiente para projeção`)
        .toBeGreaterThanOrEqual(130);
      expect(layout.chromosome, `${stage}: cromossomo ausente`).toBeTruthy();
      expect(layout.chromosome.right, `${stage}: cromossomo sobrepõe métricas`)
        .toBeLessThanOrEqual(layout.technical.x + 2);
      if (layout.width <= 1150) {
        for (const name of ['chromosomeMarkdown', 'technicalMarkdown']) {
          expect(layout[name], `${stage}: ${name} ausente`).toBeTruthy();
          expect(layout[name].marginBottom, `${stage}: margem negativa causa sobreposição`).toBe('0px');
        }
      }
      for (const name of ['chromosome', 'technical']) {
        expect(layout[name].bottom, `${stage}: ${name} sai da seção de seleção`)
          .toBeLessThanOrEqual(layout.selection.bottom + 2);
        expect(layout[name].right, `${stage}: ${name} sai horizontalmente da seleção`)
          .toBeLessThanOrEqual(layout.selection.right + 2);
      }
    } else {
      expect(layout.selection.bottom, `${stage}: seleção sobrepõe o monitor`)
        .toBeLessThanOrEqual(layout.monitorSection.y + 2);
    }
  }
}

async function snapshot(page, testInfo, name) {
  await testInfo.attach(name, {
    body: await page.screenshot({ fullPage: false, animations: 'disabled' }),
    contentType: 'image/png',
  });
}

for (const { width, height } of viewports) {
  test(`${width}x${height} — interface monocromática para projeção`, async ({ browser }, testInfo) => {
    const context = await browser.newContext({
      viewport: { width, height }, deviceScaleFactor: 1,
      locale: 'pt-BR', colorScheme: 'dark',
    });
    const page = await context.newPage();
    const mobile = width <= 620;
    const suffix = `${width}x${height}`;
    try {
      await test.step('Abertura e hierarquia do dashboard', async () => {
        await page.goto('/', { waitUntil: 'domcontentloaded' });
        // No início o Streamlit exibe um esqueleto com Source Sans.
        // Aguardar a primeira renderização antes de ler o estilo calculado.
        await expect(page.getByRole('heading', { name: 'Cliente', exact: true }))
          .toBeVisible({ timeout: 30_000 });
        await expect(page.getByRole('button', { name: 'Calcular previsão' }))
          .toBeVisible();
        // Esperar efetivamente a fonte customizada carregar. Apenas verificar
        // fontFamily permitiria uma aprovação mesmo com fallback ativo.
        await page.evaluate(async () => {
          await document.fonts.load('400 16px "Familjen Grotesk"');
          await document.fonts.ready;
        });
        const fontState = await page.locator('.stApp').evaluate(el => ({
          family: getComputedStyle(el).fontFamily,
          loaded: [...document.fonts].some(face =>
            face.family.replace(/["']/g, '').trim() === 'Familjen Grotesk' &&
            face.status === 'loaded'),
        }));
        expect(fontState.family, 'A interface deve declarar Familjen Grotesk')
          .toContain('Familjen Grotesk');
        expect(fontState.loaded, 'O navegador deve carregar Familjen Grotesk, sem fallback')
          .toBe(true);
        await expect(page.locator('.churn-topbar')).toHaveCount(0);
        await expect(page.locator('.churn-chart-descriptor')).toHaveCount(0);
        await expect(page.getByRole('combobox', { name: 'Características', exact: true })).toHaveCount(0);
        await expect(page.locator('.st-key-dashboard-detail-tabs [role="tab"]')).toHaveCount(4);
        for (const name of ['Perfil', 'Conta', 'Serviços', 'Extras']) {
          await expect(page.locator('.st-key-dashboard-detail-tabs').getByRole('tab', { name, exact: true }))
            .toHaveCount(1);
        }
        await expect(page.locator('.churn-workspace-heading[data-run-state="idle"]')).toBeVisible();
        // A faixa interna fica centralizada, discreta e imediatamente acima do conteúdo.
        for (const name of ['Cliente', 'Previsão']) {
          const heading = page.getByRole('heading', { name, exact: true });
          const appearance = await heading.evaluate(el => {
            const css = getComputedStyle(el);
            const range = document.createRange();
          range.selectNodeContents(el);
          const text = range.getBoundingClientRect();
          const rect = el.getBoundingClientRect();
          return {
            color:css.color, align:css.textAlign, height:rect.height,
            textCenter:text.x + text.width / 2,
            headingCenter:rect.x + rect.width / 2,
            before:getComputedStyle(el,'::before').content,
            after:getComputedStyle(el,'::after').content,
          };
        });
          expect(appearance.color, `${name}: título deve usar a cor do contorno`)
            .toBe('rgb(85, 88, 93)');
          expect(appearance.align).toBe('center');
          expect(appearance.height).toBeLessThanOrEqual(21);
          expect(Math.abs(appearance.textCenter - appearance.headingCenter),
            `${name}: texto fora do centro`).toBeLessThanOrEqual(2);
          expect(['none', 'normal']).toContain(appearance.before);
          expect(['none', 'normal']).toContain(appearance.after);
        }
        await expect(page.locator('.churn-run-icon')).toHaveCount(0);
        await expect(page.locator('.churn-comparison .churn-state')).toHaveCount(0);
        await expect(page.getByRole('textbox', { name: 'Tempo como cliente' })).toHaveValue('3 meses');
        const restore = page.getByRole('button', { name: 'Restaurar perfil' });
        await expect(restore).toBeVisible();
        const [restoreBox, profileBox] = await Promise.all([
          restore.boundingBox(), page.getByRole('combobox', { name: 'Perfil de exemplo' }).boundingBox(),
        ]);
        expect(Math.abs(restoreBox.y - profileBox.y), 'Ícone de restauro fora do alinhamento').toBeLessThanOrEqual(3);
        expect(Math.abs(restoreBox.height - profileBox.height), 'Ícone de restauro com altura diferente').toBeLessThanOrEqual(3);
        const tabsBar = page.locator('.st-key-dashboard-detail-tabs [role="tablist"]');
        const lastTab = page.locator('.st-key-dashboard-detail-tabs').getByRole('tab', { name: 'Extras' });
        const [tabBounds, listBounds] = await Promise.all([lastTab.boundingBox(), tabsBar.boundingBox()]);
        expect(tabBounds, 'A última aba deve existir').toBeTruthy();
        expect(listBounds, 'A navegação de abas deve existir').toBeTruthy();
        expect(tabBounds.x + tabBounds.width, 'A última aba fica truncada')
          .toBeLessThanOrEqual(listBounds.x + listBounds.width + 2);
        // O campo de meses é um input único; a faixa de botões replica Cobrança.
        const time = await page.locator('.n3-tenure-field').evaluate(field => {
          const input = field.querySelector('input');
          const buttons = [...field.querySelectorAll('button')];
          const bounds = el => { const r = el.getBoundingClientRect(); return {y:r.y,height:r.height,width:r.width}; };
          return {
            field:bounds(field), input:bounds(input), buttons:buttons.map(bounds),
            radius:getComputedStyle(field).borderTopLeftRadius,
            font:getComputedStyle(input).fontSize,
            line:getComputedStyle(input).lineHeight,
            backgrounds:buttons.map(button => getComputedStyle(button).backgroundColor),
            value:input.value,
          };
        });
        const charge = await page.locator('[data-testid="stNumberInput"]:has(input[aria-label="Cobrança mensal"])')
          .evaluate(root => {
            const field = root.querySelector('[data-baseweb="input"]');
            const input = root.querySelector('input');
            const buttons = [...root.querySelectorAll('button')];
            const bounds = el => { const r = el.getBoundingClientRect(); return {y:r.y,height:r.height,width:r.width}; };
            return {
              field:bounds(field), input:bounds(input), buttons:buttons.map(bounds),
              radius:getComputedStyle(field).borderTopLeftRadius,
              font:getComputedStyle(input).fontSize,
              line:getComputedStyle(input).lineHeight,
              backgrounds:buttons.map(b => getComputedStyle(b).backgroundColor),
            };
          });
        expect(time.value).toBe('3 meses');
        for (const item of [time, charge]) {
          expect(item.buttons).toHaveLength(2);
          expect(Math.abs(item.field.height - 42)).toBeLessThanOrEqual(2);
          expect(Math.abs(item.input.y + item.input.height / 2 - item.field.y - item.field.height / 2),
            'Valor verticalmente deslocado').toBeLessThanOrEqual(2);
          expect(parseFloat(item.radius)).toBeCloseTo(4, 0);
          expect(Math.abs(item.buttons[0].width - item.buttons[1].width)).toBeLessThanOrEqual(1);
          expect(item.backgrounds).toEqual(['rgb(14, 16, 19)', 'rgb(14, 16, 19)']);
        }
        expect(Math.abs(time.field.height - charge.field.height)).toBeLessThanOrEqual(1);
        expect(time.font).toBe(charge.font);
        expect(time.line).toBe(charge.line);
        expect(time.buttons.map(button => button.width)).toEqual(charge.buttons.map(button => button.width));
        const selector = await page.locator('.st-key-dashboard-quick-fields [data-baseweb="select"] > div')
          .first().evaluate(el => ({height:el.getBoundingClientRect().height,
                                    radius:getComputedStyle(el).borderTopLeftRadius}));
        expect(Math.abs(selector.height - time.field.height)).toBeLessThanOrEqual(2);
        expect(parseFloat(selector.radius)).toBeCloseTo(4, 0);
        await expect(page.getByRole('heading', { name: 'Cliente', exact: true })).toBeVisible();
        await expect(page.getByRole('heading', { name: 'Previsão', exact: true })).toBeVisible();
        await expect(page.getByRole('heading', { name: 'Previsão do cliente' })).toHaveCount(0);
        await expect(page.getByRole('button', { name: 'Calcular previsão' })).toBeEnabled();
        await expect(page.locator('.churn-comparison .churn-model')).toHaveCount(2);
        await expect(page.locator('.churn-prediction-value').first()).toHaveText('—');
        await expect(page.locator('.churn-bit')).toHaveCount(38); // desktop + abas móveis
        const black = await page.locator('.stApp').evaluate(el => getComputedStyle(el).backgroundColor);
        expect(black, 'O fundo principal deve ser preto puro').toBe('rgb(0, 0, 0)');
        const whiteButton = await page.getByRole('button', { name: 'Calcular previsão' })
          .evaluate(el => getComputedStyle(el).backgroundColor);
        expect(whiteButton, 'O botão de cálculo deve ser branco').toBe('rgb(245, 245, 245)');
        if (mobile) {
          await expect(page.getByRole('tab', { name: 'Análise' })).toBeVisible();
          await expect(page.getByRole('tab', { name: 'Execução' })).toBeVisible();
        }
        await geometry(page, 'Inicial', testInfo);
        await page.mouse.move(0, 0);
        await expect(page).toHaveScreenshot(`mono-01-inicial-${suffix}.png`, { fullPage: false });
      });

      let runningIconX = null;
      await test.step('Avaliações genéticas reais e monitor atualizado', async () => {
        await page.getByRole('button', { name: 'Calcular previsão' }).click();
        await expect(page.locator('.churn-workspace-heading[data-run-state="running"]')).toBeVisible();
        await expect(page.getByRole('status', { name: 'Executando previsão' })).toBeVisible();
        runningIconX = await page.locator('.churn-run-spinner').evaluate(el => {
          const box = el.getBoundingClientRect();
          return box.x + box.width / 2;
        });
        await expect(page.locator('.churn-console').first()).toContainText(/\[G\d{2}\]/, { timeout: 120_000 });
        await expect(page.locator('.churn-bit')).toHaveCount(38);
        if (mobile) {
          await page.getByRole('tab', { name: 'Execução' }).click();
          await expect(page.locator('.st-key-dashboard-mobile-detail .churn-console')).toBeVisible();
        }
        await snapshot(page, testInfo, `mono-02-processamento-${suffix}.png`);
        await geometry(page, 'Processamento', testInfo);
      });

      await test.step('Comparação, gráfico e métricas da execução completa', async () => {
        await expect(page.locator('.churn-workspace-heading[data-run-state="complete"]')).toBeVisible({ timeout: 180_000 });
        const runMarkAlignment = await page.locator('.churn-workspace-heading').evaluate(header => {
          const icon = header.querySelector('.churn-run-icon');
          const a = header.getBoundingClientRect();
          const b = icon?.getBoundingClientRect();
          return b ? Math.abs(a.y + a.height / 2 - b.y - b.height / 2) : null;
        });
        expect(runMarkAlignment, 'Indicador final não está alinhado ao título').not.toBeNull();
        expect(runMarkAlignment).toBeLessThanOrEqual(2);
        await expect(page.getByRole('status', { name: 'Previsão concluída' })).toBeVisible();
        const completedIconX = await page.locator('.churn-run-check').evaluate(el => {
          const box = el.getBoundingClientRect();
          return box.x + box.width / 2;
        });
        expect(Math.abs(completedIconX - runningIconX), 'Check mudou de posição horizontal')
          .toBeLessThanOrEqual(2);
        const checkStyle = await page.locator('.churn-run-check').first().evaluate(el => ({
          radius: getComputedStyle(el).borderRadius,
          border: getComputedStyle(el).borderWidth,
          check: getComputedStyle(el, '::before').borderRightWidth,
        }));
        expect(checkStyle.border).toBe('2px');
        expect(checkStyle.check).toBe('2px');
        expect(parseFloat(checkStyle.radius)).toBeGreaterThan(0);
        await expect(page.locator('.churn-comparison .churn-state')).toHaveCount(0);
        await expect(page.locator('.churn-prediction-value').first()).toContainText(/\d+,\d{2}%/);
        await expect(page.locator('.churn-prediction-value').last()).toContainText(/\d+,\d{2}%/);
        await expect(page.locator('.churn-outcome')).toHaveCount(2);
        await expect(page.locator('.churn-console').first()).toContainText('[FIM]');
        await expect(page.locator('.churn-metric')).toHaveCount(6);
        await expect(page.locator('.churn-chart-line')).toHaveCount(2);
        await expect(page.locator('.churn-technical').first()).toContainText('ΔF1');
        if (mobile) {
          await page.getByRole('tab', { name: 'Análise', exact: true }).click();
          await expect(page.locator('.st-key-dashboard-mobile-detail .churn-chart')).toBeVisible();
        }
        await geometry(page, 'Concluído', testInfo);
        await page.mouse.move(0, 0);
        await expect(page).toHaveScreenshot(`mono-03-concluido-${suffix}.png`, { fullPage: false });
      });

      await test.step('Edição do cliente invalida a previsão, preservando o experimento', async () => {
        const months = page.getByRole('textbox', { name: 'Tempo como cliente' });
        await months.click();
        await months.press('ControlOrMeta+A');
        await months.press('4');
        await expect(months).toHaveValue('4 meses');
        await expect(page.locator('.churn-comparison .churn-state')).toHaveText('Dados alterados');
        await expect(page.locator('.churn-workspace-heading[data-run-state="stale"]')).toBeVisible();
        await expect(page.locator('.churn-run-check')).toHaveCount(0);
        await expect(page.locator('.churn-prediction-value').first()).toHaveText('—');
        await expect(page.locator('.churn-technical').first()).toContainText('ΔF1');
        await expect(page.locator('.churn-technical').first())
          .not.toContainText('Os dados do cliente foram alterados');
        await expect(page.locator('.churn-console').first()).toContainText('[FIM]');
        await geometry(page, 'Editado', testInfo);
        await page.mouse.move(0, 0);
        await expect(page).toHaveScreenshot(`mono-04-editado-${suffix}.png`, { fullPage: false });
      });
    } finally {
      await context.close();
    }
  });
}

test('1024x768 — telefonia mantém dados das abas anteriores', async ({ browser }) => {
  const context = await browser.newContext({
    viewport: { width: 1024, height: 768 }, deviceScaleFactor: 1,
    locale: 'pt-BR', colorScheme: 'dark',
  });
  const page = await context.newPage();
  try {
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Cliente', exact: true })).toBeVisible();
    await page.locator('.st-key-dashboard-detail-tabs').getByRole('tab', { name: 'Serviços' }).click();
    await page.getByRole('combobox', { name: 'Serviço de telefone' }).click();
    await page.getByRole('option', { name: 'Não', exact: true }).click();
    await expect(page.locator('[data-testid="stException"]')).toHaveCount(0);
    const lines = page.getByRole('combobox', { name: 'Múltiplas linhas telefônicas' });
    await expect(lines).toHaveValue('Sem serviço telefônico');
    await expect(lines).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Calcular previsão' })).toBeEnabled();
  } finally {
    await context.close();
  }
});

test('1024x768 — abas do formulário e unidade do stepper', async ({ browser }) => {
  const context = await browser.newContext({
    viewport: { width: 1024, height: 768 }, deviceScaleFactor: 1,
    locale: 'pt-BR', colorScheme: 'dark',
  });
  const page = await context.newPage();
  try {
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Cliente', exact: true })).toBeVisible();
    const tabs = page.locator('.st-key-dashboard-detail-tabs');
    await expect(tabs.getByRole('tab')).toHaveCount(4);
    await tabs.getByRole('tab', { name: 'Conta', exact: true }).click();
    await expect(page.getByRole('combobox', { name: 'Método de pagamento' })).toBeVisible();
    await tabs.getByRole('tab', { name: 'Extras', exact: true }).click();
    await expect(page.getByRole('combobox', { name: 'Streaming de filmes' })).toBeVisible();
    await tabs.getByRole('tab', { name: 'Perfil', exact: true }).click();
    await expect(page.getByRole('combobox', { name: 'Gênero' })).toBeVisible();

    const months = page.getByRole('textbox', { name: 'Tempo como cliente' });
    await expect(months).toHaveValue('3 meses');
    await months.click();
    const caret = () => months.evaluate(input => ({
      start:input.selectionStart, end:input.selectionEnd,
      digits:input.value.match(/^\d+/)[0].length,
    }));
    let cursor = await caret();
    expect(cursor.start).toBe(cursor.digits);
    await months.press('End');
    cursor = await caret();
    expect(cursor.start).toBe(cursor.digits);
    await months.press('Delete');
    await expect(months).toHaveValue('3 meses');
    for (const [digits, formatted] of [
      ['1', '1 mês'], ['9', '9 meses'], ['10', '10 meses'],
      ['24', '24 meses'], ['120', '120 meses'],
    ]) {
      await months.click();
      await months.press('ControlOrMeta+A');
      await months.press('Backspace');
      for (const digit of digits) await months.press(digit);
      await expect(months).toHaveValue(formatted);
      const size = await months.evaluate(input => {
        const cs = getComputedStyle(input);
        const canvas = document.createElement('canvas');
        canvas.getContext('2d').font = cs.font;
        return {
          rendered:canvas.getContext('2d').measureText(input.value).width,
          available:input.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight),
        };
      });
      expect(size.rendered).toBeLessThanOrEqual(size.available + 1);
    }
    const plus = page.getByRole('button', { name: 'Aumentar um mês' });
    const minus = page.getByRole('button', { name: 'Diminuir um mês' });
    await plus.click();
    await expect(months).toHaveValue('121 meses');
    await minus.click();
    await expect(months).toHaveValue('120 meses');
    await months.fill('abc');
    await expect(months).toHaveValue('120 meses');
    await page.getByRole('button', { name: 'Restaurar perfil' }).click();
    await expect(months).toHaveValue('3 meses');
    await expect(page.getByRole('button', { name: 'Calcular previsão' })).toBeEnabled();
  } finally {
    await context.close();
  }
});


test('Fonte permanece disponível sem serviços externos', async ({ browser }) => {
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1,
    locale: 'pt-BR', colorScheme: 'dark',
  });
  await context.route('https://fonts.googleapis.com/**', route => route.abort());
  await context.route('https://fonts.gstatic.com/**', route => route.abort());
  const page = await context.newPage();
  try {
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Cliente', exact: true })).toBeVisible();
    const localFont = await page.request.get('/app/static/FamiljenGrotesk-Variable.ttf');
    expect(localFont.ok(), 'A fonte local deve ser servida pelo Streamlit').toBe(true);
    await page.evaluate(async () => {
      await document.fonts.load('400 16px "Familjen Grotesk"');
      await document.fonts.ready;
    });
    const loaded = await page.evaluate(() => [...document.fonts].some(face =>
      face.family.replace(/["']/g, '').trim() === 'Familjen Grotesk' &&
      face.status === 'loaded',
    ));
    expect(loaded, 'A fonte deve continuar carregando sem Google Fonts').toBe(true);
  } finally {
    await context.close();
  }
});
