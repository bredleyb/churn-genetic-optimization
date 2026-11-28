import {test,expect} from '@playwright/test';
import {scrollCueStrengths} from '../../src/client_scroll_cues.mjs';
import {openClient,client,fields,footer,tabs,action,measure,near,screenshot} from './client.helpers.mjs';

test('CL-S01 cálculo das duas sombras em limites e conteúdos curtos',()=>{
  expect(scrollCueStrengths(0,400,400)).toEqual({top:0,bottom:0});
  expect(scrollCueStrengths(0,400,800)).toEqual({top:0,bottom:1});
  expect(scrollCueStrengths(28,400,800)).toEqual({top:.5,bottom:1});
  expect(scrollCueStrengths(200,400,800)).toEqual({top:1,bottom:1});
  expect(scrollCueStrengths(372,400,800)).toEqual({top:1,bottom:.5});
  expect(scrollCueStrengths(400,400,800)).toEqual({top:1,bottom:0});
  expect(scrollCueStrengths(2,400,404)).toEqual({top:1,bottom:1});
  expect(scrollCueStrengths(999,400,404)).toEqual({top:1,bottom:0});
});

for(const size of [{width:1024,height:600},{width:390,height:600}]){
  test('CL-S02 rolagem, sombras, calhas e rodapé fixo '+size.width,async({page},info)=>{
    await openClient(page,size);
    await tabs(page).getByRole('tab',{name:'Serviços'}).click();
    const scroller=fields(page),panel=client(page);
    // Os placeholders são temporários; só medir com o conteúdo da aba montado.
    await expect(page.getByRole('combobox',{name:'Serviço de telefone'}))
      .toBeVisible({timeout:15000});
    await expect(page.getByRole('combobox',{name:'Segurança online'}))
      .toBeVisible({timeout:15000});
    await expect.poll(()=>scroller.evaluate(el=>el.scrollHeight-el.clientHeight),
      {timeout:15000}).toBeGreaterThan(3);
    const metrics=await scroller.evaluate(el=>{
      const style=getComputedStyle(el),foot=getComputedStyle(
        document.querySelector('.st-key-dashboard-client-footer'));
      return {distance:el.scrollHeight-el.clientHeight,
        gutter:style.scrollbarGutter,footerGutter:foot.scrollbarGutter,
        left:parseFloat(style.paddingLeft),right:parseFloat(style.paddingRight),
        footerLeft:parseFloat(foot.paddingLeft),footerRight:parseFloat(foot.paddingRight),
        footerOverflow:foot.overflowY,
      };
    });
    expect(metrics.gutter).toBe('stable both-edges');
    expect(metrics.footerGutter).toBe(metrics.gutter);
    expect(metrics.left).toBe(10);expect(metrics.right).toBe(10);
    expect(metrics.footerLeft).toBe(metrics.left);
    expect(metrics.footerRight).toBe(metrics.right);
    expect(metrics.footerOverflow).toBe('hidden');
    expect(metrics.distance).toBeGreaterThan(3);

    const footerBefore=await measure(footer(page)),buttonBefore=await measure(action(page));
    const strength=()=>panel.evaluate(el=>({
      top:Number(getComputedStyle(el).getPropertyValue('--n3-client-shadow-top')),
      bottom:Number(getComputedStyle(el).getPropertyValue('--n3-client-shadow-bottom')),
    }));
    const moveTo=amount=>scroller.evaluate((el,value)=>{
      el.scrollTop=value;el.dispatchEvent(new Event('scroll'));
    },amount);
    const readPseudo=()=>page.evaluate(()=>{
      const root=document.querySelector('.st-key-dashboard-client');
      const top=root.querySelector(':scope > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-client-fields)');
      const bottom=root.querySelector(':scope > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-client-footer)');
      const upper=getComputedStyle(top,'::before'),lower=getComputedStyle(bottom,'::before');
      return {topHeight:upper.height,bottomHeight:lower.height,
        topPointer:upper.pointerEvents,bottomPointer:lower.pointerEvents,
        topGradient:upper.backgroundImage,bottomGradient:lower.backgroundImage};
    });

    await moveTo(0);
    await expect.poll(async()=>(await strength()).top).toBeLessThan(.01);
    await expect.poll(async()=>(await strength()).bottom).toBeGreaterThan(.99);
    const pseudo=await readPseudo();
    expect(pseudo.topHeight).toBe('52px');
    expect(pseudo.bottomHeight).toBe('52px');
    expect(pseudo.topPointer).toBe('none');
    expect(pseudo.bottomPointer).toBe('none');
    expect(pseudo.topGradient).toContain('0.48');
    expect(pseudo.bottomGradient).toContain('0.48');
    await screenshot(page,info,'CL-S02-inicio-'+size.width);

    await moveTo(metrics.distance/2);
    await expect.poll(async()=>(await strength()).top).toBeGreaterThan(.99);
    await expect.poll(async()=>(await strength()).bottom).toBeGreaterThan(.99);
    await screenshot(page,info,'CL-S02-meio-'+size.width);
    await moveTo(metrics.distance);
    await expect.poll(async()=>(await strength()).bottom).toBeLessThan(.01);
    await expect.poll(async()=>(await strength()).top).toBeGreaterThan(.99);
    const footerAfter=await measure(footer(page)),buttonAfter=await measure(action(page));
    near(footerBefore.y,footerAfter.y,'rodapé fixo',1);
    near(buttonBefore.y,buttonAfter.y,'botão fixo',1);
    await expect(action(page)).toBeVisible();
    await screenshot(page,info,'CL-S02-fim-'+size.width);

    for(const name of ['Perfil','Conta','Serviços','Extras']){
      await tabs(page).getByRole('tab',{name,exact:true}).click();
      const room=await scroller.evaluate(el=>el.scrollHeight-el.clientHeight);
      if(room<=1){
        await expect.poll(async()=>(await strength()).top).toBeLessThan(.01);
        await expect.poll(async()=>(await strength()).bottom).toBeLessThan(.01);
      }
    }
  });
}
test('CL-S03 sombra não captura eventos e foco permanece dentro do botão',async({page})=>{
  await openClient(page,{width:1024,height:768});
  const button=action(page);
  await page.keyboard.press('Tab'); // modalidade de teclado para :focus-visible
  await button.focus();
  await expect(button).toBeFocused();
  const focus=await button.evaluate(el=>({
    outline:getComputedStyle(el).outlineStyle,
    offset:getComputedStyle(el).outlineOffset,
  }));
  expect(focus.outline).toBe('solid');
  expect(focus.offset).toBe('-4px');
});
