import { defineConfig } from '@playwright/test';

// Porta independente da aplicação normalmente aberta em localhost:8501.
const port = Number(process.env.VISUAL_TEST_PORT || 8517);
const baseURL = `http://127.0.0.1:${port}`;

export default defineConfig({
  testDir: './tests/visual',
  testMatch: '**/*.spec.mjs',
  fullyParallel: false,
  workers: 1, // Cada previsão executa o experimento inteiro; evitar buscas concorrentes.
  timeout: 240_000,
  expect: {
    timeout: 30_000,
    toHaveScreenshot: {
      animations: 'disabled',
      threshold: 0.15,
      maxDiffPixelRatio: 0.01,
    },
  },
  reporter: [
    ['list'],
    ['html', { outputFolder: 'results/playwright-report', open: 'never' }],
    ['json', { outputFile: 'results/playwright-results.json' }],
  ],
  outputDir: 'results/playwright-artifacts',
  use: {
    baseURL,
    browserName: 'chromium',
    locale: 'pt-BR',
    colorScheme: 'light',
    deviceScaleFactor: 1,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
  },
  webServer: {
    command: `python -m streamlit run streamlit_app.py --server.headless true --server.address 127.0.0.1 --server.port ${port}`,
    url: baseURL,
    reuseExistingServer: false,
    timeout: 120_000,
  },
});
