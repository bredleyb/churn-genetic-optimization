import {test,expect} from '@playwright/test';
import {openClient,profileCircles,profileActions,measure,near,screenshot,replaceMonths,expectMonths,ensureNoException} from './client.helpers.mjs';

test('CL-P01 seleção, cópia, edições isoladas, restauração e exclusão sem modal',async({page},info)=>{
  await openClient(page,{width:1024,height:768});
  const button=name=>page.getByRole('button',{name,exact:true});
  const restore=button('Restaurar perfil'),remove=button('Excluir perfil'),add=button('+');
  await expect(button('1')).toHaveAttribute('kind','primary');
  await expect(button('2')).toBeVisible();
  await expect(add).toBeVisible();
  await expect(restore).toBeDisabled();
  await expect(remove).toBeDisabled();
  await expect(restore).toHaveCSS('background-color','rgb(0, 0, 0)');
  await replaceMonths(page,24);
  await expect(restore).toBeEnabled();
  await restore.hover();
  await expect(restore).toHaveCSS('background-color','rgb(32, 33, 36)');
  await page.mouse.move(0,0);
  await add.click();
  await expect(button('3')).toHaveAttribute('kind','primary');
  await expectMonths(page,24);
  await expect(restore).toBeDisabled();
  await expect(remove).toBeEnabled();
  await replaceMonths(page,25);
  await button('1').click();
  await expectMonths(page,24);
  await button('2').click();
  await expect(remove).toBeDisabled();
  await button('3').click();
  await expectMonths(page,25);
  await restore.click();
  await expectMonths(page,24);
  await expect(restore).toBeDisabled();

  await add.click();
  await expect(button('4')).toHaveAttribute('kind','primary');
  await replaceMonths(page,40);
  await add.click();
  await expect(button('5')).toHaveAttribute('kind','primary');
  await replaceMonths(page,50);
  await expect(add).toHaveCount(0);
  await expect(profileCircles(page)).toHaveCount(5);
  // Regressão: o primeiro círculo foi recortado ao selecionar perfis extras.
  const strip=await measure(page.locator('.st-key-dashboard-profile-choices'));
  const buttons=profileCircles(page);
  const first=await measure(buttons.first()),last=await measure(buttons.last());
  expect(first.left,'Primeiro perfil recortado à esquerda').toBeGreaterThanOrEqual(strip.left-1);
  expect(last.right,'Último perfil recortado à direita').toBeLessThanOrEqual(strip.right+1);
  await screenshot(page,info,'CL-P01-limite-cinco');

  await button('4').click();
  await expectMonths(page,40);
  await remove.click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(button('5')).toHaveCount(0);
  await expect(button('3')).toHaveAttribute('kind','primary');
  await expect(add).toBeVisible();
  await button('4').click();
  await expectMonths(page,50);
  await restore.click();
  await expectMonths(page,40);
  await add.click();
  await expect(button('5')).toBeVisible();
  await ensureNoException(page);
  await screenshot(page,info,'CL-P01-reposicao-apos-exclusao');
});

for (const width of [1440,1024,768,390]) {
  test('CL-P02 ações e perfis no mesmo eixo '+width,async({page},info)=>{
    await openClient(page,{width,height:900});
    const circle=await measure(profileCircles(page).first());
    const actionBoxes=await Promise.all((await profileActions(page).all()).map(measure));
    for(const [i,rect] of actionBoxes.entries()){
      near(rect.cy,circle.cy,'alinhamento da ação '+i,2);
      near(rect.width,circle.width,'largura da ação '+i,1);
      near(rect.height,circle.height,'altura da ação '+i,1);
    }
    await expect(page.getByRole('button',{name:'Restaurar perfil'})).toBeDisabled();
    await expect(page.getByRole('button',{name:'Excluir perfil'})).toBeDisabled();
    await screenshot(page,info,'CL-P02-perfis-'+width);
  });
}

test('CL-P03 botões de perfis mantêm semântica, hover e seleção',async({page})=>{
  await openClient(page,{width:1024,height:768});
  for(const n of [1,2]){
    const control=page.getByRole('button',{name:String(n),exact:true});
    await expect(control).toBeVisible();
    await expect(control).toContainText(String(n));
  }
  const other=page.getByRole('button',{name:'2',exact:true});
  await other.hover();
  await expect(other).toHaveCSS('background-color','rgb(32, 33, 36)');
  await page.mouse.move(0,0);
  await page.getByRole('button',{name:'2',exact:true}).click();
  await expect(page.getByRole('button',{name:'2',exact:true}))
    .toHaveAttribute('kind','primary');
  await expect(page.getByRole('button',{name:'Excluir perfil'})).toBeDisabled();
});
