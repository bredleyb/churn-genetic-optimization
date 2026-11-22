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
          gutter:css.scrollbarGutter,
          paddingLeft:parseFloat(css.paddingInlineStart),
          paddingRight:parseFloat(css.paddingInlineEnd)};
      });
      expect(dimensions.gutter).toBe('stable both-edges');
      expect(dimensions.paddingLeft).toBe(10);
      expect(dimensions.paddingRight).toBe(10);
      expect(dimensions.scrollable).toBeGreaterThan(2);
      // O controle de largura total deve receber o mesmo recuo dos dois lados,
      // independentemente de scrollbar clássica, overlay ou oculta.
      const insets = await page.locator('.st-key-dashboard-detail-tabs [data-testid="stSelectbox"] [role="group"]:visible')
        .first().evaluate(el => {
          const outer = document.querySelector('.st-key-dashboard-client-fields').getBoundingClientRect();
          const inner = el.getBoundingClientRect();
          return {left:inner.left-outer.left,right:outer.right-inner.right};
        });
      expect(Math.abs(insets.left - insets.right), 'Margens horizontais do formulário assimétricas')
        .toBeLessThanOrEqual(3);

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
        const fieldsLayer=panel?.querySelector(':scope > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-client-fields)');
        const footer=panel?.querySelector('.st-key-dashboard-client-footer');
        const scroller=panel?.querySelector('.st-key-dashboard-client-fields');
        const topStyle=getComputedStyle(fieldsLayer,'::before');
        const bottomStyle=getComputedStyle(footer,'::before');
        return {
          topPointer:topStyle.pointerEvents,bottomPointer:bottomStyle.pointerEvents,
          topOpacity:Number(topStyle.opacity),bottomOpacity:Number(bottomStyle.opacity),
          topLength:topStyle.height,bottomLength:bottomStyle.height,
          topGradient:topStyle.backgroundImage,bottomGradient:bottomStyle.backgroundImage,
          topY:fieldsLayer.getBoundingClientRect().top,
          scrollY:scroller.getBoundingClientRect().top,
        };
      });
      expect(overlays.topPointer).toBe('none');
      expect(overlays.bottomPointer).toBe('none');
      expect(overlays.topOpacity).toBeLessThan(.01);
      expect(overlays.bottomOpacity).toBeGreaterThan(.99);
      expect(overlays.topLength).toBe('60px');
      expect(overlays.bottomLength).toBe('52px');
      expect(overlays.topGradient).toContain('0.72');
      expect(overlays.bottomGradient).toContain('0.48');
      expect(Math.abs(overlays.topY-overlays.scrollY), 'Gradiente superior fora da área rolável')
        .toBeLessThanOrEqual(2);
      await scrollTo(dimensions.scrollable/2);
      await expect.poll(async () => (await opacity()).top).toBeGreaterThan(.99);
      await expect.poll(async () => (await opacity()).bottom).toBeGreaterThan(.99);
      await scrollTo(dimensions.scrollable);
      await expect.poll(async () => (await opacity()).top).toBeGreaterThan(.99);
      await expect.poll(async () => (await opacity()).bottom).toBeLessThan(.01);
      await expect(footer.getByRole('button',{name:'Calcular previsão'})).toBeVisible();
      // Abas com conteúdo insuficiente para rolar não exibem gradientes.
      for (const name of ['Perfil','Conta','Serviços','Extras']) {
        await page.locator('.st-key-dashboard-detail-tabs').getByRole('tab',{name,exact:true}).click();
        const hasScroll = await fields.evaluate(el => el.scrollHeight > el.clientHeight + 1);
        if (!hasScroll) {
          await expect.poll(async () => (await opacity()).top).toBeLessThan(.01);
          await expect.poll(async () => (await opacity()).bottom).toBeLessThan(.01);
        }
      }
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
