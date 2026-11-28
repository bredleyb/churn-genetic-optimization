import { defineConfig } from '@playwright/test';
import { execFileSync } from 'node:child_process';

function gitValue(args) {
  try { return execFileSync('git',args,{encoding:'utf8',stdio:['ignore','pipe','ignore']}).trim(); }
  catch { return null; }
}
const gitHead = gitValue(['rev-parse','HEAD']);
const trackedChanges = gitValue(['status','--porcelain','--untracked-files=no']);

// Porta independente da aplicação normalmente aberta em localhost:8501.
const port = Number(process.env.VISUAL_TEST_PORT || 8517);
const baseURL = `http://127.0.0.1:${port}`;

export default defineConfig({
  metadata: { gitHead, trackedTreeClean: trackedChanges===null?null:trackedChanges==='' },
  testDir: './tests/visual',
  testMatch: '**/*.spec.mjs',
  fullyParallel: false,
  workers: 1, // Cada previsão executa o experimento inteiro; evitar buscas concorrentes.
  timeout: 240_000,
  // Capturas CL-* são anexadas aos testes; a aprovação usa medidas e estados
  // do DOM. A suíte antiga de screenshots comparativos foi substituída.
  expect: { timeout: 30_000 },
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
