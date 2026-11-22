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
      technical: bounds('.st-key-dashboard-desktop-detail .churn-technical'),
      monitor: bounds('.st-key-dashboard-desktop-detail .churn-console'),
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
  expect(layout.row.bottom, `${stage}: grade extrapola a altura da janela`)
    .toBeLessThanOrEqual(layout.height - 4);
  expect(layout.client, `${stage}: Cliente ausente`).toBeTruthy();
  expect(layout.workspace, `${stage}: Análise ausente`).toBeTruthy();
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
    expect(layout.monitor.bottom, `${stage}: console fica oculto ou cortado`)
      .toBeLessThanOrEqual(layout.monitorSection.bottom + 2);
    if (layout.width >= 1000 && layout.height <= 760) {
      expect(Math.abs(layout.selection.y - layout.monitorSection.y),
        `${stage}: seleção e monitor devem compartilhar a faixa inferior`).toBeLessThanOrEqual(2);
      expect(layout.chart.height, `${stage}: gráfico sem altura suficiente para projeção`)
        .toBeGreaterThanOrEqual(130);
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
        await expect(page.getByRole('heading', { name: 'Previsão de cancelamento' })).toBeVisible();
        await expect(page.getByRole('heading', { name: 'Cliente', exact: true })).toBeVisible();
        await expect(page.getByRole('heading', { name: 'Análise e execução' })).toBeVisible();
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
        await expect(page.locator('.churn-comparison .churn-state')).toHaveText('Concluído', { timeout: 180_000 });
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
        const months = page.getByRole('spinbutton', { name: 'Tempo como cliente (meses)' });
        await months.fill('4');
        await months.press('Tab');
        await expect(page.locator('.churn-comparison .churn-state')).toHaveText('Dados alterados');
        await expect(page.locator('.churn-prediction-value').first()).toHaveText('—');
        await expect(page.locator('.churn-technical').first())
          .toContainText('Os dados do cliente foram alterados');
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
