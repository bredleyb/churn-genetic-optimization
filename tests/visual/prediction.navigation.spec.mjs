import {test,expect} from '@playwright/test';
import {openClient,action,replaceMonths,tabs,ensureNoException} from './client.helpers.mjs';

for (const viewport of [{width:1366,height:768},{width:390,height:900}]) {
  test('PR-N01 quatro abas independentes e persistentes '+viewport.width, async({page})=>{
    await openClient(page,viewport);
    const nav=page.locator('.st-key-dashboard-prediction-tabs');
    const list=nav.getByRole('tab');
    await expect(list).toHaveCount(4);
    await expect(list).toHaveText(['Painel','Terminal','Métricas','Metodologia']);
    await expect(nav.getByRole('tab',{name:'Painel',exact:true})).toHaveAttribute('aria-selected','true');
    await nav.getByRole('tab',{name:'Metodologia',exact:true}).click();
    await expect(nav.getByRole('tab',{name:'Metodologia',exact:true})).toHaveAttribute('aria-selected','true');
    await tabs(page).getByRole('tab',{name:'Conta',exact:true}).click();
    await expect(nav.getByRole('tab',{name:'Metodologia',exact:true})).toHaveAttribute('aria-selected','true');
    await replaceMonths(page,4);
    await expect(nav.getByRole('tab',{name:'Metodologia',exact:true})).toHaveAttribute('aria-selected','true');
    await nav.getByRole('tab',{name:'Painel',exact:true}).click();
    await page.getByRole('link',{name:'Ver métricas',exact:true}).click();
    await expect(nav.getByRole('tab',{name:'Métricas',exact:true})).toHaveAttribute('aria-selected','true');
    await expect(action(page)).toHaveText('Calcular previsão');
    await ensureNoException(page);
  });
}
