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
      tenureInput: bounds('.st-key-dashboard-tenure-control input[aria-label="Tempo como cliente"]'),
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
  expect(layout.clientTitle.y - layout.client.y, `${stage}: título Cliente muito distante do topo`)
    .toBeLessThanOrEqual(27);
  expect(layout.workspaceTitle.y - layout.workspace.y, `${stage}: título Previsão muito distante do topo`)
    .toBeLessThanOrEqual(27);
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
        await expect(page.locator('.churn-run-icon')).toHaveCount(0);
        await expect(page.locator('.churn-comparison .churn-state')).toHaveCount(0);
        await expect(page.getByRole('spinbutton', { name: 'Tempo como cliente' })).toHaveValue('3');
        const tabsBar = page.locator('.st-key-dashboard-detail-tabs [role="tablist"]');
        const lastTab = page.locator('.st-key-dashboard-detail-tabs').getByRole('tab', { name: 'Extras' });
        const [tabBounds, listBounds] = await Promise.all([lastTab.boundingBox(), tabsBar.boundingBox()]);
        expect(tabBounds, 'A última aba deve existir').toBeTruthy();
        expect(listBounds, 'A navegação de abas deve existir').toBeTruthy();
        expect(tabBounds.x + tabBounds.width, 'A última aba fica truncada')
          .toBeLessThanOrEqual(listBounds.x + listBounds.width + 2);
        // Tempo e Cobrança usam o mesmo componente e parâmetros de layout.
        const numbers = [
          page.locator('.st-key-dashboard-tenure-control [data-testid="stNumberInput"]'),
          page.locator('[data-testid="stNumberInput"]:has(input[aria-label="Cobrança mensal"])'),
        ];
        const metrics = await Promise.all(numbers.map(widget => widget.evaluate(root => {
          const field = root.querySelector('[data-baseweb="input"]');
          const label = root.querySelector('[data-testid="stWidgetLabel"]');
          const input = root.querySelector('input');
          if (!field || !label || !input) return null;
          const rect = el => {
            const r = el.getBoundingClientRect();
            return {y:r.y,width:r.width,height:r.height};
          };
          const buttons = [...root.querySelectorAll('button')];
          return {
            field:rect(field), label:rect(label), input:rect(input),
            buttons:buttons.map(rect),
            radius:getComputedStyle(field).borderTopLeftRadius,
            font:getComputedStyle(input).fontSize,
            line:getComputedStyle(input).lineHeight,
            backgrounds:buttons.map(button => getComputedStyle(button).backgroundColor),
          };
        })));
        for (const field of metrics) {
          expect(field, 'Campo numérico incompleto').toBeTruthy();
          expect(field.buttons, 'Stepper nativo deve ter dois botões').toHaveLength(2);
          expect(Math.abs(field.field.height - 42), 'Altura do campo incorreta')
            .toBeLessThanOrEqual(2);
          expect(Math.abs(field.input.y + field.input.height / 2 -
                          field.field.y - field.field.height / 2), 'Texto fora do centro vertical')
            .toBeLessThanOrEqual(2);
          expect(parseFloat(field.radius), 'Raio externo incorreto').toBeCloseTo(4, 0);
          expect(Math.abs(field.buttons[0].width - field.buttons[1].width)).toBeLessThanOrEqual(1);
          expect(field.backgrounds).toEqual(['rgb(14, 16, 19)', 'rgb(14, 16, 19)']);
        }
        const [tenure, monthly] = metrics;
        const gap = field => field.field.y - (field.label.y + field.label.height);
        expect(Math.abs(gap(tenure) - gap(monthly)), 'Distância entre rótulo e campo diverge')
          .toBeLessThanOrEqual(2);
        expect(Math.abs(tenure.field.height - monthly.field.height)).toBeLessThanOrEqual(1);
        expect(tenure.font).toBe(monthly.font);
        expect(tenure.line).toBe(monthly.line);
        expect(tenure.buttons.map(b => b.width)).toEqual(monthly.buttons.map(b => b.width));
        const select = await page.locator('.st-key-dashboard-quick-fields [data-baseweb="select"] > div')
          .first().evaluate(el => ({height:el.getBoundingClientRect().height,
                                    radius:getComputedStyle(el).borderTopLeftRadius}));
        expect(Math.abs(select.height - tenure.field.height)).toBeLessThanOrEqual(2);
        expect(parseFloat(select.radius)).toBeCloseTo(4, 0);
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

      await test.step('Avaliações genéticas reais e monitor atualizado', async () => {
        await page.getByRole('button', { name: 'Calcular previsão' }).click();
        await expect(page.locator('.churn-workspace-heading[data-run-state="running"]')).toBeVisible();
        await expect(page.getByRole('status', { name: 'Executando previsão' })).toBeVisible();
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
        await expect(page.getByRole('status', { name: 'Previsão concluída' })).toBeVisible();
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
        const months = page.getByRole('spinbutton', { name: 'Tempo como cliente' });
    for (const value of ['1', '9', '10', '24', '120']) {
      await months.fill(value);
      await months.press('Tab');
      await expect(months).toHaveValue(value);
    }
    const buttons = page.locator('.st-key-dashboard-tenure-control [data-testid="stNumberInput"] button');
    await expect(buttons).toHaveCount(2);
    await buttons.nth(1).click();
    await expect(months).toHaveValue('121');
    await buttons.nth(0).click();
    await expect(months).toHaveValue('120');
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

    const months = page.getByRole('spinbutton', { name: 'Tempo como cliente' });
    for (const [typed, expected] of [
      ['1', '1 mês'], ['9', '9 meses'], ['10', '10 meses'],
      ['24', '24 meses'], ['120', '120 meses'],
    ]) {
      await months.fill(typed);
      await months.press('Tab');
      await expect(months).toHaveValue(expected);
      const sizes = await months.evaluate(el => {
        const cs = getComputedStyle(el);
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        context.font = cs.font;
        return {
          rendered: context.measureText(el.value).width,
          available: el.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight),
        };
      });
      expect(sizes.rendered, `Texto cortado: ${expected}`)
        .toBeLessThanOrEqual(sizes.available + 1);
    }
    await page.getByRole('button', { name: 'Aumentar um mês', exact: true }).click();
    await expect(months).toHaveValue('121 meses');
    await page.getByRole('button', { name: 'Diminuir um mês', exact: true }).click();
    await expect(months).toHaveValue('120 meses');
    await months.fill('abc');
    await months.press('Tab');
    await expect(page.getByRole('button', { name: 'Calcular previsão' })).toBeDisabled();
    await expect(page.getByText('Informe um número inteiro de meses.')).toBeVisible();
    await months.fill('24 meses');
    await months.press('Tab');
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
