import {test,expect} from '@playwright/test';
import {openClient,ensureNoException} from './client.helpers.mjs';

test('PR-A03 fontes monoespaçadas locais e iconografia Carbon',async({page})=>{
  await openClient(page,{width:1366,height:768});
  const fonts=await page.evaluate(async()=>{
    await Promise.all([document.fonts.load('400 11px "IBM Plex Mono"'),document.fonts.load('400 13px "Cascadia Mono"')]);
    return Array.from(document.fonts).filter(f=>f.status==='loaded').map(f=>f.family.replace(/["']/g,''));
  });
  expect(fonts).toContain('IBM Plex Mono');
  expect(fonts).toContain('Cascadia Mono');
  const gene=page.locator('.churn-bit').first();
  await expect(gene).toHaveCSS('font-family','"IBM Plex Mono", Consolas, "Liberation Mono", monospace');
  await expect(gene).toHaveCSS('font-weight','400');
  const workspace=page.locator('.st-key-dashboard-workspace');
  await expect(workspace.locator('.n3-status-icon svg')).toHaveCount(1);
  await expect(workspace.getByRole('button',{name:'Informações: Referência'}).locator('svg')).toHaveCount(1);
  await workspace.getByRole('tab',{name:'Terminal',exact:true}).click();
  const terminal=page.locator('.n3-terminal-log');
  expect(await terminal.evaluate(el=>getComputedStyle(el).fontFamily)).toContain('Cascadia Mono');
  await ensureNoException(page);
});
