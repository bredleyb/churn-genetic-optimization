/** Localizadores e medições compartilhados. Somente API pública do Playwright. */
import { expect } from '@playwright/test';

export const VIEWPORTS = [
  {width:1440,height:900}, {width:1366,height:768},
  {width:1280,height:720}, {width:1024,height:768},
  {width:768,height:900}, {width:390,height:900},
];

export const client = page => page.locator('.st-key-dashboard-client');
export const fields = page => page.locator('.st-key-dashboard-client-fields');
export const footer = page => page.locator('.st-key-dashboard-client-footer');
export const action = page => footer(page).locator('[data-testid="stButton"] button');
export const tabs = page => page.locator('.st-key-dashboard-detail-tabs');
export const profileCircles = page =>
  page.locator('.st-key-dashboard-profile-choices [data-testid="stButton"] button:visible');
export const profileActions = page =>
  page.locator('.st-key-dashboard-profile-actions [data-testid="stButton"] button:visible');

export const fieldGroup = (page,name) =>
  page.locator('[data-testid="stSelectbox"]')
    .filter({has:page.locator('input[aria-label="'+name+'"]')}).locator('[role="group"]');

export async function openClient(page,viewport) {
  await page.setViewportSize(viewport);
  await page.goto('/',{waitUntil:'domcontentloaded'});
  await expect(page.getByRole('heading',{name:'Cliente',exact:true})).toBeVisible({timeout:30000});
  await expect(action(page)).toBeVisible();
  await page.evaluate(async()=>{await document.fonts.ready;});
  await expect(page.locator('[data-testid="stException"]')).toHaveCount(0);
}

export async function measure(locator) {
  const box=await locator.boundingBox();
  expect(box,'Elemento esperado não possui caixa renderizada').toBeTruthy();
  return {left:box.x,right:box.x+box.width,top:box.y,bottom:box.y+box.height,
    x:box.x,y:box.y,width:box.width,height:box.height,cx:box.x+box.width/2,cy:box.y+box.height/2};
}

export const near=(actual,expected,label,tolerance=2)=>
  expect(Math.abs(actual-expected),label+': '+actual+' contra '+expected)
    .toBeLessThanOrEqual(tolerance);

export async function screenshot(page,testInfo,name){
  await testInfo.attach(name,{
    body:await page.screenshot({fullPage:false,animations:'disabled'}),
    contentType:'image/png',
  });
}

export async function clickOption(page,label,name) {
  const input=page.getByRole('combobox',{name:label,exact:true});
  const option=page.getByRole('option',{name,exact:true});
  await expect(input,'Campo ausente na aba ativa: '+label).toBeVisible({timeout:15000});
  // Reruns podem desmontar um menu logo após duas alterações consecutivas.
  // Reabrir o mesmo campo é limitado a três tentativas, sem esperas de minutos.
  for(let attempt=1;attempt<=3;attempt++){
    await expect(input).toBeVisible({timeout:10000});
    try {
      if(await input.getAttribute('aria-expanded')!=='true')
        await input.click({timeout:8000});
      await expect(input).toHaveAttribute('aria-expanded','true',{timeout:3500});
      await expect(option).toBeVisible({timeout:3500});
      await option.click({timeout:8000});
      await expect(input).toHaveValue(name,{timeout:8000});
      return;
    } catch(error) {
      if(await input.inputValue().catch(()=>null)===name)return;
      if(attempt===3)throw new Error(
        'Falha ao escolher '+JSON.stringify(name)+' em '+JSON.stringify(label)+
        ' após três tentativas: '+error.message);
      if(await input.getAttribute('aria-expanded').catch(()=>null)==='true')
        await page.keyboard.press('Escape');
    }
  }
}

export async function expectMonths(page,value) {
  const input=page.getByRole('textbox',{name:'Tempo como cliente'});
  await expect(input).toHaveValue(String(Number(value)),{timeout:7000});
  // A unidade deve pertencer ao input ativo; reruns podem deixar um nó antigo.
  await expect(input.locator('xpath=..').locator('.n3-tenure-unit'))
    .toHaveText(Number(value)===1?'mês':'meses');
}

export async function replaceMonths(page,digits) {
  const input=page.getByRole('textbox',{name:'Tempo como cliente'});
  await input.click();
  // Agora Ctrl+A é nativo e só seleciona os dígitos. A unidade é um span.
  const previous=await input.inputValue();
  expect(previous,'O valor editável deve ser numérico').toMatch(/^\d{1,3}$/);
  await input.press('ControlOrMeta+A');
  await expect.poll(() => input.evaluate(el => [
    el.selectionStart,el.selectionEnd,
  ])).toEqual([0,previous.length]);
  await page.keyboard.insertText(String(digits));
  await expectMonths(page,digits);
}

export async function ensureNoException(page) {
  await expect(page.locator('[data-testid="stException"]')).toHaveCount(0);
}
