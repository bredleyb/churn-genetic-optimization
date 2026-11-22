/** Executa o Playwright e empacota os diagnósticos, inclusive em caso de falha. */
import { spawn, spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, rmSync, writeFileSync, appendFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const results = join(root, 'results');
const logPath = join(results, 'playwright-console.log');
const playwrightCli = join(root, 'node_modules', 'playwright', 'cli.js');
const argumentsFromNpm = process.argv.slice(2);
const mode = argumentsFromNpm.includes('--update-snapshots') ? 'atualizacao-referencias' : 'comparacao';

mkdirSync(results, { recursive: true });
for (const artifact of ['playwright-report', 'playwright-artifacts', 'playwright-results.json']) {
  rmSync(join(results, artifact), { recursive: true, force: true });
}
writeFileSync(logPath, '', 'utf8');

function report(message) {
  process.stdout.write(message);
  appendFileSync(logPath, message, 'utf8');
}

async function test() {
  if (!existsSync(playwrightCli)) {
    report('Playwright não encontrado. Execute npm install antes dos testes.\n');
    return 1;
  }
  report(`Iniciando testes visuais (${mode})...\n`);
  return new Promise((done) => {
    const child = spawn(process.execPath, [playwrightCli, 'test', ...argumentsFromNpm], {
      cwd: root,
      env: { ...process.env, FORCE_COLOR: '0' },
      stdio: ['inherit', 'pipe', 'pipe'],
    });
    let finished = false;
    function finish(code) {
      if (finished) return;
      finished = true;
      done(code);
    }
    child.stdout.on('data', (chunk) => report(chunk.toString()));
    child.stderr.on('data', (chunk) => {
      process.stderr.write(chunk);
      appendFileSync(logPath, chunk.toString(), 'utf8');
    });
    child.on('error', (error) => {
      report(`Falha ao iniciar o Playwright: ${error.message}\n`);
      finish(1);
    });
    child.on('close', (code, signal) => {
      if (signal) report(`Playwright interrompido: ${signal}\n`);
      finish(typeof code === 'number' ? code : 1);
    });
  });
}

const exitCode = await test();
report(`\nResultado dos testes: ${exitCode === 0 ? 'APROVADO' : 'FALHOU'} (código ${exitCode}).\n`);
report('Criando ZIP para revisão...\n');
const python = process.env.PYTHON || 'python';
const pack = spawnSync(python, [
  join(root, 'scripts', 'package_visual_results.py'),
  '--project-root', root,
  '--test-exit-code', String(exitCode),
  '--mode', mode,
], { cwd: root, stdio: 'inherit' });

if (pack.error) {
  report(`Falha ao iniciar empacotamento: ${pack.error.message}\n`);
}
process.exitCode = exitCode !== 0 ? exitCode : (pack.status ?? 1);
