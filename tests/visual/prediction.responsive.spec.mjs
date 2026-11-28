import {test,expect} from '@playwright/test';
import {openClient, client, action, tabs, measure, near, screenshot, ensureNoException} from './client.helpers.mjs';

for (const size of [{width:1440,height:768},{width:768,height:1024},{width:390,height:844},{width:320,height:720}]) {
  test('PR-R01 geometria final e acesso às quatro abas '+size.width, async({page},info)=>{
    await openClient(page,size);
    const workspace=page.locator('.st-key-dashboard-workspace');
    const c=await measure(client(page)), w=await measure(workspace);
    near(c.left,12,'margem externa',2);
    if(size.width>=1024){
      near(c.width,366,'Cliente desktop',2);
      near(w.left-c.right,12,'intervalo horizontal',2);
      near(c.height,size.height-24,'altura desktop',2);
    }else{
      near(w.top-c.bottom,12,'intervalo vertical',2);
      if(size.width<700)near(c.height,Math.min(744,size.height-24),'altura Cliente',2);
    }
    const nav=workspace.getByRole('tab');
    await expect(nav).toHaveCount(4);
    await expect(action(page)).toBeEnabled();
    await screenshot(page,info,'PR-R01-cliente-'+size.width);
    for(const name of ['Painel','Terminal','Métricas','Metodologia']){
      await workspace.getByRole('tab',{name,exact:true}).click();
      const content=workspace.getByRole('tabpanel',{name,exact:true});
      await expect(content).toBeVisible();
      expect(await content.evaluate(el=>el.scrollWidth-el.clientWidth),'overflow de '+name).toBeLessThanOrEqual(2);
      expect(await page.locator('[data-testid="stMain"]').evaluate(el=>el.scrollWidth-el.clientWidth)).toBeLessThanOrEqual(2);
      await screenshot(page,info,'PR-R01-'+name+'-'+size.width);
    }
    await ensureNoException(page);
  });
}

test('PR-R02 limiares preservam valores e seleção das abas',async({page})=>{
  await openClient(page,{width:1366,height:768});
  const workspace=page.locator('.st-key-dashboard-workspace');
  await tabs(page).getByRole('tab',{name:'Conta',exact:true}).click();
  await workspace.getByRole('tab',{name:'Metodologia',exact:true}).click();
  const value=await page.locator('input[aria-label="Cobrança mensal"]').inputValue();
  for(const width of [1365,1024,1023,700,699,390,389,320,1366]){
    await page.setViewportSize({width,height:720});
    await expect(workspace.getByRole('tab',{name:'Metodologia'})).toHaveAttribute('aria-selected','true');
    await expect(tabs(page).getByRole('tab',{name:'Conta'})).toHaveAttribute('aria-selected','true');
    await expect(page.locator('input[aria-label="Cobrança mensal"]')).toHaveValue(value);
    const c=await measure(client(page)),w=await measure(workspace);
    if(width>=1024)near(w.left-c.right,12,'desktop '+width,2);
    else near(w.top-c.bottom,12,'empilhado '+width,2);
    expect(await page.locator('[data-testid="stMain"]').evaluate(el=>el.scrollWidth-el.clientWidth)).toBeLessThanOrEqual(2);
  }
  await ensureNoException(page);
});
