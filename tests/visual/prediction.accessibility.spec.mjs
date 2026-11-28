import {test,expect} from '@playwright/test';
import {openClient, screenshot, ensureNoException} from './client.helpers.mjs';

for (const width of [1366,1024,390,320]) {
  test('PR-A01 tooltip informativo com teclado, clique e limites '+width, async({page},info)=>{
    await openClient(page,{width,height:768});
    const trigger=page.getByRole('button',{name:'Informações: Referência',exact:true});
    await trigger.scrollIntoViewIfNeeded();
    await trigger.focus();
    const tip=page.getByRole('tooltip');
    await expect(tip).toBeVisible();
    await expect(tip).toContainText('probabilidade de cancelamento');
    const box=await tip.boundingBox();
    expect(box.x).toBeGreaterThanOrEqual(7);
    expect(box.x+box.width).toBeLessThanOrEqual(width-7);
    expect(box.y).toBeGreaterThanOrEqual(7);
    expect(box.y+box.height).toBeLessThanOrEqual(761);
    await expect(trigger).toHaveAttribute('aria-describedby','n3-workspace-tooltip');
    await screenshot(page,info,'PR-A01-tooltip-'+width);
    await page.keyboard.press('Escape');
    await expect(tip).toBeHidden();
    await expect(trigger).toBeFocused();
    await trigger.click();
    await expect(tip).toBeVisible();
    await trigger.click();
    await expect(tip).toBeHidden();
    await expect(page.locator('.churn-bit[data-n3-tip]')).toHaveCount(0);
    await ensureNoException(page);
  });
}

test('PR-A02 toque abre e fecha tooltip informativo',async({browser})=>{
  const context=await browser.newContext({viewport:{width:390,height:844},hasTouch:true,isMobile:true});
  const page=await context.newPage();
  try {
    await openClient(page,{width:390,height:844});
    const trigger=page.getByRole('button',{name:'Informações: Seleção genética',exact:true});
    await trigger.tap();
    await expect(page.getByRole('tooltip')).toBeVisible();
    await trigger.tap();
    await expect(page.getByRole('tooltip')).toBeHidden();
    await ensureNoException(page);
  } finally { await context.close(); }
});
