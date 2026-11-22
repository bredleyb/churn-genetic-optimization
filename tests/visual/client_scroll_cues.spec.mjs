import { test, expect } from '@playwright/test';
import { scrollCueStrengths } from '../../src/client_scroll_cues.mjs';

test('sem overflow as duas sombras permanecem invisíveis', () => {
  expect(scrollCueStrengths(0, 480, 480)).toEqual({top:0,bottom:0});
  expect(scrollCueStrengths(50, 480, 470)).toEqual({top:0,bottom:0});
});
test('sombras complementares no início, meio e fim', () => {
  const height = 300, total = 900;
  expect(scrollCueStrengths(0,height,total)).toEqual({top:0,bottom:1});
  expect(scrollCueStrengths(28,height,total)).toEqual({top:0.5,bottom:1});
  expect(scrollCueStrengths(300,height,total)).toEqual({top:1,bottom:1});
  expect(scrollCueStrengths(572,height,total)).toEqual({top:1,bottom:0.5});
  expect(scrollCueStrengths(600,height,total)).toEqual({top:1,bottom:0});
});
test('conteúdo curto mantém as transições contínuas e sem divisão por zero', () => {
  expect(scrollCueStrengths(0,300,304)).toEqual({top:0,bottom:1});
  expect(scrollCueStrengths(2,300,304)).toEqual({top:1,bottom:1});
  expect(scrollCueStrengths(4,300,304)).toEqual({top:1,bottom:0});
  expect(scrollCueStrengths(999,300,304)).toEqual({top:1,bottom:0});
});
for (const viewport of [{width:1024,height:768},{width:390,height:900}]) {
  test('rolagem do Cliente controla os gradientes — '+viewport.width+'x'+viewport.height,
    async ({page}) => {
      await page.setViewportSize(viewport);
      await page.goto('/', {waitUntil:'domcontentloaded'});
      const client = page.locator('.st-key-dashboard-client');
      const fields = page.locator('.st-key-dashboard-client-fields');
      const footer = page.locator('.st-key-dashboard-client-footer');
      await expect(page.getByRole('heading',{name:'Cliente',exact:true})).toBeVisible();
      await expect(fields).toBeVisible();
      await expect(footer.getByRole('button',{name:'Calcular previsão'})).toBeVisible();
      const dimensions = await fields.evaluate(el => {
        const css = getComputedStyle(el);
        return {scrollable:el.scrollHeight-el.clientHeight,
          gutter:css.scrollbarGutter,padding:parseFloat(css.paddingInlineEnd)};
      });
      expect(dimensions.gutter).toBe('stable');
      expect(dimensions.padding).toBeGreaterThanOrEqual(10);
      expect(dimensions.scrollable).toBeGreaterThan(2);

      const opacity = async () => client.evaluate(el => ({
        top:Number(getComputedStyle(el).getPropertyValue('--n3-client-shadow-top')),
        bottom:Number(getComputedStyle(el).getPropertyValue('--n3-client-shadow-bottom')),
      }));
      const scrollTo = async position => fields.evaluate((el,y) => {
        el.scrollTop=y;
        el.dispatchEvent(new Event('scroll'));
      },position);

      await scrollTo(0);
      await expect.poll(async () => (await opacity()).bottom).toBeGreaterThan(.99);
      await expect.poll(async () => (await opacity()).top).toBeLessThan(.01);
      const overlays = await page.evaluate(() => {
        const panel=document.querySelector('.st-key-dashboard-client');
        const heading=panel?.querySelector(':scope > [data-testid="stLayoutWrapper"]:has(.churn-panel-heading)');
        const footer=panel?.querySelector('.st-key-dashboard-client-footer');
        return {heading:getComputedStyle(heading,'::after').pointerEvents,
          footer:getComputedStyle(footer,'::before').pointerEvents};
      });
      expect(overlays).toEqual({heading:'none',footer:'none'});
      await scrollTo(dimensions.scrollable/2);
      await expect.poll(async () => (await opacity()).top).toBeGreaterThan(.99);
      await expect.poll(async () => (await opacity()).bottom).toBeGreaterThan(.99);
      await scrollTo(dimensions.scrollable);
      await expect.poll(async () => (await opacity()).top).toBeGreaterThan(.99);
      await expect.poll(async () => (await opacity()).bottom).toBeLessThan(.01);
      await expect(footer.getByRole('button',{name:'Calcular previsão'})).toBeVisible();
    });
}
test('captura não mostra barras laterais de foco na aba ativa', async ({page}) => {
  await page.setViewportSize({width:1024,height:768});
  await page.goto('/', {waitUntil:'domcontentloaded'});
  const tab = page.locator('.st-key-dashboard-detail-tabs').getByRole('tab',{name:'Serviços'});
  await tab.click();
  await expect(tab).toHaveAttribute('aria-selected','true');
  const css=await tab.evaluate(el=>({
    outline:getComputedStyle(el).outlineStyle,
    shadow:getComputedStyle(el).boxShadow,
  }));
  expect(css.outline).toBe('none');
  expect(css.shadow).toBe('none');
});
