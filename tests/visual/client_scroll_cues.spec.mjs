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
      const dimensions = await page.evaluate(() => {
        const scroller = document.querySelector('.st-key-dashboard-client-fields');
        const footer = document.querySelector('.st-key-dashboard-client-footer');
        const scrollStyle = getComputedStyle(scroller);
        const footerStyle = getComputedStyle(footer);
        return {
          scrollable:scroller.scrollHeight-scroller.clientHeight,
          gutter:scrollStyle.scrollbarGutter,
          footerGutter:footerStyle.scrollbarGutter,
          paddingLeft:parseFloat(scrollStyle.paddingInlineStart),
          paddingRight:parseFloat(scrollStyle.paddingInlineEnd),
          footerLeft:parseFloat(footerStyle.paddingInlineStart),
          footerRight:parseFloat(footerStyle.paddingInlineEnd),
          footerOverflow:footerStyle.overflowY,
        };
      });
      expect(dimensions.gutter).toBe('stable both-edges');
      expect(dimensions.footerGutter).toBe(dimensions.gutter);
      expect(dimensions.paddingLeft).toBe(10);
      expect(dimensions.paddingRight).toBe(10);
      expect(dimensions.footerLeft).toBe(dimensions.paddingLeft);
      expect(dimensions.footerRight).toBe(dimensions.paddingRight);
      expect(dimensions.footerOverflow).toBe('hidden');
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
        const footerLayer=panel?.querySelector(':scope > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-client-footer)');
        const scroller=panel?.querySelector('.st-key-dashboard-client-fields');
        const topStyle=getComputedStyle(fieldsLayer,'::before');
        const bottomStyle=getComputedStyle(footerLayer,'::before');
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
      expect(overlays.topLength).toBe('52px');
      expect(overlays.bottomLength).toBe('52px');
      expect(overlays.topGradient).toContain('0.48');
      expect(overlays.bottomGradient).toContain('0.48');
      expect(overlays.topGradient).toContain('0.2');
      expect(overlays.bottomGradient).toContain('0.2');
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


/* O alinhamento deve sobreviver às abas com/sem overflow, às duas variantes
   de scrollbar e aos breakpoints em que os campos rápidos são empilhados. */
for (const viewport of [
  {width:1440,height:900},
  {width:1024,height:768},
  {width:768,height:900},
  {width:390,height:900},
]) {
  test('Cliente usa o mesmo alinhamento para campos e botão — '+viewport.width+'x'+viewport.height,
    async ({page}) => {
      await page.setViewportSize(viewport);
      await page.goto('/', {waitUntil:'domcontentloaded'});
      const fields = page.locator('.st-key-dashboard-client-fields');
      const button = page.locator('.st-key-dashboard-client-footer button');
      const profile = page.locator('.churn-profile-label');
      const firstCircle = page.locator('.st-key-dashboard-profile-choices [data-testid="stButton"] button').first();
      const internet = page.locator('.st-key-dashboard-quick-fields [data-testid="stSelectbox"]:has(input[aria-label="Serviço de internet"]) [role="group"]');
      const charges = page.locator('.st-key-dashboard-quick-fields [data-testid="stNumberInput"]:has(input[aria-label="Cobrança mensal"]) [data-baseweb="input"]');
      await expect(button).toBeVisible();
      const btn = await button.boundingBox();
      const reference = await fields.boundingBox();

      for (const [label,loc,edge] of [
        ['Perfil de exemplo',profile,'left'],
        ['Primeiro perfil',firstCircle,'left'],
        ['Serviço de internet',internet,'left'],
        ['Cobrança mensal',charges,'right'],
      ]) {
        await expect(loc, label).toBeVisible();
        const rect=await loc.boundingBox();
        expect(Math.abs(rect.x + (edge === 'right' ? rect.width : 0) -
          btn.x - (edge === 'right' ? btn.width : 0)),
          label + ': desalinhado com o botão de cálculo').toBeLessThanOrEqual(2);
      }
      for (const tabName of ['Perfil','Conta','Serviços','Extras']) {
        await page.locator('.st-key-dashboard-detail-tabs')
          .getByRole('tab',{name:tabName,exact:true}).click();
        const input=page.locator('.st-key-dashboard-detail-tabs [data-testid="stSelectbox"] [role="group"]:visible').first();
        await expect(input, tabName).toBeVisible();
        const rect=await input.boundingBox();
        expect(Math.abs(rect.x-btn.x),
          tabName + ': margem esquerda diferente do rodapé').toBeLessThanOrEqual(2);
        expect(Math.abs(rect.x+rect.width-btn.x-btn.width),
          tabName + ': margem direita diferente do rodapé').toBeLessThanOrEqual(2);
        const scrollGeometry=await fields.evaluate(el=>({
          scrollWidth:el.scrollWidth,clientWidth:el.clientWidth,
          overflow:el.scrollHeight>el.clientHeight+1,
        }));
        expect(scrollGeometry.scrollWidth,
          tabName+': rolagem horizontal inesperada').toBeLessThanOrEqual(scrollGeometry.clientWidth+1);
      }
      const footerBounds=await page.locator('.st-key-dashboard-client-footer').boundingBox();
      expect(btn.x).toBeGreaterThanOrEqual(reference.x+7);
      expect(btn.x+btn.width).toBeLessThanOrEqual(reference.x+reference.width-7);
      expect(btn.x).toBeGreaterThan(footerBounds.x);
      expect(btn.x+btn.width).toBeLessThan(footerBounds.x+footerBounds.width);
    });
}
