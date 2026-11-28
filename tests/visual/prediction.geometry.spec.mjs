import {test,expect} from '@playwright/test';
import {openClient,action,profileCircles,screenshot,ensureNoException} from './client.helpers.mjs';

async function noOverlap(page){
  const bounds=await page.evaluate(()=>{
    const selectors=['.n3-status','.churn-comparison','.churn-chart','.st-key-dashboard-selection-section'];
    return selectors.map(selector=>{
      const node=document.querySelector(selector), r=node.getBoundingClientRect();
      return {selector,top:r.top,bottom:r.bottom};
    });
  });
  for(let i=1;i<bounds.length;i++){
    expect(bounds[i].top-bounds[i-1].bottom,bounds[i-1].selector+' → '+bounds[i].selector).toBeGreaterThanOrEqual(4);
  }
}
for(const width of [1366,1024,390,320]){
  test('PR-G01 cartões sem sobreposição '+width,async({page})=>{
    await openClient(page,{width,height:768});
    await noOverlap(page);
    await ensureNoException(page);
  });
}
test('PR-G02 segundo exemplo real: permanência, métricas e terminal',async({page},info)=>{
  test.slow();
  await openClient(page,{width:1366,height:768});
  await profileCircles(page).nth(1).click();
  await expect(page.getByRole('textbox',{name:'Tempo como cliente'})).not.toHaveValue('3');
  await action(page).click();
  await expect(page.locator('.churn-workspace-heading')).toHaveAttribute('data-run-state','complete',{timeout:120000});
  await expect(action(page)).toBeEnabled();
  await expect(page.locator('.n3-status-title')).toHaveText('Permanência prevista');
  await expect(page.locator('.churn-prediction-value')).toHaveText(['0,37%','0,71%']);
  await expect(page.locator('.n3-risk-fill.is-positive')).toHaveCount(2);
  await noOverlap(page);
  await screenshot(page,info,'PR-G02-permanencia-1366');
  const workspace=page.locator('.st-key-dashboard-workspace');
  for(const name of ['Métricas','Terminal','Metodologia']){
    await workspace.getByRole('tab',{name,exact:true}).click();
    await expect(workspace.getByRole('tabpanel',{name,exact:true})).toBeVisible();
    await screenshot(page,info,'PR-G02-'+name+'-1366');
  }
  await workspace.getByRole('tab',{name:'Painel',exact:true}).click();
  await page.setViewportSize({width:390,height:844});
  await page.locator('.n3-status').scrollIntoViewIfNeeded();
  await noOverlap(page);
  await screenshot(page,info,'PR-G02-permanencia-390-status');
  await page.locator('.churn-comparison').scrollIntoViewIfNeeded();
  await screenshot(page,info,'PR-G02-permanencia-390-modelos');
  await page.locator('.n3-impact').scrollIntoViewIfNeeded();
  await screenshot(page,info,'PR-G02-permanencia-390-impacto');
  await ensureNoException(page);
});
