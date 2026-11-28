import {test, expect} from '@playwright/test';
import fs from 'node:fs/promises';
import {openClient, action, replaceMonths, ensureNoException} from './client.helpers.mjs';

test('PR-T01 métricas indisponíveis e metodologia antes da execução', async({page})=>{
  await openClient(page,{width:1366,height:768});
  const tabs=page.locator('.st-key-dashboard-prediction-tabs');
  await tabs.getByRole('tab',{name:'Métricas',exact:true}).click();
  const cells=page.locator('.n3-metrics-table tbody td');
  await expect(cells).toHaveCount(20);
  await expect(cells).toHaveText(Array(20).fill('—'));
  await tabs.getByRole('tab',{name:'Terminal',exact:true}).click();
  await expect(page.locator('.n3-terminal-log')).toBeEmpty();
  await expect(tabs.getByRole('tabpanel',{name:'Terminal'}).getByRole('button',{name:'Baixar log'})).toBeDisabled();
  await tabs.getByRole('tab',{name:'Metodologia',exact:true}).click();
  await expect(page.locator('.n3-methodology')).toContainText('7.043');
  await expect(page.locator('.n3-methodology')).toContainText('Fitness = F1 médio (CV) − 0,02 × k/19');
  await expect(action(page)).toHaveText('Calcular previsão');
  await ensureNoException(page);
});

test('PR-T02 execução real, métricas, log integral UTF-8 e histórico', async({page})=>{
  test.slow();
  await openClient(page,{width:1366,height:768});
  const tabs=page.locator('.st-key-dashboard-prediction-tabs');
  await action(page).click();
  await expect(page.locator('.churn-workspace-heading')).toHaveAttribute('data-run-state','running');
  await tabs.getByRole('tab',{name:'Terminal',exact:true}).click();
  const terminal=tabs.getByRole('tabpanel',{name:'Terminal'});
  const download=terminal.getByRole('button',{name:'Baixar log'});
  await expect(download).toBeDisabled();
  await expect(page.locator('.churn-workspace-heading')).toHaveAttribute('data-run-state','complete',{timeout:120000});
  await expect(download).toBeEnabled();
  const logRegion=page.locator('.n3-terminal-log');
  const log=await logRegion.textContent();
  // O Terminal acompanha o final. Interação real de teclado deve suspender
  // o acompanhamento e preservar a posição ao alternar abas/reruns.
  await expect.poll(()=>logRegion.evaluate(el=>el.scrollHeight-el.clientHeight-el.scrollTop)).toBeLessThanOrEqual(4);
  await logRegion.focus();
  await page.keyboard.press('Home');
  await expect.poll(()=>logRegion.evaluate(el=>el.scrollTop)).toBeLessThanOrEqual(4);
  expect(log.startsWith('[EXECUÇÃO] Processamento iniciado.')).toBeTruthy();
  expect(log).toContain('[FIM]');
  const pending=page.waitForEvent('download');
  await download.click();
  const file=await pending;
  expect(file.suggestedFilename()).toBe('execucao-genetica.log');
  expect(await fs.readFile(await file.path(),'utf8')).toBe(log+'\n');
  await tabs.getByRole('tab',{name:'Métricas',exact:true}).click();
  const rows=page.locator('.n3-metrics-table tbody tr');
  await expect(rows).toHaveCount(10);
  await expect(rows.filter({hasText:'Falsos negativos'}).locator('td')).toHaveText(['165','173']);
  await expect(rows.filter({hasText:'F1 médio (CV)'}).locator('td')).toHaveText(['0,5952','0,6059']);
  await replaceMonths(page,4);
  await expect(page.locator('.n3-metrics-header h3')).toHaveText('Métricas · execução anterior');
  await tabs.getByRole('tab',{name:'Terminal',exact:true}).click();
  await expect(logRegion).toHaveText(log);
  await expect.poll(()=>logRegion.evaluate(el=>el.scrollTop)).toBeLessThanOrEqual(4);
  // Ao voltar ao final, o acompanhamento fica novamente disponível.
  await logRegion.focus();
  await page.keyboard.press('End');
  await expect.poll(()=>logRegion.evaluate(el=>el.scrollHeight-el.clientHeight-el.scrollTop)).toBeLessThanOrEqual(4);
  await ensureNoException(page);
});
