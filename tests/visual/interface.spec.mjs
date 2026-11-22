import { expect, test } from '@playwright/test';

// O dashboard ocupa a altura do navegador: são permitidas rolagens somente nos painéis.
const viewports = [1440, 1024, 768, 390];

async function checkDashboardGeometry(page, stage, width, testInfo) {
  const layout = await page.evaluate(() => {
    const rect = selector => {
      const el = document.querySelector(selector);
      if (!el) return null;
      const b = el.getBoundingClientRect();
      const css = getComputedStyle(el);
      return { x: b.x, y: b.y, right: b.right, bottom: b.bottom,
               width: b.width, height: b.height, overflowY: css.overflowY };
    };
    const documentRoot = document.scrollingElement || document.documentElement;
    return {
      width: window.innerWidth, height: window.innerHeight,
      scrollHeight: documentRoot.scrollHeight,
      clientHeight: documentRoot.clientHeight,
      scrollWidth: documentRoot.scrollWidth,
      clientWidth: documentRoot.clientWidth,
      client: rect('.st-key-dashboard-client'),
      workspace: rect('.st-key-dashboard-workspace'),
      clientFields: rect('.st-key-dashboard-client-fields'),
      clientFooter: rect('.st-key-dashboard-client-footer'),
      calculateButton: rect('.st-key-dashboard-client-footer button'),
      mobileRow: rect('[data-testid="stHorizontalBlock"]:has(.st-key-dashboard-client):has(.st-key-dashboard-workspace)'),
      clientColumn: rect('[data-testid="stColumn"]:has(.st-key-dashboard-client)'),
      workspaceColumn: rect('[data-testid="stColumn"]:has(.st-key-dashboard-workspace)'),
      clientBlock: rect('[data-testid="stColumn"]:has(.st-key-dashboard-client) > [data-testid="stVerticalBlock"]'),
      clientWrapper: rect('[data-testid="stColumn"]:has(.st-key-dashboard-client) > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"]'),
      workspaceBlock: rect('[data-testid="stColumn"]:has(.st-key-dashboard-workspace) > [data-testid="stVerticalBlock"]'),
      workspaceWrapper: rect('[data-testid="stColumn"]:has(.st-key-dashboard-workspace) > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"]'),
      mobileRowStyles: (() => {
        const el = document.querySelector('[data-testid="stHorizontalBlock"]:has(.st-key-dashboard-client):has(.st-key-dashboard-workspace)');
        if (!el) return null;
        const style = getComputedStyle(el);
        return {display: style.display, position: style.position, gridTemplateRows: style.gridTemplateRows,
                top: style.top, bottom: style.bottom, height: style.height,
                minHeight: style.minHeight, overflowY: style.overflowY};
      })(),
    };
  });
  // Anexar geometria e CSS calculado para diagnosticar falhas móveis no ZIP.
  if (width <= 620 && testInfo) {
    await testInfo.attach(`geometria-${stage}-${width}.json`, {
      body: JSON.stringify(layout, null, 2), contentType: 'application/json',
    });
    expect(layout.mobileRow, `${stage}: linha principal do dashboard não localizada`).toBeTruthy();
    expect(layout.mobileRowStyles.display, `${stage}: linha móvel precisa usar grid`).toBe('grid');
    expect(layout.mobileRowStyles.position, `${stage}: linha móvel deve ficar vinculada ao viewport`).toBe('fixed');
    expect(layout.mobileRow.bottom, `${stage}: grade principal ultrapassa a tela`).toBeLessThanOrEqual(layout.height + 2);
    // Trace real de 390px: stColumn > stVerticalBlock > stLayoutWrapper > painel.
    // Os wrappers precisam caber na coluna; height:auto neles expandia o cartão até 1016px.
    for (const [innerName, columnName] of [
      ['clientBlock', 'clientColumn'], ['clientWrapper', 'clientColumn'],
      ['workspaceBlock', 'workspaceColumn'], ['workspaceWrapper', 'workspaceColumn'],
    ]) {
      expect(layout[innerName], `${stage}: ${innerName} do Streamlit ausente`).toBeTruthy();
      expect(layout[innerName].bottom, `${stage}: ${innerName} expande sua coluna`).toBeLessThanOrEqual(layout[columnName].bottom + 2);
      expect(layout[innerName].height, `${stage}: ${innerName} é maior que a coluna`).toBeLessThanOrEqual(layout[columnName].height + 2);
    }
    expect(layout.client.height, `${stage}: cartão Cliente ultrapassa a coluna`).toBeLessThanOrEqual(layout.clientColumn.height + 2);
    expect(layout.workspace.height, `${stage}: cartão Execução ultrapassa a coluna`).toBeLessThanOrEqual(layout.workspaceColumn.height + 2);
  }
  expect(layout.client, `${stage}: painel Cliente ausente`).toBeTruthy();
  expect(layout.workspace, `${stage}: painel Execução ausente`).toBeTruthy();
  expect(layout.scrollWidth, `${stage}: rolagem horizontal da página`).toBeLessThanOrEqual(layout.clientWidth + 2);
  expect(layout.scrollHeight, `${stage}: rolagem vertical da página`).toBeLessThanOrEqual(layout.clientHeight + 2);
  for (const name of ['client', 'workspace']) {
    const panel = layout[name];
    expect(panel.x, `${stage}: ${name} fora da tela à esquerda`).toBeGreaterThanOrEqual(-2);
    expect(panel.y, `${stage}: ${name} fora da tela no topo`).toBeGreaterThanOrEqual(-2);
    expect(panel.right, `${stage}: ${name} fora da tela à direita`).toBeLessThanOrEqual(width + 2);
    expect(panel.bottom, `${stage}: ${name} fora da tela abaixo`).toBeLessThanOrEqual(layout.height + 2);
    expect(panel.height, `${stage}: ${name} sem altura útil`).toBeGreaterThan(100);
    expect(panel.overflowY, `${stage}: ${name} não tem região interna controlada`).toMatch(/auto|hidden|scroll/);
  }
  // A seção de campos pode rolar, enquanto o botão principal permanece dentro do painel.
  for (const name of ['clientFields', 'clientFooter', 'calculateButton']) {
    expect(layout[name], `${stage}: ${name} não encontrado`).toBeTruthy();
    expect(layout[name].y, `${stage}: ${name} acima do painel Cliente`).toBeGreaterThanOrEqual(layout.client.y - 2);
    expect(layout[name].bottom, `${stage}: ${name} fora do painel Cliente`).toBeLessThanOrEqual(layout.client.bottom + 2);
  }
  expect(layout.clientFields.overflowY, `${stage}: campos sem rolagem interna`).toMatch(/auto|scroll/);
  expect(layout.clientFields.bottom, `${stage}: os campos encobrem o botão Calcular previsão`).toBeLessThanOrEqual(layout.clientFooter.y + 2);
  if (width <= 620) {
    expect(layout.client.bottom, `${stage}: painéis móveis sobrepostos`).toBeLessThanOrEqual(layout.workspace.y + 2);
  }
}

async function capture(page, testInfo, name) {
  const screenshot = await page.screenshot({ fullPage: false, animations: 'disabled' });
  await testInfo.attach(name, { body: screenshot, contentType: 'image/png' });
}

for (const width of viewports) {
  test(`${width}px — dashboard escuro sem scroll e execução completa`, async ({ browser }, testInfo) => {
    const context = await browser.newContext({
      viewport: { width, height: 900 },
      deviceScaleFactor: 1,
      locale: 'pt-BR',
      colorScheme: 'dark',
    });
    const page = await context.newPage();
    try {
      await test.step('Dashboard pronto e controles de cliente acessíveis', async () => {
        await page.goto('/', { waitUntil: 'domcontentloaded' });
        await expect(page.getByRole('heading', { name: 'Previsão de cancelamento' })).toBeVisible();
        await expect(page.getByRole('heading', { name: 'Cliente', exact: true })).toBeVisible();
        await expect(page.getByRole('heading', { name: 'Execução e previsão' })).toBeVisible();
        await expect(page.getByRole('button', { name: 'Calcular previsão' })).toBeEnabled();
        await expect(page.locator('.churn-kpi')).toHaveCount(4);
        await expect(page.locator('.churn-bit')).toHaveCount(19);
        await expect(page.locator('.churn-kpi-value').first()).toHaveText('—');
        const bg = await page.locator('.stApp').evaluate(el => getComputedStyle(el).backgroundColor);
        expect(bg, 'O tema deve ser escuro').toBe('rgb(11, 17, 27)');
        await checkDashboardGeometry(page, 'Inicial', width, testInfo);
        await page.mouse.move(0, 0);
        await expect(page).toHaveScreenshot(`dashboard-01-inicial-${width}.png`, { fullPage: false });
      });

      await test.step('Monitor recebe avaliações reais e cromossomo é atualizado', async () => {
        await page.getByRole('button', { name: 'Calcular previsão' }).click();
        await expect(page.locator('.churn-console')).toContainText(/\[G\d{2}\]/, { timeout: 120_000 });
        await expect(page.locator('.churn-bit')).toHaveCount(19);
        await capture(page, testInfo, `dashboard-02-processamento-${width}.png`);
        await checkDashboardGeometry(page, 'Processamento', width, testInfo);
      });

      await test.step('Resultados e comparação visíveis no dashboard', async () => {
        await expect(page.locator('.churn-kpi').last()).toContainText('Concluído', { timeout: 180_000 });
        await expect(page.locator('.churn-kpi-value').first()).toContainText(/\d+,\d{2}%/);
        await expect(page.locator('.churn-kpi-value').nth(1)).toContainText(/\d+,\d{2}%/);
        await expect(page.locator('.churn-console')).toContainText('[FIM]');
        await expect(page.locator('.churn-tech-item')).toHaveCount(4);
        await expect(page.locator('.churn-bit')).toHaveCount(19);
        await checkDashboardGeometry(page, 'Concluído', width, testInfo);
        await page.mouse.move(0, 0);
        await expect(page).toHaveScreenshot(`dashboard-03-concluido-${width}.png`, {
          fullPage: false,
          // Tempo de execução varia entre computadores.
          mask: [page.locator('.churn-tech-item').nth(3)],
        });
      });

      await test.step('Editar cliente invalida previsões, preservando o histórico', async () => {
        const months = page.getByRole('spinbutton', { name: 'Tempo como cliente (meses)' });
        await months.fill('4');
        await months.press('Tab');
        await expect(page.locator('.churn-kpi').last()).toContainText('Alterado');
        await expect(page.locator('.churn-kpi-value').first()).toHaveText('—');
        await expect(page.getByText(/Os dados do cliente foram alterados/)).toBeVisible();
        await expect(page.locator('.churn-console')).toContainText('[FIM]');
        await checkDashboardGeometry(page, 'Editado', width, testInfo);
        await page.mouse.move(0, 0);
        await expect(page).toHaveScreenshot(`dashboard-04-editado-${width}.png`, {
          fullPage: false,
          mask: [page.locator('.churn-tech-item').nth(3)],
        });
      });
    } finally {
      await context.close();
    }
  });
}
