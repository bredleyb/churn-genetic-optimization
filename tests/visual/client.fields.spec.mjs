import {test,expect} from '@playwright/test';
import {openClient,tabs,fieldGroup,clickOption,replaceMonths,measure,near,screenshot,ensureNoException} from './client.helpers.mjs';
import {clampMonths,displayMonths,replaceMonthDigits} from '../../src/tenure_control.mjs';

test('CL-F01 mês singular/plural, limites e substituição numérica sem afetar unidade',()=>{
  expect([0,1,2,999].map(displayMonths)).toEqual(['0 meses','1 mês','2 meses','999 meses']);
  expect(clampMonths(-1)).toBe(0);
  expect(clampMonths(1000)).toBe(999);
  expect(clampMonths(1.8)).toBe(1);
  expect(replaceMonthDigits(24,0,2,'5')).toBe(5);
  expect(replaceMonthDigits(24,2,2,'abc')).toBe(24);
  expect(replaceMonthDigits(2,1,1,'9999')).toBe(999);
});

test('CL-F02 editor de meses tem um único texto protegido e stepper correto',async({page},info)=>{
  await openClient(page,{width:1024,height:768});
  const months=page.getByRole('textbox',{name:'Tempo como cliente'});
  const field=page.locator('.n3-tenure-field');
  const minus=page.getByRole('button',{name:'Diminuir um mês'});
  const plus=page.getByRole('button',{name:'Aumentar um mês'});
  await expect(months).toHaveValue('3 meses');
  await plus.click();
  await expect(months).toHaveValue('4 meses');
  await minus.click();
  await expect(months).toHaveValue('3 meses');
  await replaceMonths(page,1);
  await expect(months).toHaveValue('1 mês');
  await months.click();
  await months.press('End');
  await expect.poll(async()=>months.evaluate(el=>el.selectionStart)).toBe(1);
  await months.press('Delete');
  await expect(months).toHaveValue('1 mês');
  await months.press('ArrowRight');
  await expect.poll(async()=>months.evaluate(el=>el.selectionStart)).toBe(1);
  await replaceMonths(page,0);
  await expect(minus).toBeDisabled();
  await expect(plus).toBeEnabled();
  await replaceMonths(page,999);
  await expect(plus).toBeDisabled();
  await expect(minus).toBeEnabled();
  await months.click();
  const focus=await field.evaluate(el=>({
    shadow:getComputedStyle(el).boxShadow,border:getComputedStyle(el).borderColor,
    width:el.getBoundingClientRect().width,
  }));
  expect(focus.shadow).toContain('inset');
  expect(focus.border).toBe('rgb(245, 245, 245)');
  expect(focus.width).toBeGreaterThan(60);
  await screenshot(page,info,'CL-F02-meses-foco-e-limite');
});

test('CL-F03 categorias representam apenas os dados do dataset',async({page})=>{
  await openClient(page,{width:1024,height:768});
  await tabs(page).getByRole('tab',{name:'Perfil'}).click();
  await page.getByRole('combobox',{name:'Gênero'}).click();
  const options=page.getByRole('option');
  await expect(options).toHaveCount(2);
  await expect(page.getByRole('option',{name:'Feminino'})).toBeVisible();
  await expect(page.getByRole('option',{name:'Masculino'})).toBeVisible();
  await page.getByRole('option',{name:'Masculino'}).click();
  await expect(page.getByRole('combobox',{name:'Gênero'})).toHaveValue('Masculino');
  await clickOption(page,'Pessoa idosa','Sim');
  await clickOption(page,'Possui parceiro(a)','Sim');
  await clickOption(page,'Possui dependentes','Sim');
  await tabs(page).getByRole('tab',{name:'Extras'}).click();
  await clickOption(page,'Streaming de filmes','Sim');
  await tabs(page).getByRole('tab',{name:'Perfil'}).click();
  await expect(page.getByRole('combobox',{name:'Gênero'})).toHaveValue('Masculino');
  await expect(page.getByRole('combobox',{name:'Possui dependentes'})).toHaveValue('Sim');
  await ensureNoException(page);
});

test('CL-F04 telefonia e internet sincronizam campos dependentes',async({page})=>{
  await openClient(page,{width:1024,height:768});
  await tabs(page).getByRole('tab',{name:'Serviços'}).click();
  await clickOption(page,'Serviço de telefone','Não');
  const lines=page.getByRole('combobox',{name:'Múltiplas linhas telefônicas'});
  await expect(lines).toHaveValue('Sem serviço telefônico');
  await expect(lines).toBeDisabled();
  await clickOption(page,'Serviço de telefone','Sim');
  await expect(lines).toBeEnabled();
  await expect(lines).toHaveValue('Não');
  await clickOption(page,'Serviço de internet','Não');
  for(const name of ['Segurança online','Backup online','Proteção de dispositivos']){
    const field=page.getByRole('combobox',{name});
    await expect(field).toHaveValue('Sem serviço de internet');
    await expect(field).toBeDisabled();
  }
  await tabs(page).getByRole('tab',{name:'Extras'}).click();
  for(const name of ['Suporte técnico','Streaming de TV','Streaming de filmes']){
    const field=page.getByRole('combobox',{name});
    await expect(field).toBeDisabled();
    await expect(field).toHaveValue('Sem serviço de internet');
  }
  await clickOption(page,'Serviço de internet','DSL');
  for(const name of ['Suporte técnico','Streaming de TV','Streaming de filmes']){
    await expect(page.getByRole('combobox',{name})).toBeEnabled();
  }
  await ensureNoException(page);
});

test('CL-F05 campos de cobrança e total indisponível conservam tipos',async({page})=>{
  await openClient(page,{width:1024,height:768});
  const charge=page.getByRole('spinbutton',{name:'Cobrança mensal'});
  await expect(charge).toHaveValue('95,50');
  await charge.fill('101,50');
  await charge.press('Tab');
  await tabs(page).getByRole('tab',{name:'Conta'}).click();
  const missing=page.getByRole('checkbox',{name:'Total cobrado indisponível'});
  const total=page.getByRole('spinbutton',{name:'Total cobrado'});
  await expect(total).toBeEnabled();
  await missing.check();
  await expect(total).toBeDisabled();
  await missing.uncheck();
  await expect(total).toBeEnabled();
  await tabs(page).getByRole('tab',{name:'Perfil'}).click();
  await expect(charge).toHaveValue('101,50');
});
