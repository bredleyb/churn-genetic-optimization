import { expect, test } from '@playwright/test';

// Larguras acordadas para a interface; altura fixa para capturas comparáveis.
const viewports = [1440, 1024, 768, 390];

async function checkHorizontalOverflow(page, stage) {
  const widths = await page.evaluate(() => ({
    viewport: document.documentElement.clientWidth,
    document: document.documentElement.scrollWidth,
    body: document.body.scrollWidth,
  }));
  expect(
    Math.max(widths.document, widths.body),
    `${stage}: rolagem horizontal indesejada em ${widths.viewport}px`,
  ).toBeLessThanOrEqual(widths.viewport + 2);
}

async function attachScreenshot(page, testInfo, name) {
  const image = await page.screenshot({ fullPage: true, animations: 'disabled' });
  await testInfo.attach(name, { body: image, contentType: 'image/png' });
}

for (const width of viewports) {
  test(`${width}px — abertura, execução, previsão e edição`, async ({ browser }, testInfo) => {
    const context = await browser.newContext({
      viewport: { width, height: 900 },
      deviceScaleFactor: 1,
      locale: 'pt-BR',
      colorScheme: 'light',
    });
    const page = await context.newPage();

    try {
      await test.step('Abertura da interface', async () => {
        await page.goto('/', { waitUntil: 'domcontentloaded' });
        await expect(page.getByRole('heading', { name: 'Previsão de cancelamento' })).toBeVisible();
        await expect(page.getByRole('heading', { name: 'Cliente', exact: true })).toBeVisible();
        await expect(page.getByRole('heading', { name: 'Execução e previsão' })).toBeVisible();
        await expect(page.getByRole('button', { name: 'Calcular previsão' })).toBeEnabled();
        await expect(page.locator('.churn-result')).toHaveCount(0);
        await checkHorizontalOverflow(page, 'Abertura');
        await page.mouse.move(0, 0);
        await expect(page).toHaveScreenshot(`01-inicial-${width}.png`, { fullPage: true });
      });

      await test.step('Processamento verdadeiro e monitor de execução', async () => {
        await page.getByRole('button', { name: 'Calcular previsão' }).click();
        await expect(page.locator('.churn-console')).toBeVisible({ timeout: 120_000 });
        await expect(page.locator('.churn-chromosome')).toBeVisible({ timeout: 120_000 });
        await expect(page.locator('.churn-bit')).toHaveCount(19);
        await attachScreenshot(page, testInfo, `02-processamento-${width}.png`);
        await checkHorizontalOverflow(page, 'Processamento');
      });

      await test.step('Previsão e resultados calculados', async () => {
        await expect(page.getByRole('heading', { name: 'Previsão', exact: true })).toBeVisible({ timeout: 180_000 });
        await expect(page.locator('.churn-result')).toHaveCount(2);
        await expect(page.locator('.churn-value').first()).toContainText(/\d+,\d{2}%/);
        await expect(page.locator('.churn-value').last()).toContainText(/\d+,\d{2}%/);
        await expect(page.locator('.churn-console')).toContainText('[FIM]');
        await checkHorizontalOverflow(page, 'Resultado');
        await page.mouse.move(0, 0);
        // Tempo total varia entre computadores; ocultar somente esse rótulo instável.
        await expect(page).toHaveScreenshot(`03-concluido-${width}.png`, {
          fullPage: true,
          mask: [page.getByText(/Execução concluída · \d+ subconjuntos avaliados · \d+ gerações ·/)],
        });
      });

      await test.step('Edição invalida a previsão anterior', async () => {
        const months = page.getByRole('spinbutton', { name: 'Tempo como cliente (meses)' });
        await months.fill('4');
        await months.press('Tab');
        await expect(page.getByText(/Os dados do cliente foram alterados/)).toBeVisible();
        await expect(page.locator('.churn-result')).toHaveCount(0);
        await checkHorizontalOverflow(page, 'Cliente alterado');
        await page.mouse.move(0, 0);
        await expect(page).toHaveScreenshot(`04-editado-${width}.png`, {
          fullPage: true,
          mask: [page.getByText(/Execução concluída · \d+ subconjuntos avaliados · \d+ gerações ·/)],
        });
      });
    } finally {
      await context.close();
    }
  });
}
